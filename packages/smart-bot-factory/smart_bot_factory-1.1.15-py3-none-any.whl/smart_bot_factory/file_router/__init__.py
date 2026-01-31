"""
FileRouter модуль - специализированный роутер для обработки событий связанных с файлами
"""

from .router import FileRouter
from .sender import FileSender

__all__ = ["FileRouter", "FileSender"]
