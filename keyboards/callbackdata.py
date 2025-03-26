from aiogram.filters.callback_data import CallbackData


class GroupCallback(CallbackData, prefix="group"):
    action: str
    chat_uid: int


class DeleteTextCallback(CallbackData, prefix="del_text"):
    action: str
    mes_id: int
    chat_uid: str
