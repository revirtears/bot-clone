from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, KeyboardButtonRequestChat, ChatAdministratorRights 

import random


class ReplyKb:
    @staticmethod
    async def main_menu():
        builder = ReplyKeyboardBuilder()
        builder.button(text="Подключить", request_contact=True)
        builder.adjust(1)
        
        return builder.as_markup(resize_keyboard=True)
    

    @staticmethod
    async def numpad_menu():
        builder = ReplyKeyboardBuilder()
        
        buttons = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '0️⃣', '❌']

        for text in buttons:
            builder.button(text=text)

        builder.adjust(3, 3, 3, 1)
        
        return builder.as_markup(resize_keyboard=True)
    

    @staticmethod
    async def del_connect_menu():
        builder = ReplyKeyboardBuilder()
        
        builder.button(text="Отключить")
        
        return builder.as_markup(resize_keyboard=True)
    

    @staticmethod
    async def admin_menu(admin_chat_status: bool, spam_chat_status: bool):
        admin_rights = ChatAdministratorRights(
            is_anonymous=False,
            can_manage_chat=True,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=True,
            can_change_info=False,
            can_invite_users=True,
            can_post_stories=False,
            can_edit_stories=False,
            can_delete_stories=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_pin_messages=False,
            can_manage_topics=False
        )

        buttons = []

        if not admin_chat_status:  
            buttons.append([KeyboardButton(
                text="Добавить админ чат",
                request_chat=KeyboardButtonRequestChat(
                    request_id=random.randint(-2147483648, 2147483647),
                    chat_is_channel=False,
                    bot_is_member=True,
                    bot_administrator_rights=admin_rights,
                    user_administrator_rights=admin_rights,
                    chat_is_created=False
                )
            )])

        if not spam_chat_status and admin_chat_status:  
            buttons.append([KeyboardButton(
                text="Добавить спам чат",
                request_chat=KeyboardButtonRequestChat(
                    request_id=random.randint(-2147483648, 2147483647),
                    chat_is_channel=False,
                    bot_is_member=True,
                    bot_administrator_rights=admin_rights,
                    user_administrator_rights=admin_rights,
                    chat_is_created=False
                )
            )])

        menu = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=buttons)
        return menu
