import logging
import re
from typing import List, Optional

from trafilatura import sitemaps

logger = logging.getLogger(__name__)


def search_sitemap(
    url: str,
    regex: Optional[str] = None,
    limit: Optional[int] = None,
    include_source: bool = False,
) -> List[str]:
    """
    Ищет ссылки в sitemap, при необходимости фильтруя их по регулярному выражению.

    Args:
        url: URL sitemap для поиска
        regex: Опциональное регулярное выражение для фильтрации ссылок
        limit: Опциональный лимит на количество возвращаемых ссылок
        include_source: Если True, исходный URL будет добавлен в список результатов (по умолчанию False)

    Returns:
        Список найденных ссылок (возможно, отфильтрованных и ограниченных)
    """
    if not url:
        raise ValueError("Не указан URL для поиска")

    logger.info(f"🗺️ Загружаю sitemap: {url}")
    try:
        links = sitemaps.sitemap_search(url)
        initial_count = len(links)
        logger.info(f"✅ Найдено ссылок в sitemap: {initial_count}")
    except Exception as exc:
        logger.error(f"❌ Ошибка при загрузке sitemap: {exc}")
        raise

    if regex:
        logger.info(f"🔍 Применяю фильтр (regex): {regex}")
        links = [link for link in links if re.match(regex, link)]
        filtered_count = len(links)
        logger.info(f"✅ После фильтрации: {filtered_count} ссылок (было {initial_count})")

    if limit is not None and limit > 0:
        before_limit = len(links)
        links = links[:limit]
        logger.info(f"✂️ Применён лимит: {len(links)} из {before_limit} ссылок")

    if include_source:
        if url not in links:
            links.insert(0, url)
            logger.info("➕ Добавлена исходная ссылка в список")
        else:
            logger.debug("ℹ️ Исходная ссылка уже присутствует в списке")

    final_count = len(links)
    logger.info(f"📋 Итого ссылок для обработки: {final_count}")
    return links
