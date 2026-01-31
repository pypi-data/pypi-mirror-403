import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from project_root_finder import root
from trafilatura import fetch_url, html2txt

from .parser_prompt import prompt

logger = logging.getLogger(__name__)


class SiteParser:
    def __init__(self, additional_instructions: Optional[str] = None, bot_id: Optional[str] = None):
        self.bot_id = bot_id
        self.api_key = self._load_api_key()

        model = ChatOpenAI(model="gpt-5-mini", temperature=0, api_key=self.api_key)

        self.chain = prompt | model | StrOutputParser()
        self.additional_instructions = additional_instructions

    def _load_api_key(self) -> str:
        """Загружает OPENAI_API_KEY аналогично SupabaseClient"""
        env_candidates = []

        if self.bot_id:
            env_candidates.append(root / "bots" / self.bot_id / ".env")

        # Добавляем общий .env в корне проекта
        env_candidates.append(root / ".env")

        for env_path in env_candidates:
            if env_path and env_path.exists():
                load_dotenv(env_path)
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    logger.info(f"🔑 OPENAI_API_KEY загружен из {env_path}")
                    return api_key

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден. Добавьте его в .env")
        return api_key

    def _text_from_site(self, url: str):
        logger.info(f"🌐 Загружаю страницу: {url}")
        try:
            html = fetch_url(url)
            if not html:
                raise ValueError("Пустой ответ при загрузке страницы")

            text = html2txt(html)
            if not text:
                raise ValueError("Не удалось конвертировать HTML в текст")

            return text
        except Exception as exc:
            logger.warning(f"⚠️ Ошибка при парсинге {url}: {exc}")
            return ""

    async def _clean_text(self, text: str):
        add_prompt = self.additional_instructions if self.additional_instructions else "Доп инструкций нет!"

        response = await self.chain.ainvoke({"additional_instructions": add_prompt, "text": text})

        return response

    async def parser(
        self,
        url: Union[str, List[str]],
        max_workers: int = 5,
        to_files: bool = False,
    ) -> Union[str, List[Path]]:
        """
        Полный цикл обработки:
        1. Скачиваем HTML по каждому URL
        2. Конвертируем в текст
        3. Прогоняем через LLM с дополнительными инструкциями
        4. Возвращаем готовый очищенный текст
        """
        logger.info("🚀 Запуск парсинга сайтов")
        if isinstance(url, str):
            urls: List[str] = [url]
        else:
            urls = list(url)

        if not urls:
            return [] if to_files else ""

        total = len(urls)
        concurrency = max(1, min(max_workers, total))
        logger.info(f"⚙️ Одновременных задач: {concurrency}, всего ссылок: {total}")

        # Ограничиваем количество одновременных задач
        semaphore = asyncio.Semaphore(concurrency)

        async def process_link(idx: int, link: str):
            position = f"[{idx + 1}/{total}]"
            logger.info(f"➡️ {position} Старт парсинга: {link}")
            async with semaphore:
                raw_text = await asyncio.to_thread(self._text_from_site, link)
                if not raw_text:
                    logger.warning(f"⚠️ {position} Не удалось получить текст: {link}")
                    return link, ""

                cleaned_text = await self._clean_text(raw_text)
                cleaned = cleaned_text.strip() if cleaned_text else ""
                if cleaned:
                    logger.info(f"✅ {position} Готово, длина текста: {len(cleaned)} символов")
                else:
                    logger.warning(f"⚠️ {position} Пустой результат после очистки")
                remaining = total - (idx + 1)
                if remaining > 0:
                    logger.info(f"⏳ Осталось обработать ~{remaining} ссылок")
                return link, cleaned

        tasks = [asyncio.create_task(process_link(i, link)) for i, link in enumerate(urls)]
        processed_results = await asyncio.gather(*tasks)

        if to_files:
            if not self.bot_id:
                raise ValueError("Для сохранения файлов требуется указать bot_id")

            output_dir = root / "bots" / self.bot_id / "parser"
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Тексты будут сохранены в {output_dir}")

            saved_files: List[Path] = []
            for link, text in processed_results:
                if not text:
                    continue
                filename = self._build_filename_from_url(link)
                file_path = output_dir / f"{filename}.txt"
                file_path.write_text(text, encoding="utf-8")
                saved_files.append(file_path)
                logger.info(f"💾 Сохранено: {file_path.name}")

            logger.info(f"📦 Всего сохранено файлов: {len(saved_files)}")
            return saved_files

        processed_chunks = [text for _, text in processed_results if text]
        success_count = len(processed_chunks)
        fail_count = total - success_count
        logger.info(f"🏁 Парсинг завершён. Успехов: {success_count}, пропусков: {fail_count}")

        return "\n\n".join(processed_chunks)

    def _build_filename_from_url(self, link: str) -> str:
        parsed = urlparse(link)
        last_segment = parsed.path.rstrip("/").split("/")[-1] or "index"
        safe_segment = "".join(ch for ch in last_segment if ch.isalnum() or ch in ("-", "_"))
        return safe_segment or "page"
