"""Property-based тесты для conversation_manager с использованием Hypothesis"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from smart_bot_factory.utils.conversation_manager import ConversationManager


class TestTruncateMessagePropertyBased:
    """Property-based тесты для _truncate_message"""

    @pytest.fixture
    def manager(self):
        """Фикстура для ConversationManager"""
        return ConversationManager.__new__(ConversationManager)

    @given(st.text(), st.integers(min_value=1, max_value=100))
    def test_truncate_message_preserves_short_messages(self, text, max_lines):
        """Тест что короткие сообщения не обрезаются"""
        manager = ConversationManager.__new__(ConversationManager)
        lines = text.split("\n")

        if len(lines) <= max_lines:
            result = manager._truncate_message(text, max_lines=max_lines)
            assert result == text

    @given(st.text(min_size=1), st.integers(min_value=1, max_value=50))
    def test_truncate_message_max_lines_respected(self, text, max_lines):
        """Тест что результат не превышает разумного предела"""
        # Добавляем еще строки для тестирования обрезки
        multi_line_text = "\n".join([text] * min(10, max_lines + 5))

        manager = ConversationManager.__new__(ConversationManager)
        result = manager._truncate_message(multi_line_text, max_lines=max_lines)

        result_lines = result.split("\n")
        original_lines = multi_line_text.split("\n")

        # Если текст был обрезан, результат должен быть не более 7 строк (3 + 1 + 3)
        if len(original_lines) > max_lines:
            assert len(result_lines) <= 7
        else:
            # Если текст не был обрезан, результат должен совпадать с исходным
            assert len(result_lines) == len(original_lines)

    @given(st.text())
    def test_truncate_message_idempotent_for_short_text(self, text):
        """Тест идемпотентности для коротких текстов"""
        manager = ConversationManager.__new__(ConversationManager)
        lines = text.split("\n")

        if len(lines) <= 10:  # Короткий текст
            result1 = manager._truncate_message(text, max_lines=10)
            result2 = manager._truncate_message(result1, max_lines=10)
            assert result1 == result2

    @given(st.text())
    def test_truncate_message_contains_ellipsis_for_long_text(self, text):
        """Тест что длинные тексты содержат многоточие"""
        manager = ConversationManager.__new__(ConversationManager)
        lines = text.split("\n")

        if len(lines) > 5:
            result = manager._truncate_message(text, max_lines=5)
            # Должно содержать многоточие или быть обрезанным
            assert "..." in result or len(result.split("\n")) <= 5

    @given(st.text(), st.integers(min_value=1, max_value=100))
    def test_truncate_message_preserves_content(self, text, max_lines):
        """Тест что результат содержит исходный контент (хотя бы частично)"""
        manager = ConversationManager.__new__(ConversationManager)
        result = manager._truncate_message(text, max_lines=max_lines)

        # Если исходный текст не пустой, результат тоже не должен быть пустым
        if text.strip():
            assert len(result) > 0

        # Первые строки должны совпадать
        original_lines = text.split("\n")
        result_lines = result.split("\n")
        if len(original_lines) > 0 and len(result_lines) > 0:
            # Первая строка должна совпадать (если не была обрезана)
            min_lines = min(len(original_lines), len(result_lines))
            if min_lines > 0:
                assert original_lines[0] == result_lines[0] or len(result_lines) <= max_lines
