import httpx
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties

from config import settings
from database.models import CreateDatabase
from database.requests.manager import RequestsManager


class SettingsBot(Bot):
    def __init__(self, token: str) -> None:
        session = AiohttpSession()  
        super().__init__(token=token, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

        self.dp = Dispatcher()  
        self.db_manager = CreateDatabase(database_url=settings.get_db_url(), echo=False)
        self.udb = RequestsManager(db_session_maker=self.db_manager.get_session)
        self.config = settings
        self.running_bots = {} 


    async def format_chat_uid(self, chat_type: str, chat_uid: int):
        return str(chat_uid) if chat_type == 'supergroup' else f'-100{abs(chat_uid)}'


    async def is_valid_token(self, token: str) -> dict | None:
        url = f"https://api.telegram.org/bot{token}/getMe"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=5)
                data = response.json()
                return data["result"] if data.get("ok") else None
            except httpx.RequestError:
                return None


    async def close(self):
        await self.session.close() 
