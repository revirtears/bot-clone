from asyncio import Lock
from sqlalchemy.ext.asyncio import async_sessionmaker


class BaseRequests:
    def __init__(self, db_session_maker: async_sessionmaker) -> None:
        self.db_session_maker = db_session_maker
        self.lock = Lock()