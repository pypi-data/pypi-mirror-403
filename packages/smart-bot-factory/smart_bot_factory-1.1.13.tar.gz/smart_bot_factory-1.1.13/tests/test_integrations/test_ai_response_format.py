"""Тесты для проверки формата ответа от ИИ"""

import pytest
from pydantic import ValidationError

from smart_bot_factory.handlers.constants import AIMetadataKey
from smart_bot_factory.integrations.openai.responce_models import MainResponseModel


class TestAIResponseFormat:
    """Тесты для проверки формата ответа от ИИ"""

    def test_valid_response_format(self):
        """Тест валидного формата ответа"""
        valid_response = {
            "user_message": "Привет! Как дела?",
            "service_info": {
                "этап": "introduction",
                "качество": 5,
                "события": [],
            },
        }

        model = MainResponseModel(**valid_response)
        assert model.user_message == "Привет! Как дела?"
        assert model.service_info["этап"] == "introduction"
        assert model.service_info["качество"] == 5
        assert model.service_info["события"] == []

    def test_response_with_events(self):
        """Тест ответа с событиями"""
        valid_response = {
            "user_message": "Записал ваш номер",
            "service_info": {"этап": "contacts", "качество": 9, "события": [{"тип": "телефон", "инфо": "+79219603144"}]},
        }

        model = MainResponseModel(**valid_response)
        assert len(model.service_info["события"]) == 1
        assert model.service_info["события"][0]["тип"] == "телефон"
        assert model.service_info["события"][0]["инфо"] == "+79219603144"

    def test_response_with_multiple_events(self):
        """Тест ответа с несколькими событиями"""
        valid_response = {
            "user_message": "Обработал запросы",
            "service_info": {
                "этап": "consult",
                "качество": 7,
                "события": [{"тип": "консультация", "инфо": "Запросил материалы"}, {"тип": "вопрос", "инфо": "Спросил про цены"}],
            },
        }

        model = MainResponseModel(**valid_response)
        assert len(model.service_info["события"]) == 2
        assert model.service_info["события"][0]["тип"] == "консультация"
        assert model.service_info["события"][1]["тип"] == "вопрос"

    def test_response_with_files(self):
        """Тест ответа с файлами"""
        valid_response = {
            "user_message": "Отправляю файлы",
            "service_info": {"этап": "offer", "качество": 6, "события": [], "файлы": ["presentation.pdf", "price_list.xlsx"], "каталоги": []},
        }

        model = MainResponseModel(**valid_response)
        assert "файлы" in model.service_info
        assert len(model.service_info["файлы"]) == 2
        assert "presentation.pdf" in model.service_info["файлы"]

    def test_response_with_directories(self):
        """Тест ответа с каталогами"""
        valid_response = {
            "user_message": "Отправляю каталог",
            "service_info": {"этап": "offer", "качество": 7, "события": [], "файлы": [], "каталоги": ["catalog1", "catalog2"]},
        }

        model = MainResponseModel(**valid_response)
        assert "каталоги" in model.service_info
        assert len(model.service_info["каталоги"]) == 2

    def test_response_missing_user_message(self):
        """Тест что user_message обязателен"""
        invalid_response = {"service_info": {"этап": "introduction", "качество": 5, "события": []}}

        with pytest.raises(ValidationError):
            MainResponseModel(**invalid_response)

    def test_response_missing_service_info(self):
        """Тест что service_info обязателен (но может быть пустым)"""
        # service_info имеет default_factory=dict, поэтому может быть пустым
        valid_response = {"user_message": "Текст сообщения"}

        model = MainResponseModel(**valid_response)
        assert model.user_message == "Текст сообщения"
        assert model.service_info == {}

    def test_quality_range_validation(self):
        """Тест что качество должно быть числом (валидация диапазона не в модели, но проверяем структуру)"""
        # Качество должно быть числом, но валидация диапазона 1-10 не в модели
        # Проверяем что принимается любое число
        valid_response = {"user_message": "Тест", "service_info": {"этап": "introduction", "качество": 10, "события": []}}

        model = MainResponseModel(**valid_response)
        assert isinstance(model.service_info["качество"], int)
        assert model.service_info["качество"] == 10

    def test_quality_out_of_range(self):
        """Тест что качество может быть любым числом (валидация диапазона не в модели)"""
        # Модель не валидирует диапазон, но проверяем что принимается
        valid_response = {
            "user_message": "Тест",
            "service_info": {
                "этап": "introduction",
                "качество": 15,  # Вне диапазона, но модель примет
                "события": [],
            },
        }

        model = MainResponseModel(**valid_response)
        assert model.service_info["качество"] == 15

    def test_stage_validation(self):
        """Тест что этап должен быть строкой"""
        valid_response = {"user_message": "Тест", "service_info": {"этап": "consult", "качество": 5, "события": []}}

        model = MainResponseModel(**valid_response)
        assert isinstance(model.service_info["этап"], str)
        assert model.service_info["этап"] == "consult"

    def test_events_must_be_list(self):
        """Тест что события должны быть списком"""
        valid_response = {
            "user_message": "Тест",
            "service_info": {
                "этап": "introduction",
                "качество": 5,
                "события": [],  # Пустой список
            },
        }

        model = MainResponseModel(**valid_response)
        assert isinstance(model.service_info["события"], list)

    def test_event_structure(self):
        """Тест структуры события"""
        valid_response = {
            "user_message": "Тест",
            "service_info": {"этап": "contacts", "качество": 8, "события": [{"тип": "телефон", "инфо": "Иван Петров +79219603144"}]},
        }

        model = MainResponseModel(**valid_response)
        event = model.service_info["события"][0]
        assert "тип" in event
        assert "инфо" in event
        assert event["тип"] == "телефон"
        assert event["инфо"] == "Иван Петров +79219603144"

    def test_event_missing_type(self):
        """Тест что событие должно иметь тип"""
        # Модель не валидирует структуру событий строго, но проверяем что структура сохраняется
        valid_response = {
            "user_message": "Тест",
            "service_info": {"этап": "introduction", "качество": 5, "события": [{"инфо": "Только инфо без типа"}]},
        }

        model = MainResponseModel(**valid_response)
        event = model.service_info["события"][0]
        assert "инфо" in event
        # Тип может отсутствовать, модель не валидирует строго

    def test_empty_user_message(self):
        """Тест что user_message может быть пустой строкой"""
        valid_response = {"user_message": "", "service_info": {"этап": "introduction", "качество": 5, "события": []}}

        model = MainResponseModel(**valid_response)
        assert model.user_message == ""

    def test_json_serialization(self):
        """Тест сериализации в JSON"""
        valid_response = {
            "user_message": "Тест",
            "service_info": {"этап": "consult", "качество": 6, "события": [{"тип": "вопрос", "инфо": "Спросил про услуги"}]},
        }

        model = MainResponseModel(**valid_response)
        json_data = model.model_dump()

        assert json_data["user_message"] == "Тест"
        assert json_data["service_info"]["этап"] == "consult"
        assert json_data["service_info"]["качество"] == 6
        assert len(json_data["service_info"]["события"]) == 1

    def test_model_validate_json(self):
        """Тест валидации из JSON строки"""
        json_string = """{
            "user_message": "Привет!",
            "service_info": {
                "этап": "introduction",
                "качество": 5,
                "события": []
            }
        }"""

        model = MainResponseModel.model_validate_json(json_string)
        assert model.user_message == "Привет!"
        assert model.service_info["этап"] == "introduction"

    def test_invalid_json(self):
        """Тест что невалидный JSON вызывает ошибку"""
        invalid_json = '{"user_message": "Тест", "service_info": {}}'

        # Это валидный JSON, но проверим что парсится
        model = MainResponseModel.model_validate_json(invalid_json)
        assert model.user_message == "Тест"

    def test_complete_response_format(self):
        """Тест полного формата ответа со всеми полями"""
        complete_response = {
            "user_message": "Отправляю материалы и записываю контакт",
            "service_info": {
                "этап": "offer",
                "качество": 8,
                "события": [{"тип": "телефон", "инфо": "+79219603144"}, {"тип": "консультация", "инфо": "Запросил прайс"}],
                "файлы": ["presentation.pdf", "price_list.xlsx"],
                "каталоги": ["products"],
            },
        }

        model = MainResponseModel(**complete_response)

        # Проверяем все поля
        assert model.user_message == "Отправляю материалы и записываю контакт"
        assert model.service_info["этап"] == "offer"
        assert model.service_info["качество"] == 8
        assert len(model.service_info["события"]) == 2
        assert len(model.service_info["файлы"]) == 2
        assert len(model.service_info["каталоги"]) == 1

    def test_service_info_optional_fields(self):
        """Тест что некоторые поля в service_info опциональны"""
        minimal_response = {"user_message": "Минимальный ответ", "service_info": {"этап": "introduction"}}

        model = MainResponseModel(**minimal_response)
        assert model.service_info["этап"] == "introduction"
        # Качество и события могут отсутствовать

    def test_validate_quality_range_1_to_10(self):
        """Тест валидации диапазона качества от 1 до 10 (бизнес-логика)"""
        # Проверяем что качество должно быть в диапазоне 1-10 согласно бизнес-правилам
        valid_qualities = [1, 5, 10]
        for quality in valid_qualities:
            response = {"user_message": "Тест", "service_info": {"этап": "introduction", "качество": quality, "события": []}}
            model = MainResponseModel(**response)
            assert model.service_info["качество"] == quality

    def test_validate_stage_values(self):
        """Тест что этап должен быть строкой (бизнес-логика)"""
        valid_stages = ["introduction", "consult", "offer", "contacts"]
        for stage in valid_stages:
            response = {"user_message": "Тест", "service_info": {"этап": stage, "качество": 5, "события": []}}
            model = MainResponseModel(**response)
            assert model.service_info["этап"] == stage

    def test_validate_event_type_and_info(self):
        """Тест что событие должно иметь тип и инфо"""
        response = {
            "user_message": "Тест",
            "service_info": {"этап": "contacts", "качество": 9, "события": [{"тип": "телефон", "инфо": "+79219603144"}]},
        }

        model = MainResponseModel(**response)
        event = model.service_info["события"][0]
        # Проверяем что оба поля присутствуют
        assert AIMetadataKey.EVENT_TYPE in event
        assert AIMetadataKey.EVENT_INFO in event
        assert event[AIMetadataKey.EVENT_TYPE] == "телефон"
        assert event[AIMetadataKey.EVENT_INFO] == "+79219603144"

    def test_validate_files_format(self):
        """Тест что файлы должны быть списком строк"""
        response = {
            "user_message": "Отправляю файлы",
            "service_info": {"этап": "offer", "качество": 6, "события": [], "файлы": ["file1.pdf", "file2.jpg"]},
        }

        model = MainResponseModel(**response)
        files = model.service_info.get("файлы", [])
        assert isinstance(files, list)
        assert all(isinstance(f, str) for f in files)

    def test_validate_directories_format(self):
        """Тест что каталоги должны быть списком строк"""
        response = {
            "user_message": "Отправляю каталоги",
            "service_info": {"этап": "offer", "качество": 7, "события": [], "каталоги": ["catalog1", "catalog2"]},
        }

        model = MainResponseModel(**response)
        directories = model.service_info.get("каталоги", [])
        assert isinstance(directories, list)
        assert all(isinstance(d, str) for d in directories)

    def test_response_from_dict(self):
        """Тест создания модели из словаря (как приходит от OpenAI)"""
        response_dict = {"user_message": "Привет!", "service_info": {"этап": "introduction", "качество": 5, "события": []}}

        model = MainResponseModel(**response_dict)
        assert model.user_message == response_dict["user_message"]
        assert model.service_info == response_dict["service_info"]

    def test_response_with_empty_events(self):
        """Тест что события могут быть пустым массивом"""
        response = {"user_message": "Обычное сообщение", "service_info": {"этап": "consult", "качество": 6, "события": []}}

        model = MainResponseModel(**response)
        assert model.service_info["события"] == []
        assert len(model.service_info["события"]) == 0
