"""Тесты для состояний FSM админа"""

from smart_bot_factory.admin.states import AdminStates


class TestAdminStates:
    """Тесты для AdminStates"""

    def test_admin_states_exists(self):
        """Тест что состояния существуют"""
        assert AdminStates.admin_mode is not None
        assert AdminStates.in_conversation is not None
        assert AdminStates.create_event_name is not None
        assert AdminStates.create_event_date is not None
        assert AdminStates.create_event_time is not None
        assert AdminStates.create_event_segment is not None
        assert AdminStates.create_event_message is not None
        assert AdminStates.create_event_files is not None
        assert AdminStates.create_event_confirm is not None

    def test_admin_states_group(self):
        """Тест что состояния в группе"""
        assert hasattr(AdminStates, "__states__")
        assert len(AdminStates.__states__) >= 9
