"""Тесты для состояний FSM"""

from smart_bot_factory.handlers.states import UserStates


class TestUserStates:
    """Тесты для UserStates"""

    def test_user_states_exists(self):
        """Тест что состояния существуют"""
        assert UserStates.waiting_for_message is not None
        assert UserStates.admin_chat is not None
        assert UserStates.voice_confirmation is not None
        assert UserStates.voice_editing is not None

    def test_user_states_group(self):
        """Тест что состояния в группе"""
        assert hasattr(UserStates, "__states__")
        assert len(UserStates.__states__) >= 4
