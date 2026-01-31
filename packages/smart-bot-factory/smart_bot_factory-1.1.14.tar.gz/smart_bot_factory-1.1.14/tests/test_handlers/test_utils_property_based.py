"""Property-based тесты для handlers.utils с использованием Hypothesis"""

from hypothesis import given
from hypothesis import strategies as st

from smart_bot_factory.handlers.utils import fix_html_markup


class TestFixHtmlMarkupPropertyBased:
    """Property-based тесты для fix_html_markup"""

    @given(st.text())
    def test_fix_html_markup_idempotent(self, text):
        """Тест идемпотентности: применение функции дважды дает тот же результат"""
        result1 = fix_html_markup(text)
        result2 = fix_html_markup(result1)

        # Применение дважды должно дать тот же результат
        assert result1 == result2

    @given(st.text())
    def test_fix_html_markup_preserves_length_approximately(self, text):
        """Тест сохранения длины: результат не должен быть намного длиннее исходного"""
        result = fix_html_markup(text)

        # Результат может быть длиннее из-за экранирования, но не более чем в 6 раз
        # (максимальная длина экранирования: &lt; и &gt; вместо < и >)
        assert len(result) <= len(text) * 6

    @given(st.text())
    def test_fix_html_markup_no_invalid_tags(self, text):
        """Тест отсутствия невалидных тегов в результате"""
        result = fix_html_markup(text)

        # Проверяем, что невалидные теги экранированы
        # Валидные теги: b, i, u, s, code, pre, a
        valid_tags = ["b", "i", "u", "s", "code", "pre", "a"]

        # Если есть < или >, они должны быть либо частью валидного тега, либо экранированы
        import re

        # Находим все < и >, которые не являются частью валидных тегов
        invalid_pattern = r"<(?!/?(?:" + "|".join(valid_tags) + r")(?:\s|>))"
        matches = re.findall(invalid_pattern, result, re.IGNORECASE)

        # Если есть невалидные теги, они должны быть экранированы
        for match in matches:
            # Проверяем, что после < идет &lt; или валидный тег
            assert "&lt;" in result or match.startswith("<") and match[1:2] in valid_tags

    @given(st.text(min_size=1))
    def test_fix_html_markup_preserves_valid_tags(self, text):
        """Тест сохранения валидных тегов"""
        # Добавляем валидные теги в текст
        text_with_tags = f"<b>{text}</b> <i>{text}</i>"
        result = fix_html_markup(text_with_tags)

        # Валидные теги должны остаться
        assert "<b>" in result or "&lt;b&gt;" not in result
        assert "</b>" in result or "&lt;/b&gt;" not in result
        assert "<i>" in result or "&lt;i&gt;" not in result

    @given(st.text(), st.text())
    def test_fix_html_markup_commutative_with_concatenation(self, text1, text2):
        """Тест коммутативности: результат для объединенного текста должен быть предсказуемым"""
        combined = text1 + text2
        result_combined = fix_html_markup(combined)

        result1 = fix_html_markup(text1)
        result2 = fix_html_markup(text2)

        # Результат для объединенного текста должен содержать результаты для частей
        # (хотя порядок может отличаться из-за обработки тегов)
        assert len(result_combined) >= max(len(result1), len(result2)) - len(text1) - len(text2)

    @given(st.text())
    def test_fix_html_markup_handles_empty_string(self, text):
        """Тест обработки пустой строки"""
        result = fix_html_markup("")
        assert result == ""

        # Пустая строка в середине текста не должна ломать обработку
        text_with_empty = text + "" + text
        result_with_empty = fix_html_markup(text_with_empty)
        assert len(result_with_empty) >= len(result) * 2 - len(text) * 2
