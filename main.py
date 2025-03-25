import asyncio
from config import settings
from signature import SettingsBot
from handlers.setup import setup


class BotRunner:
    def __init__(self):
        self.bot_instance = SettingsBot(token=settings.TOKEN)
        self.running_bots = [] 


    async def multiplate_bots(self):
        await self.bot_instance.db_manager.async_main()
        
        tokens = await self.bot_instance.udb.accounts.get_tokens()
        tasks = []

        for token in tokens:
            bot_instance = SettingsBot(token=token)
            await setup(bot_instance=bot_instance)
            print(f"Бот {token} запущен")

            self.running_bots.append(bot_instance)
            tasks.append(asyncio.create_task(bot_instance.dp.start_polling(bot_instance)))

        return tasks  

    async def start(self):
        await setup(bot_instance=self.bot_instance)
        print("Основной бот запущен")
        await self.bot_instance.dp.start_polling(self.bot_instance)


    async def stop_bots(self):
        print("Остановка ботов...")
        for bot in self.running_bots:
            await bot.close()  
        await self.bot_instance.close()  


    async def run(self):
        try:
            tasks = await self.multiplate_bots()
            tasks.append(asyncio.create_task(self.start()))  
            await asyncio.gather(*tasks) 
        except KeyboardInterrupt:
            print("Bot stopped!")
            await self.stop_bots() 


if __name__ == '__main__':
    try:
        bot_runner = BotRunner()
        asyncio.run(bot_runner.run())
    except KeyboardInterrupt: print("Бот остановлен")
