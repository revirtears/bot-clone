from aiogram import F
from aiogram.types import Message
from aiogram.filters import CommandStart

from ..text import TextBot
from signature import SettingsBot
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
        self.dp.message(F.text == 'Отключить')(self.cancel_connect)
        self.dp.message(F.text.startswith("/admin"))(self.add_admin_chat)
        self.dp.message(F.text.startswith("/spam"))(self.add_spam_chat)
 

    async def home(self, m: Message):
        if m.from_user.id in self.cfg.ADMINS or m.from_user.id in await self.udb.user.get_ids_license():
            await self.udb.user.exists_user(uid=m.from_user.id, name=m.from_user.full_name, uname=m.from_user.username)
            return await m.answer(TextBot.welcome_message)

        chats = await self.udb.user.get_chats_spams()
        print("Чаты:", chats)

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
            except Exception as e: print("Аккаунт пишет в боте старт:", e) 

    
    async def cancel_connect(self, m: Message):
        phone = await self.udb.accounts.cancel_connect(uid=m.from_user.id)
        success = await disconect_app(phone=phone)

        if success:
            await m.answer("Аккаунт успешно отключен!", reply_markup=await kb.main_menu())
        else:
            await m.answer("Ошибка: аккаунт не найден среди активных.")


    async def add_admin_chat(self, m: Message):
        chat_uid = m.text.replace('/admin', '').split()[0]

        if chat_uid[0] != '-': return await m.answer("Неверный формат ID!")

        try:
            chat_info = await m.bot.get_chat(chat_id=chat_uid)
            bot_member = await m.bot.get_chat_member(chat_uid, m.bot.id)
            
            if bot_member.status not in ["administrator", "creator"]:
                return await m.answer(f"Бот не является администратором в чате {chat_info.title}!\n\nДобавьте бота в администраторы и попробуйте снова.")

            resp = await self.udb.user.add_admin_chat(uid=m.from_user.id, chat_uid=chat_uid)
            if not resp: return await m.answer("Чат уже добавлен!")

            await m.answer(f"<b>Чат админ [<code>{chat_info.title}</code>] успешно добавлен!</b>")

        except Exception as e: print(f"Ошибка: {e}")

    
    async def add_spam_chat(self, m: Message):
        chat_uid = m.text.replace('/spam', '').split()[0]

        if chat_uid[0] != '-': return await m.answer("Неверный формат ID!")

        try:
            chat_info = await m.bot.get_chat(chat_id=chat_uid)
            bot_member = await m.bot.get_chat_member(chat_uid, m.bot.id)
            
            if bot_member.status not in ["administrator", "creator"]:
                return await m.answer(f"Бот не является администратором в чате {chat_info.title}!\n\nДобавьте бота в администраторы и попробуйте снова.")

            resp = await self.udb.user.add_spam_chat(uid=m.from_user.id, chat_uid=chat_uid)
            if not resp: return await m.answer("Чат уже добавлен!")
            
            await m.answer(f"<b>Чат спам [<code>{chat_info.title}</code>] успешно добавлен!</b>")

        except Exception as e: print(f"Ошибка: {e}")