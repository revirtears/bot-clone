from sqlalchemy.ext.asyncio import async_sessionmaker

from database.requests.users import UserRequests
from database.requests.accounts import AccountsRequests


class RequestsManager:
    def __init__(self, db_session_maker: async_sessionmaker):
        self.user = UserRequests(db_session_maker=db_session_maker)
        self.accounts = AccountsRequests(db_session_maker=db_session_maker)
