import asyncio
import logging

from smart_bot_factory.site_parser import SiteParser, search_sitemap

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pars_site")

additional_prompt = (
    "В конце сайта всег пересидаются все услуги конртеной категории - их Не надо сохранять, это бесполезная информация. "
    "Также в начале сайта пропиасно номер телефона и время работы - это тоже убрать."
)

parser = SiteParser(bot_id="mdclinica", additional_instructions=additional_prompt)


async def main():
    logger.info("🔍 Ищу ссылки в sitemap...")
    links = search_sitemap("https://mdclinica.ru/uslugi")
    logger.info(f"📌 Найдено ссылок: {len(links)}. Берём первые 10 для теста.")

    logger.info("🚀 Запускаю парсер для выбранных ссылок...")
    result = await parser.parser(links[:10], to_files=True)

    logger.info("✅ Парсинг завершён, печатаю результат ниже:\n")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
