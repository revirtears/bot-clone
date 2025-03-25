import os
import time
import asyncio

from aiogram import Bot

from telethon import events
from telethon import TelegramClient
from telethon.errors import *
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.messages import SetTypingRequest
from telethon.tl.types import SendMessageTypingAction

from config import params
from utils.loguru import logger
from database.requests.manager import RequestsManager


clients = {}
current_task_client = {}


class RegisterClient:
    def __init__(self, phone: str):
        self.client = TelegramClient(
            session=f'sessions/session-{phone}', 
            api_id=params['api_id'], 
            api_hash=params['api_hash'], 
            device_model=params['device_model'], 
            system_version=params['system_version'], 
            app_version=params['app_version']
        )
        self.phone = phone
        self.connected = False
        self.lock = asyncio.Lock()


    async def __aenter__(self):
        if not self.client.is_connected(): 
            await self.client.connect()
            self.connected = True
            clients[self.phone] = self  
        print(f"✅ Клиент {self.phone} подключен.")
        return self


    async def __aexit__(self, exc_type, exc, tb):
        await self.disconnect_account()


    async def disconnect_account(self):
        await self.client.disconnect()
        clients.pop(self.phone, None) 
        print(f"❌ Клиент {self.phone} отключен.")
        return True


    async def send_phone_code(self):
        try:
            if not self.connected:  
                await self.client.connect()
                
            print(f"📩 Отправка кода на номер {self.phone}...")
            send_code = await self.client.send_code_request(self.phone)
            time.sleep(2)
            return True, send_code.phone_code_hash
        except PhoneNumberInvalidError:
            return False, '❌ Номер телефона недействителен!'
        except Exception as e:
            return self.log_error(e)


    async def register_account(self, phone_code_hash: str, code: str):
        try:
            if not self.client.is_connected():  
                await self.client.connect()
                
            print(f"🔑 Попытка входа в аккаунт {self.phone}...")
            await self.client.sign_in(phone=self.phone, code=code, phone_code_hash=phone_code_hash)
            return True, await self.client.get_me()
        except SessionPasswordNeededError:
            return False, '🔒 Требуется 2FA'
        except PhoneCodeInvalidError:
            return False, '❌ Неверный код!'
        except PhoneCodeExpiredError:
            return False, '⏳ Время для ввода кода истекло.'
        except Exception as e:
            return self.log_error(e)
        finally: await self.client.disconnect()


    async def join_group(self, chat_url: str, admin_chat: str, manager: RequestsManager, spam_chat: str, bot: Bot):
        async with self.lock:
            try:
                task_current = current_task_client.get(self.client, None)
                if task_current:
                    if not task_current.done() or task_current.done():
                        print("Cancelling pending task.")
                        task_current.cancel()
                        try:
                            await task_current
                        except asyncio.CancelledError:
                            pass 

                if not self.client.is_connected():
                    await self.client.connect()

                print(f"🔹 {self.phone} вступает в группу {chat_url}...")

                try:
                    # Пробуем войти в чат по URL
                    await self.client(ImportChatInviteRequest(hash=chat_url.replace("https://t.me/+", '').strip()))
                    print(f"✅ {self.phone} успешно вошёл в группу {chat_url}")

                    # После успешного входа запускаем асинхронный прослушиватель сообщений
                    current_task_client[self.client] = asyncio.create_task(
                        self.listen_for_messages(chat_id=spam_chat, manager=manager, admin_chat_id=admin_chat, bot=bot))

                    return True, None
                except RPCError as e:
                    # В случае ошибки при входе в чат
                    error_message = f"🚨 Ошибка при входе {self.phone} в группу {chat_url}: {e}"
                    print(error_message)
                    await self.client.disconnect()
                    return False, error_message

            except Exception as e:
                # Логируем ошибку, если что-то пошло не так
                return self.log_error(e)
            

    async def message_handler(self, event):
        """Обработчик входящих сообщений."""
        try:
            user = await self.client.get_me()

            if event.sender_id == user.id:

                logger.info(f"💬 Новое сообщение от {event.sender_id}: {event.message.text}")

                chats = await self.manager.user.get_chats_ids(admin_chat_uid=self.admin_chat_id)
                logger.info(f"Чаты для пересылки: {chats}")

                reply_to_text = None
                if event.message.reply_to:
                    try:
                        reply_message = await event.message.get_reply_message()
                        reply_to_text = reply_message.text if reply_message else None
                        logger.info(f"📌 Реплай на: {reply_to_text}")
                    except Exception as e:
                        logger.error(f"⚠ Ошибка при получении реплая: {e}")

                media = None
                if event.message.media:
                    media = event.message.photo or event.message.video or event.message.document

                for chat in chats:
                    chat = int(chat)
                    reply_to_msg_id = None
                    
                    try:
                        await self.client(SetTypingRequest(chat, SendMessageTypingAction()))
                        await asyncio.sleep(2)

                        if reply_to_text:
                            async for msg in self.client.iter_messages(chat, limit=50):
                                if msg.text and msg.text.strip() == reply_to_text.strip():
                                    reply_to_msg_id = msg.id
                                    logger.info(f"🔗 Найдено сообщение для реплая в {chat}: {reply_to_msg_id}")
                                    break
                            else:
                                logger.warning(f"⚠ Сообщение для реплая в {chat} не найдено")

                        if media:
                            await self.client.send_file(entity=chat, file=media, caption=event.message.text, reply_to=reply_to_msg_id)
                        else:
                            await self.client.send_message(entity=chat, message=event.message.text, reply_to=reply_to_msg_id)
                        
                        logger.info(f"✅ Сообщение отправлено в {chat} (реплай к {reply_to_msg_id})")
                    except Exception as e:
                        logger.error(f"❌ Ошибка при отправке в {chat}: {e}")
                        await self.bot.send_message(chat_id=self.admin_chat_id, text=f"❌ Ошибка при отправке в {chat}: {e}")

        except Exception as e:
            logger.critical(f"❌ Критическая ошибка обработки сообщения: {e}")
            await self.bot.send_message(chat_id=self.admin_chat_id, text=f"❌ Критическая ошибка: {e}")


    async def listen_for_messages(self, chat_id: str, manager: RequestsManager, admin_chat_id: str, bot: Bot):
        """Запускает прослушивание чатов."""
        clients[self.phone] = self
        self.admin_chat_id = admin_chat_id
        self.bot = bot
        self.manager = manager

        try:
            await self.client.connect()

            # Удаляем предыдущий обработчик (если он есть)
            self.client.remove_event_handler(self.message_handler)

            # Добавляем новый обработчик
            self.client.add_event_handler(self.message_handler, events.NewMessage(chats=int(chat_id)))

            logger.info(f"👂 {self.phone} слушает сообщения в чате {chat_id}...")

        except Exception as e:
            logger.critical(f"❌ Ошибка запуска: {e}")
            await bot.send_message(chat_id=admin_chat_id, text=f"❌ Ошибка запуска бота: {e}")


    def log_error(self, e):
        error_mapping = {
            PhoneNumberInvalidError: "❌ Неверный номер телефона! Проверьте формат и попробуйте снова.",
            SessionPasswordNeededError: "🔒 Требуется ввод пароля (2FA). Включена двухфакторная аутентификация.",
            PhoneCodeInvalidError: "❌ Введен неверный код! Попробуйте снова.",
            PhoneCodeExpiredError: "⏳ Время для ввода кода истекло. Запросите новый код.",
            ChatAdminRequiredError: "⚠️ Необходимы права администратора для выполнения этого действия.",
            UserAlreadyParticipantError: "ℹ️ Пользователь уже состоит в данной группе.",
            RPCError: "🚨 Произошла ошибка RPC. Проверьте соединение с сервером Telegram.",
            
            # 🔴 Добавлены новые ошибки
            UserDeactivatedBanError: "🚫 Этот аккаунт был удален или заблокирован Telegram.",
            UserIsBlockedError: "🔕 Вы не можете отправить сообщение этому пользователю. Возможно, он вас заблокировал.",
            FloodWaitError: "⏳ Слишком много запросов. Подождите некоторое время и попробуйте снова.",
            ChatWriteForbiddenError: "🔇 Вы не можете отправлять сообщения в этот чат. Возможно, у вас ограничены права.",
            PeerFloodError: "🚨 Превышен лимит отправки сообщений. Подождите перед следующей попыткой.",
            MessageTooLongError: "⚠️ Сообщение слишком длинное. Попробуйте сократить текст.",
            ChannelPrivateError: "🔒 Вы не можете взаимодействовать с этим каналом, так как он приватный.",
            UserRestrictedError: "🚫 Ваш аккаунт временно ограничен в действиях Telegram.",
            MessageIdInvalidError: "⚠️ Сообщение не найдено или уже удалено."
        }

        error_message = error_mapping.get(type(e), f"❌ Неизвестная ошибка: {str(e)}")
        
        print(f"🚨 Ошибка ({self.phone}): {error_message}")
        return False, error_message


async def send_phone_code_user(phone: str):
    async with RegisterClient(phone) as user_client:
        return await user_client.send_phone_code()


async def register_phone_code(phone: str, phone_code_hash: str, code: str):
    async with RegisterClient(phone) as user_client:
        status, resp = await user_client.register_account(phone_code_hash, code)
        return status, resp


async def join_from_chats(
        phone_url_map: dict[str, str], admin_chat: str, manager: RequestsManager, spam_chat: str, bot: Bot):
    tasks = []
    response_text = ""
    success_count = 0
    failed_accounts = []

    # Обрабатываем каждую пару (номер, чат)
    for phone, url in phone_url_map.items():
        if (clients.get(phone, None)):
            client = clients[phone]
        else:
            client = RegisterClient(phone)

        # Каждый клиент работает параллельно для каждого номера
        task = asyncio.create_task(client.join_group(chat_url=url, admin_chat=admin_chat, manager=manager, spam_chat=spam_chat, bot=bot))
        tasks.append(task)

    # Ожидаем завершения всех задач
    responses = await asyncio.gather(*tasks)

    # Обрабатываем результаты
    for (phone, url), (status, error) in zip(phone_url_map.items(), responses):
        if status:
            success_count += 1
        else:
            failed_accounts.append({"phone": phone, "chat": url, "error": error})

    response_text += "\n📊 Статистика вступления в чаты:\n"
    response_text += f"✅ Успешно вошли: {success_count}/{len(phone_url_map)}\n"
    
    if failed_accounts:
        response_text += "❌ Ошибки:\n"
        for acc in failed_accounts:
            response_text += f"- {acc['phone']} (Чат: {acc['chat']}): {acc['error']}\n"
    
    return {"success": success_count, "failed": failed_accounts, "response_text": response_text}


async def start_listen_message(phone: str, chat_id: str, manager: RequestsManager, admin_chat_id: str, bot: Bot):
    user_client = RegisterClient(phone)

    try:
        await user_client.listen_for_messages(chat_id=chat_id, manager=manager, admin_chat_id=admin_chat_id, bot=bot)
    except Exception as e:
        print(f"❌ Ошибка в слушателе: {e}") 


async def disconect_app(phone: str):
    if phone in clients:
        print(clients[phone])
        await clients[phone].disconnect_account()
        await asyncio.sleep(1)
        os.remove(f"sessions/session-{phone}.session")
        print(f"✅ Аккаунт {phone} успешно удален!")
        return True
    else:
        print(f"❌ Клиент {phone} не найден среди активных!")
        return False
