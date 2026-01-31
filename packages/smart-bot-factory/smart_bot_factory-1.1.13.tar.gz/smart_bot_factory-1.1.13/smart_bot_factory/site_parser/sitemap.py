import logging
import re
from typing import List, Optional

from trafilatura import sitemaps

logger = logging.getLogger(__name__)


def search_sitemap(url: str, regex: Optional[str] = None, limit: Optional[int] = None) -> List[str]:
    """
    Ищет ссылки в sitemap, при необходимости фильтруя их по регулярному выражению.

    Args:
        url: URL sitemap для поиска
        regex: Опциональное регулярное выражение для фильтрации ссылок
        limit: Опциональный лимит на количество возвращаемых ссылок

    Returns:
        Список найденных ссылок (возможно, отфильтрованных и ограниченных)
    """
    if not url:
        raise ValueError("Не указан URL для поиска")

    logger.info(f"🗺️ Загружаю sitemap: {url}")
    links = sitemaps.sitemap_search(url)
    logger.info(f"🔗 Найдено ссылок: {len(links)}")

    if regex:
        logger.info(f"🧪 Применяю фильтр regex: {regex}")
        links = [link for link in links if re.match(regex, link)]
        logger.info(f"✅ После фильтрации осталось: {len(links)} ссылок")

    if limit is not None and limit > 0:
        links = links[:limit]
        logger.info(f"✂️ Применён лимит: оставлено {len(links)} ссылок")

    return links
