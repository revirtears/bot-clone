from typing import Union

from sqlalchemy import select, update, func, or_, and_, delete, desc, insert

from database.models import Accounts, User, License
from database.requests.base import BaseRequests


class AccountsRequests(BaseRequests):
    async def add_account(self, spam_chat: int, account_uid: int, uname: str, phone: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                user = (await session.execute(select(User).where(User.spam_chat_uid == spam_chat))).scalar()

                new_account = Accounts(
                    admin_chat=user.chat_admin_uid, account_uid=account_uid, username=uname, spam_chat_uid=user.spam_chat_uid, phone=phone)
                session.add(new_account)
                await session.commit()

                return user.spam_chat_uid, user.chat_admin_uid


    async def exists_account(self, uid: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                return (await session.execute(select(Accounts).where(Accounts.account_uid == uid))).scalar()
            
    
    async def cancel_connect(self, uid: int):
        async with self.lock:
            async with self.db_session_maker() as session:
                account = (await session.execute(select(Accounts).where(Accounts.account_uid == uid))).scalar()
                phone = account.phone

                await session.execute(delete(Accounts).where(Accounts.account_uid == uid))
                await session.commit()
                return phone
            
    
    async def add_licence_token(self, uid: int, token: str):
        async with self.lock:
            async with self.db_session_maker() as session:
                new_user = License(uid=uid, token=token)
                session.add(new_user)
                await session.commit()

    
    async def get_tokens(self):
        async with self.lock:
            async with self.db_session_maker() as session:
                tokens = (await session.execute(select(License.token))).scalars().all()
                return [token for token in tokens]
                