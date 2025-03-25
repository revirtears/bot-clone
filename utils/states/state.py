from aiogram.fsm.state import State, StatesGroup


class RegisterAcc(StatesGroup):
    PHONE = State()
    CODE = State()


class AddChatState(StatesGroup):
    UID_CHAT = State()
