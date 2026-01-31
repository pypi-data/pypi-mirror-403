"""Тесты для response_models"""

import pytest
from pydantic import ValidationError

from smart_bot_factory.integrations.openai.responce_models import (
    AnalyzeSentimentResponseModel,
    GenerateFollowUpResponseModel,
    MainResponseModel,
)


class TestMainResponseModel:
    """Тесты для MainResponseModel"""

    def test_main_response_model_valid(self):
        """Тест валидной модели ответа"""
        model = MainResponseModel(user_message="Тестовое сообщение", service_info={"этап": "introduction", "качество": 5})

        assert model.user_message == "Тестовое сообщение"
        assert model.service_info["этап"] == "introduction"
        assert model.service_info["качество"] == 5

    def test_main_response_model_empty_service_info(self):
        """Тест модели с пустым service_info"""
        model = MainResponseModel(user_message="Тестовое сообщение", service_info={})

        assert model.user_message == "Тестовое сообщение"
        assert model.service_info == {}

    def test_main_response_model_missing_user_message(self):
        """Тест что user_message обязателен"""
        with pytest.raises(ValidationError):
            MainResponseModel(service_info={})

    def test_main_response_model_default_service_info(self):
        """Тест что service_info имеет значение по умолчанию"""
        model = MainResponseModel(user_message="Тест")

        assert model.user_message == "Тест"
        assert isinstance(model.service_info, dict)


class TestAnalyzeSentimentResponseModel:
    """Тесты для AnalyzeSentimentResponseModel"""

    def test_analyze_sentiment_model_valid(self):
        """Тест валидной модели анализа настроения"""
        model = AnalyzeSentimentResponseModel(
            sentiment="positive",
            interest_level=8,
            purchase_readiness=7,
            objections=["цена высокая"],
            key_questions=["как быстро доставка?"],
            response_strategy="highlight_benefits",
        )

        assert model.sentiment == "positive"
        assert model.interest_level == 8
        assert model.purchase_readiness == 7
        assert len(model.objections) == 1
        assert len(model.key_questions) == 1

    def test_analyze_sentiment_model_missing_fields(self):
        """Тест что все поля обязательны"""
        with pytest.raises(ValidationError):
            AnalyzeSentimentResponseModel(sentiment="positive", interest_level=8)


class TestGenerateFollowUpResponseModel:
    """Тесты для GenerateFollowUpResponseModel"""

    def test_generate_follow_up_model_valid(self):
        """Тест валидной модели продолжения разговора"""
        model = GenerateFollowUpResponseModel(follow_up_message="Следующее сообщение", follow_up_type="question", follow_up_data={"key": "value"})

        assert model.follow_up_message == "Следующее сообщение"
        assert model.follow_up_type == "question"
        assert model.follow_up_data["key"] == "value"

    def test_generate_follow_up_model_default_data(self):
        """Тест что follow_up_data имеет значение по умолчанию"""
        model = GenerateFollowUpResponseModel(follow_up_message="Тест", follow_up_type="message")

        assert isinstance(model.follow_up_data, dict)
        assert model.follow_up_data == {}
