from typing import Union

from sqlalchemy import select, update, func, or_, and_, delete, desc, insert

from database.models import (
    User, Accounts, Chats, License
)

from database.requests.base import BaseRequests


class UserRequests(BaseRequests):
    async def exists_user(self, uid: int, name: str, uname: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                user = (await session.execute(select(User).where(User.uid == uid))).scalar()

                if user: return True

                new_user = User(uid=uid, name=name, username=uname)
                session.add(new_user)
                await session.commit()


    async def select_user(self, uid: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                user = (await session.execute(select(User).where(User.uid == uid))).scalar()
                return user
            

    async def add_chat(self, uid: int, chat_uid: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                user = (await session.execute(select(User).where(User.uid == uid))).scalar()

                if not user.chat_admin_uid or not user.spam_chat_uid:
                    values = {}
                    if not user.chat_admin_uid:
                        values["chat_admin_uid"] = chat_uid
                    elif not user.spam_chat_uid:
                        values["spam_chat_uid"] = chat_uid
                    
                    await session.execute(update(User).where(User.uid == uid).values(**values))
                    await session.commit()
                    return True
                return False
            
            
    async def get_account_or_chat(self, chat_uid: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                accounts = (await session.execute(select(func.count(Accounts.id)).where(Accounts.admin_chat == chat_uid))).scalar()
                chats = (await session.execute(select(func.count(Chats.id)).where(Chats.admin_chat == chat_uid))).scalar()

                return accounts, chats
            
    
    async def exist_account(self, uid: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                return (await session.execute(select(Accounts).where(Accounts.account_uid == uid))).scalar()
            
    
    async def add_active_chat(self, chat_uid: str, title: str, url: str, admin_chat_uid: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                new_chat = Chats(admin_chat=admin_chat_uid, chat_uid=chat_uid, title=title, url=url)
                session.add(new_chat)
                await session.commit()
                return new_chat.id
            
    
    async def get_chats(self, admin_chat_uid: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                chats = (await session.execute(select(Chats).where(Chats.admin_chat == admin_chat_uid))).scalars().all()
                return [(row.url, row.connect) for row in chats]
            
    
    async def get_chat(self, count: int, admin_chat_uid: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                chat = (
                    await session.execute(select(Chats).where(Chats.admin_chat == admin_chat_uid).order_by(
                        Chats.id).offset(count - 1).limit(1))).scalars().first()
                return chat
            
    
    async def get_chats_url(self, admin_chat_uid: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                data = (await session.execute(
                    select(Chats.url, Chats.chat_uid, Accounts.phone, Accounts.account_uid)
                    .outerjoin(Accounts, Chats.admin_chat == Accounts.admin_chat)
                    .where(Chats.admin_chat == admin_chat_uid)
                    .group_by(Chats.url, Chats.chat_uid, Accounts.phone, Accounts.account_uid)  
                )).all()

                spam_chat = (await session.execute(
                    select(Accounts.spam_chat_uid).where(Accounts.admin_chat == admin_chat_uid)
                )).scalar()

                chat_urls = [(row[0], row[1]) for row in data if row[0] is not None and row[1] is not None]
                phone_numbers = [(row[2], row[3]) for row in data if row[2] is not None and row[3] is not None]

                return chat_urls, phone_numbers, spam_chat
            
    
    async def set_connect_chat(self, chat_uid: int, admin_chat_uid: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                chat = (await session.execute(select(Chats).where(
                    Chats.id == chat_uid, Chats.admin_chat == admin_chat_uid))).scalars().first()

                if not chat: return None  

                chat.connect = not chat.connect
                await session.commit()
                return chat
            
    
    async def delete_chat(self, chat_uid: int, admin_chat_uid: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                await session.execute(delete(Chats).where(Chats.id == chat_uid, Chats.admin_chat == admin_chat_uid))
                await session.commit()

    
    async def get_chats_ids(self, admin_chat_uid: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                chats = (await session.execute(
                    select(Chats).where(Chats.admin_chat == admin_chat_uid, Chats.connect != False))).scalars().all()
                return [row.chat_uid for row in chats]
            
    
    async def get_chats_spams(self):
        async with self.lock:
            async with self.db_session_maker() as session:
                chats = (await session.execute(select(User.spam_chat_uid))).scalars().all()
                return chats
            
    
    async def get_admin_chat(self, spam_chat: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                return (await session.execute(select(User.chat_admin_uid).where(User.spam_chat_uid == spam_chat))).scalar()
            
    
    async def delete_licence(self, uid: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                license = (await session.execute(select(License).where(License.uid == uid))).scalar()

                if not license: return False

                await session.execute(delete(License).where(License.uid == uid))
                await session.commit()
                return True

            