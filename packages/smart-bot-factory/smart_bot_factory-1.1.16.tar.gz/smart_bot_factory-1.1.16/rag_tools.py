import logging
from typing import Optional

from smart_bot_factory.rag import RagRouter, VectorStore

logger = logging.getLogger(__name__)

rag_router = RagRouter("mdclinica_rag")


vectorstore = VectorStore(bot_id="mdclinica")


def _format_results(results) -> str:
    text = ""
    for index, doc in enumerate(results):
        text += f"#{index + 1}\n {doc.page_content}\n\n"
    return text


@rag_router.tool
async def get_info_from_rag(query: str, section: Optional[str] = None) -> str:
    """Запрос информации из RAG-системы.

    Args:
        query: Запрос к RAG-системе.
        section: Раздел внутри категории (например, `about_procedure`).
        Отправить можешь несколько через |. Пример - "prices|about_procedure|
        indications". Если не нужно фильтровать по разделу, то не отправляй
        этот параметр.
    Returns:
        Строка с подборкой категорий (один чанк на блок текста).
    """
    logger.info("Запрос категорий услуг: %s", query)

    metadata_filter = {}

    if section:
        metadata_filter["section"] = section.split("|")

    logger.info("Фильтры metadata: %s", metadata_filter)

    # Используем новый метод asimilarity_search с автоматической фильтрацией по score
    # score по умолчанию 0.6, можно изменить через параметр
    results = await vectorstore.asimilarity_search(query, k=5, filter=metadata_filter, score=0.55)

    text = _format_results(results)
    logger.info("Текст результатов: %s", text)

    return text
