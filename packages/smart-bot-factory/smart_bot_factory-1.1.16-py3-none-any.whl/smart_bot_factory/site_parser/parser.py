import asyncio
import logging
import os
import time
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from project_root_finder import root
from trafilatura import fetch_url, html2txt

from .parser_prompt import prompt
from .sitemap import search_sitemap

logger = logging.getLogger(__name__)


def _log_or_print(level: int, message: str):
    """Выводит сообщение через logger, если настроен, иначе через print"""
    if logger.handlers or logging.root.handlers:
        if level == logging.INFO:
            logger.info(message)
        elif level == logging.WARNING:
            logger.warning(message)
        elif level == logging.ERROR:
            logger.error(message)
        else:
            logger.debug(message)
    else:
        print(message)


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
                    logger.debug(f"🔑 OPENAI_API_KEY загружен из {env_path}")
                    return api_key

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден. Добавьте его в .env")
        return api_key

    def _text_from_site(self, url: str):
        try:
            html = fetch_url(url)
            if not html:
                raise ValueError("Пустой ответ при загрузке страницы")
            text = html2txt(html)
            if not text:
                raise ValueError("Не удалось конвертировать HTML в текст")
            return text
        except Exception as exc:
            logger.debug(f"⚠️ Ошибка при парсинге {url}: {exc}")
            return ""

    async def _clean_text(self, text: str, url: str = ""):
        add_prompt = (
            self.additional_instructions
            if self.additional_instructions
            else "Доп инструкций нет!"
        )
        response = await self.chain.ainvoke({"additional_instructions": add_prompt, "text": text})
        return response

    async def parser(
        self,
        url: Optional[Union[str, List[str]]] = None,
        sitemap: Optional[str] = None,
        sitemap_regex: Optional[str] = None,
        sitemap_limit: Optional[int] = None,
        sitemap_include_source: bool = False,
        max_workers: int = 5,
        to_files: bool = True,
    ) -> Union[str, List[Path]]:
        """
        Полный цикл обработки:
        1. Если передан sitemap, получает ссылки из него
        2. Скачиваем HTML по каждому URL
        3. Конвертируем в текст
        4. Прогоняем через LLM с дополнительными инструкциями
        5. Возвращаем готовый очищенный текст или сохраняет в файлы

        Args:
            url: URL или список URL для парсинга (если не передан sitemap)
            sitemap: URL sitemap для получения списка ссылок
            sitemap_regex: Регулярное выражение для фильтрации ссылок из sitemap
            sitemap_limit: Лимит на количество ссылок из sitemap
            sitemap_include_source: Включать ли исходный URL sitemap в список
            max_workers: Максимальное количество одновременных задач
            to_files: Сохранять ли результаты в файлы (по умолчанию True)
        """
        start_time = time.time()
        _log_or_print(logging.INFO, "🚀 Запуск парсинга сайтов")

        # Если передан sitemap, получаем ссылки из него
        if sitemap:
            _log_or_print(logging.INFO, f"🗺️ Используется sitemap: {sitemap}")
            urls = search_sitemap(
                url=sitemap,
                regex=sitemap_regex,
                limit=sitemap_limit,
                include_source=sitemap_include_source
            )
            if not urls:
                _log_or_print(logging.WARNING, "⚠️ Sitemap не вернул ссылок")
                return [] if to_files else ""
        elif url:
            if isinstance(url, str):
                urls: List[str] = [url]
            else:
                urls = list(url)
        else:
            raise ValueError("Необходимо указать либо url, либо sitemap")

        if not urls:
            return [] if to_files else ""

        # Подготовка директории для сохранения файлов (если нужно)
        output_dir = None
        if to_files:
            if not self.bot_id:
                raise ValueError("Для сохранения файлов требуется указать bot_id")
            output_dir = root / "bots" / self.bot_id / "parser"
            output_dir.mkdir(parents=True, exist_ok=True)
            _log_or_print(logging.INFO, f"📁 Сохраняю файлы в: {output_dir}")

        total = len(urls)
        concurrency = max(1, min(max_workers, total))
        _log_or_print(logging.INFO, f"⚙️ Обработка {total} ссылок (одновременно: {concurrency})")

        # Ограничиваем количество одновременных задач
        semaphore = asyncio.Semaphore(concurrency)

        # Счетчик для отслеживания прогресса
        completed_count = 0
        completed_lock = asyncio.Lock()
        saved_files: List[Path] = []
        saved_lock = asyncio.Lock()
        success_count = 0

        async def process_link(idx: int, link: str):
            nonlocal completed_count, success_count
            position = f"[{idx + 1}/{total}]"

            async with semaphore:
                raw_text = await asyncio.to_thread(self._text_from_site, link)
                if not raw_text:
                    async with completed_lock:
                        completed_count += 1
                        current_percent = int((completed_count / total) * 100)
                    _log_or_print(logging.WARNING, f"⚠️ {position} ({current_percent}%) Пропущено: не удалось получить текст")
                    return link, ""

                cleaned_text = await self._clean_text(raw_text, link)
                cleaned = cleaned_text.strip() if cleaned_text else ""

                # Сохраняем файл сразу, если to_files=True
                if to_files and cleaned and output_dir:
                    filename = self._build_filename_from_url(link)
                    file_path = output_dir / f"{filename}.txt"
                    await asyncio.to_thread(file_path.write_text, cleaned, encoding="utf-8")
                    async with saved_lock:
                        saved_files.append(file_path)

                async with completed_lock:
                    completed_count += 1
                    current_percent = int((completed_count / total) * 100)
                    remaining = total - completed_count
                    if cleaned:
                        success_count += 1
                
                if cleaned:
                    _log_or_print(
                        logging.INFO,
                        f"✅ {position} ({current_percent}%) Готово | "
                        f"Осталось: {remaining} | "
                        f"Размер: {len(cleaned)} символов"
                    )
                else:
                    _log_or_print(logging.WARNING, f"⚠️ {position} ({current_percent}%) Пустой результат")

                return link, cleaned

        tasks = [asyncio.create_task(process_link(i, link)) for i, link in enumerate(urls)]
        processed_results = await asyncio.gather(*tasks)

        elapsed_time = time.time() - start_time

        if to_files:
            _log_or_print(
                logging.INFO,
                f"🏁 Готово! Сохранено: {len(saved_files)} файлов | "
                f"Успешно: {success_count}/{total} ({int(success_count/total*100)}%) | "
                f"Время: {elapsed_time:.2f} сек"
            )
            return saved_files

        # Для случая без сохранения в файлы - считаем из результатов
        processed_chunks = [text for _, text in processed_results if text]
        final_success_count = len(processed_chunks)
        _log_or_print(
            logging.INFO,
            f"🏁 Готово! Успешно: {final_success_count}/{total} ({int(final_success_count/total*100)}%) | "
            f"Время: {elapsed_time:.2f} сек"
        )

        return "\n\n".join(processed_chunks)

    def _build_filename_from_url(self, link: str) -> str:
        parsed = urlparse(link)
        last_segment = parsed.path.rstrip("/").split("/")[-1] or "index"
        safe_segment = "".join(ch for ch in last_segment if ch.isalnum() or ch in ("-", "_"))
        return safe_segment or "page"
