from datetime import datetime

from contextlib import asynccontextmanager

from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, Boolean, Float, BigInteger, DateTime, ForeignKey


# Базовый класс для всех моделей
class Base(DeclarativeBase):
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True, autoincrement=True)


class User(Base):
    __tablename__ = 'users'

    uid = Column(BigInteger(), nullable=False, unique=True)
    name = Column(String(100), nullable=True, default=None)
    username = Column(String(100), nullable=True, default=None)
    chat_admin_uid = Column(String(), default=None)
    spam_chat_uid = Column(String(), default=None)
    created_at = Column(DateTime, default=datetime.now())


class Accounts(Base):
    __tablename__ = 'accounts'

    admin_chat = Column(String(), nullable=False)
    phone = Column(String())
    account_uid = Column(BigInteger(), nullable=False, unique=True)
    username = Column(String(100), nullable=True, default=None)
    spam_chat_uid = Column(String(), default=None)
    connect = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.now())


class Chats(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_chat = Column(String(), nullable=False)
    chat_uid = Column(String())
    title = Column(String())
    url = Column(String())
    connect = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.now())


class License(Base):
    __tablename__ = 'license'

    uid = Column(BigInteger())
    token = Column(String())
    created_at = Column(DateTime, default=datetime.now())


class CreateDatabase:
    def __init__(self, database_url: str, echo: bool = False) -> None:
        """
        Инициализация асинхронного движка и сессии для работы с базой данных.
        """
        self.engine = create_async_engine(url=database_url, echo=echo)
        self.async_session = async_sessionmaker(
            bind=self.engine, 
            expire_on_commit=False,  
            class_=AsyncSession,  
            autoflush=False
        )

    @asynccontextmanager
    async def get_session(self):
        """
        Асинхронный контекстный менеджер для работы с сессиями.
        """
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    async def async_main(self):
        """
        Создание всех таблиц в базе данных и добавление базовых городов.
        """
        async with self.engine.begin() as conn:
            try:
                await conn.run_sync(Base.metadata.create_all)
                print("Таблицы успешно созданы")
            except Exception as e:
                print(f'Ошибка при создании таблиц: {e}')
