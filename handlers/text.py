class TextBot:
    welcome_message = """
<b>Приветсвую, выбери действие:</b>
"""

    add_active_chat_text = """
<b>Чат /chat{chat_id}</b> добавлен!

Название: <code>{title}</code>
Айди: [<code>{chat_uid}</code>]
Участников: {count}

<i>Для запуска откройте меню чата в списке чатов</i>
"""

    text_chat_info = """
Название чата: {title}
ID: {chat_uid}
Статус: {status}
"""
