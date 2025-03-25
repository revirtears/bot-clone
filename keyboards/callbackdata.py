from aiogram.filters.callback_data import CallbackData


class GroupCallback(CallbackData, prefix="group"):
    action: str
    chat_uid: int