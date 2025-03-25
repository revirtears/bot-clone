from typing import Union
from datetime import datetime

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from config import settings
from keyboards.callbackdata import *


class Ikb:
    @staticmethod
    async def chat_menu():
        menu = InlineKeyboardBuilder()

        menu.button(text="Добавить чат", callback_data="add_chat")
        menu.button(text="Список чатов", callback_data="list_chat")
        menu.button(text="Открыть чаты", callback_data="open_chats")
        menu.button(text="Войти в чаты", callback_data="go_to_chat")

        return menu.adjust(1).as_markup()
    

    @staticmethod
    async def update_menu():
        menu = InlineKeyboardBuilder()

        menu.button(text="Обновить🔄", callback_data="update_time")

        return menu.adjust(1).as_markup()
    

    @staticmethod
    async def group_settings_menu(chat_uid: int, connect: bool):
        menu = InlineKeyboardBuilder()

        text_connect = 'Подключить' if not connect else 'Отключить'
        callback_data = GroupCallback(action='connect', chat_uid=chat_uid)
        menu.button(text=text_connect, callback_data=callback_data)

        callback_data = GroupCallback(action='del_chat', chat_uid=chat_uid)
        menu.button(text="Удалить чат", callback_data=callback_data)

        return menu.adjust(1).as_markup()


    @staticmethod
    async def add_account_menu():
        menu = InlineKeyboardBuilder()

        menu.button(text="Добавить аккаунт", callback_data="add_account")

        return menu.adjust(1).as_markup()
    