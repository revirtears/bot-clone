from utils.loguru import setup_logger
from handlers.client.client import Client
from handlers.client.add_account import Account
from handlers.client.admin_panel import AdminChat


async def setup(bot_instance):
        await bot_instance.db_manager.async_main()

        user_client = Client(bot=bot_instance)
        account = Account(bot=bot_instance)
        admin_chat = AdminChat(bot=bot_instance)

        await user_client.register_handlers()
        await account.register_handlers()
        await admin_chat.register_handlers()
        await setup_logger(level=bot_instance.config.LOGGING_LEVEL)