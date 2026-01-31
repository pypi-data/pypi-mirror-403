from typing import Any, Dict, List

from pydantic import BaseModel, Field


class MainResponseModel(BaseModel):
    user_message: str = Field(..., description="Это текст, который отправишь пользователю.")

    service_info: Dict[str, Any] = Field(..., default_factory=dict, description="Служебная информация в json формате")


class AnalyzeSentimentResponseModel(BaseModel):
    sentiment: str = Field(..., description="Настроение клиента")
    interest_level: int = Field(..., description="Уровень заинтересованности клиента")
    purchase_readiness: int = Field(..., description="Готовность к покупке клиента")
    objections: List[str] = Field(..., description="Основные возражения или вопросы клиента")
    key_questions: List[str] = Field(..., description="Ключевые вопросы клиента")
    response_strategy: str = Field(..., description="Рекомендуемая стратегия ответа")


class GenerateFollowUpResponseModel(BaseModel):
    follow_up_message: str = Field(..., description="Следующее сообщение для отправки клиенту")
    follow_up_type: str = Field(..., description="Тип следующего сообщения")
    follow_up_data: Dict[str, Any] = Field(..., default_factory=dict, description="Данные для следующего сообщения")
