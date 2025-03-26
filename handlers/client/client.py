import os
import asyncio

from aiogram import F
from aiogram.types import Message
from aiogram.filters import CommandStart

from ..text import TextBot
from signature import SettingsBot
from keyboards.inline import Ikb as ikb
from keyboards.reply import ReplyKb as kb

from keyboards.callbackdata import *
from handlers.soft.code import disconect_app


class Client:
    def __init__(self, bot: SettingsBot) -> None:
        self.bot = bot
        self.dp = bot.dp
        self.udb = bot.udb
        self.cfg = bot.config
        self.format_chat_uid = bot.format_chat_uid


    async def register_handlers(self):
        self.dp.message(CommandStart())(self.home)
        self.dp.message(F.new_chat_member)(self.bot_added_to_chat)
        self.dp.message(F.text == 'Отключить')(self.cancel_connect)
        self.dp.message(F.chat_shared)(self.parse_user_chat)
 

    async def home(self, m: Message):
        chats = await self.udb.user.get_chats_spams()

        if chats:
            try:
                for chat in chats:
                    member = await m.bot.get_chat_member(chat_id=chat, user_id=m.from_user.id)

                    if member.status == ("member"):
                        user = await self.udb.accounts.exists_account(uid=m.from_user.id)

                        if not user: 
                            return await m.answer(
                                "Добро пожаловать, подключите аккаунт.", reply_markup=await kb.main_menu())
                        
                        await m.answer("Аккаунт подключен!", reply_markup=await kb.del_connect_menu())
            except: pass

        if m.from_user.id in self.cfg.ADMINS or m.from_user.id in await self.udb.user.get_ids_license():
            admin_chat, spam_chat = await self.udb.user.exists_user(
                uid=m.from_user.id, name=m.from_user.full_name, uname=m.from_user.username)
            
            await m.answer(
                TextBot.welcome_message, reply_markup=await kb.admin_menu(admin_chat_status=admin_chat, spam_chat_status=spam_chat))

    
    async def bot_added_to_chat(self, m: Message):
        if any(member.id == m.bot.id for member in m.new_chat_members):

            chat_uid = await self.format_chat_uid(chat_type=m.chat.type, chat_uid=m.chat.id)
            status = await self.udb.user.add_chat(uid=m.from_user.id, chat_uid=chat_uid)

            if status:
                await m.answer("Чат успешно подключен!")

    
    async def cancel_connect(self, m: Message):
        phone = await self.udb.accounts.cancel_connect(uid=m.from_user.id)
        success = await disconect_app(phone=phone)

        if success:
            await m.answer("Аккаунт успешно отключен!", reply_markup=await kb.main_menu())
        else:
            await m.answer("Ошибка: аккаунт не найден среди активных.")
    

    async def parse_user_chat(self, m: Message):
        if m.from_user.id in self.cfg.ADMINS or m.from_user.id in await self.udb.user.get_ids_license():
            try:
                chat_info = await m.bot.get_chat(chat_id=m.chat_shared.chat_id)

                chat_id = await self.format_chat_uid(chat_type=chat_info.type, chat_uid=chat_info.id)
                admin_chat, spam_chat = await self.udb.user.add_chat(uid=m.from_user.id, chat_uid=chat_id)

                await m.answer(
                    f"Чат {chat_info.title} успешно добавлен!", reply_markup=await kb.admin_menu(admin_chat_status=admin_chat, spam_chat_status=spam_chat))

            except Exception as e: pass