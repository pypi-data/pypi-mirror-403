from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    waiting_for_message = State()
    admin_chat = State()  # пользователь в диалоге с админом

    voice_confirmation = State()  # ожидание подтверждения распознанного текста
    voice_editing = State()  # редактирование распознанного текста
