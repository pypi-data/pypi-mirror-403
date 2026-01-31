from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    admin_mode = State()
    in_conversation = State()

    # Состояния для создания события
    create_event_name = State()
    create_event_date = State()
    create_event_time = State()
    create_event_segment = State()
    create_event_message = State()
    create_event_files = State()
    create_event_confirm = State()
    
    # Состояния для редактирования события
    edit_event_select = State()
    edit_event_action = State()
    edit_event_message = State()
    edit_event_delete_confirm = State()