import asyncio
from datetime import datetime

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from ..text import TextBot
from signature import SettingsBot
from keyboards.inline import Ikb as ikb

from keyboards.callbackdata import *
from utils.states.state import AddChatState

from handlers.soft.code import join_from_chats

from utils.loguru import setup_logger
from handlers.client.client import Client
from handlers.client.add_account import Account


async def setup(bot_instance):
        await bot_instance.db_manager.async_main()

        user_client = Client(bot=bot_instance)
        account = Account(bot=bot_instance)
        admin_chat = AdminChat(bot=bot_instance)

        await user_client.register_handlers()
        await account.register_handlers()
        await admin_chat.register_handlers()
        await setup_logger(level=bot_instance.config.LOGGING_LEVEL)


tasks_bot = {}


class AdminChat:
    def __init__(self, bot: SettingsBot) -> None:
        self.bot = bot
        self.dp = bot.dp
        self.udb = bot.udb
        self.cfg = bot.config
        self.format_chat_uid = bot.format_chat_uid
        self.is_valid_token = bot.is_valid_token


    async def register_handlers(self):
        self.dp.message(Command("menu"))(self.command_menu)
        self.dp.callback_query(F.data == 'add_chat')(self.add_chat)
        self.dp.message(F.text, AddChatState.UID_CHAT)(self.save_uid_chat)
        self.dp.callback_query(F.data == 'list_chat')(self.open_chats)
        self.dp.callback_query(F.data == 'update_time')(self.update_time)
        self.dp.message(F.text.startswith("/chat"))(self.open_chat)
        self.dp.callback_query(F.data == 'go_to_chat')(self.go_to_chats)
        self.dp.callback_query(GroupCallback.filter(F.action == 'connect'))(self.connect_chat)
        self.dp.callback_query(GroupCallback.filter(F.action == 'del_chat'))(self.delete_chat)
        self.dp.message(F.text.startswith("/add"))(self.add_license)
        self.dp.message(F.text.startswith('/del'))(self.del_license)
        self.dp.message(F.text)(self.no_register_account)
        self.dp.callback_query(DeleteTextCallback.filter(F.action == 'del_chat'))(self.delete_message_chat)
        self.dp.callback_query(F.data == 'open_chats')(self.open_chats_or_close)
 

    async def command_menu(self, m: Message):
        chat_uid = await self.format_chat_uid(chat_type=m.chat.type, chat_uid=m.chat.id)
        accounts, chats = await self.udb.user.get_account_or_chat(chat_uid=chat_uid)
        connect = await self.udb.user.get_connect(admin_chat=chat_uid)

        await m.answer(f"⚙️<b>Меню управления</b>\n\nАккаунтов в боте: {accounts}\nЧатов подключено: {chats}", 
            reply_markup=await ikb.chat_menu(connect=connect))
        
    
    async def add_chat(self, call: CallbackQuery, state: FSMContext):
        await call.message.delete()
        await call.message.answer("Введите ID чата")
        await state.set_state(AddChatState.UID_CHAT)
        
    
    async def save_uid_chat(self, m: Message, state: FSMContext):
        chat_admin_uid = await self.format_chat_uid(chat_type=m.chat.type, chat_uid=m.chat.id)

        try:
            chat = await m.bot.get_chat(chat_id=m.text)
            count_members = await m.bot.get_chat_member_count(chat_id=m.text)

            chat_id = await self.udb.user.add_active_chat(
                admin_chat_uid=chat_admin_uid, chat_uid=str(chat.id), title=chat.title, url=chat.invite_link)
            
            await m.reply(TextBot.add_active_chat_text.format(
                chat_id=chat_id, title=chat.title, chat_uid=chat.id, count=count_members))

        except Exception as e: print(e)

        await state.clear()

    
    async def open_chats(self, call: CallbackQuery):
        await call.message.delete()
        
        chat_admin_uid = await self.format_chat_uid(chat_type=call.message.chat.type, chat_uid=call.message.chat.id)
        chats = await self.udb.user.get_chats(admin_chat_uid=chat_admin_uid)

        if not chats:
            return await call.message.answer("❌ У вас нет активных чатов.")

        chats_text = "\n".join(
            f"(/chat{count}) - {chat[0]}, {'🟡' if chat[1] else '🔴'}"
            for count, chat in enumerate(chats, 1))

        text = (
            f"Активных чатов: <code>{len(chats)}</code>\n\n"
            f"{chats_text}\n\n"
            f"<i>Обновлено в {datetime.now():%H:%M:%S}</i>")

        await call.message.answer(text, disable_web_page_preview=True, reply_markup=await ikb.update_menu())

    
    async def open_chat(self, m: Message):
        count = m.text.replace("/chat", '').strip()
        chat_admin_uid = await self.format_chat_uid(chat_type=m.chat.type, chat_uid=m.chat.id)

        if not count.isdigit(): return await m.answer("Неверный формат команды!")
        
        chat = await self.udb.user.get_chat(count=int(count), admin_chat_uid=chat_admin_uid)

        if not chat: return await m.answer("Чат не найден!")

        await m.reply(TextBot.text_chat_info.format(
            title=chat.title, chat_uid=chat.chat_uid, status='🟡' if chat.connect else '🔴'),
            reply_markup=await ikb.group_settings_menu(chat_uid=chat.id, connect=chat.connect))
    

    async def update_time(self, call: CallbackQuery):
        await self.open_chats(call=call)

    
    async def go_to_chats(self, call: CallbackQuery):
        await call.message.delete()
        chat_admin_uid = await self.format_chat_uid(chat_type=call.message.chat.type, chat_uid=call.message.chat.id)
        urls, phones, spam_chat = await self.udb.user.get_chats_url(admin_chat_uid=chat_admin_uid)

        phone_url_map = {}

        for url, chat_id in urls:
            for phone, account_uid in phones:
                try:
                    member = await call.bot.get_chat_member(chat_id=chat_id, user_id=account_uid)
                    if member.status != 'member': 
                        if phone not in phone_url_map: 
                            phone_url_map[phone] = url
                except Exception as e:
                    print(f"Ошибка при проверке пользователя {phone} в чате {url}: {e}")

        if phone_url_map:
            resp = await join_from_chats(
                phone_url_map=phone_url_map, 
                admin_chat=chat_admin_uid,
                manager=self.udb,
                spam_chat=spam_chat,
                bot=call.bot
            )

            success_count = resp["success"]
            failed_accounts = resp["failed"]

            result_text = f"📊 Статистика вступления в чаты:\n"
            result_text += f"✅ Успешно вошли: {success_count}/{len(phone_url_map)}\n"

            if failed_accounts:
                result_text += "❌ Ошибки:\n"
                for acc in failed_accounts:
                    result_text += f"- {acc['phone']} (Чат: {acc['chat']}): {acc['error']}\n"

            await call.message.answer(result_text)
        else:
            await call.message.answer("Все пользователи уже состоят в чатах.")

    
    async def connect_chat(self, call: CallbackQuery, callback_data: GroupCallback):
        await call.message.delete()
        chat_admin_uid = await self.format_chat_uid(chat_type=call.message.chat.type, chat_uid=call.message.chat.id)
        chat = await self.udb.user.set_connect_chat(chat_uid=callback_data.chat_uid, admin_chat_uid=chat_admin_uid)

        await call.message.answer(TextBot.text_chat_info.format(
            title=chat.title, chat_uid=chat.chat_uid, status='🟡' if chat.connect else '🔴'),
            reply_markup=await ikb.group_settings_menu(chat_uid=callback_data.chat_uid, connect=chat.connect))
        
    
    async def delete_chat(self, call: CallbackQuery, callback_data: GroupCallback):
        await call.message.delete()
        chat_admin_uid = await self.format_chat_uid(chat_type=call.message.chat.type, chat_uid=call.message.chat.id)
        await self.udb.user.delete_chat(chat_uid=callback_data.chat_uid, admin_chat_uid=chat_admin_uid)
        await call.message.answer("Чат удален!")


    async def add_license(self, m: Message):
        if m.from_user.id in self.cfg.ADMINS and m.chat.type == 'private':
            args = m.text.replace('/add', '').split()
            uid, token = args
            tasks = []
            
            if len(args) != 2: return await m.answer("❌ Неверный формат! Используйте: /add -ID- -TOKEN-")

            bot_info = await self.is_valid_token(token=token)

            if not bot_info: return await m.answer("❌ Недействительный токен! Проверьте и попробуйте снова.")

            bot_username = bot_info.get("username", "неизвестно")
            bot_name = bot_info.get("first_name", "Без имени")
            bot_uid = bot_info.get("id", "неизвестный ID")

            await self.udb.accounts.add_licence_token(uid=int(uid), token=token)
            bot_instance = SettingsBot(token=token)
            await setup(bot_instance=bot_instance)

            await m.answer(f"⚙️ Токен успешно добавлен!\n\n🤖 Бот: {bot_name} (@{bot_username})\n🆔 ID: {bot_uid}")

            task = asyncio.create_task(bot_instance.dp.start_polling(bot_instance))
            tasks_bot[uid] = (task, bot_instance)


    async def no_register_account(self, m: Message):
        if m.chat.type in ['supergroup', 'group']:
            chat_uid = await self.format_chat_uid(chat_type=m.chat.type, chat_uid=m.chat.id)
            admin_chat = await self.udb.user.get_admin_chat(chat_uid=chat_uid)

            if not admin_chat: return

            user = await self.udb.accounts.exists_account(uid=m.from_user.id)

            if not user:
                text = TextBot.no_register_account.format(
                    title=m.chat.title, uid=m.from_user.id, time=datetime.now().strftime("%H:%M:%S"))
                
                chat_id_str = str(chat_uid).replace("-100", "")
                message_link = f"https://t.me/c/{chat_id_str}/{m.message_id}"

                try:
                    await m.bot.send_message(
                        chat_id=admin_chat, text=text,
                        reply_markup=await ikb.error_menu(chat_uid=chat_uid, url=message_link, mes_id=m.message_id))
                except: pass
            
    
    async def del_license(self, m: Message):
        if m.from_user.id in self.cfg.ADMINS and m.chat.type == 'private':
            uid = int(m.text.replace('/del', '').split()[0])
            resp = await self.udb.user.delete_licence(uid=uid)

            if not resp: return await m.answer("Такого айди нет!")

            await m.answer("Лицензия успешно удалена!")
            
            task, bot = tasks_bot.get(str(uid), (None, None))

            if task:
                await bot.dp.stop_polling()
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError: print(f"Задача для {uid} была отменена.")
            else:
                print(f"Задача для {uid} не найдена.")

    
    async def delete_message_chat(self, call: CallbackQuery, callback_data: DeleteTextCallback):
        try:
            await call.bot.delete_message(chat_id=callback_data.chat_uid, message_id=callback_data.mes_id)
            await call.message.edit_text("Сообщение удалено!")
        except: pass


    async def open_chats_or_close(self, call: CallbackQuery):
        admin_chat = await self.format_chat_uid(chat_type=call.message.chat.type, chat_uid=call.message.chat.id)
        connect = await self.udb.user.connect_chats(admin_chat=admin_chat)

        await call.message.edit_reply_markup(reply_markup=await ikb.chat_menu(connect=connect))
        