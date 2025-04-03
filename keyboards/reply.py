from aiogram.utils.keyboard import ReplyKeyboardBuilder


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
