import json
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TOKEN: str
    LOGGING_LEVEL: str
    DB_USER: str
    DB_NAME: str
    DB_PASSWORD: str
    DB_HOST: str
    ADMINS: List[int]

    def get_db_url(self) -> str:
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}'

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()


with open("settings.json", "r", encoding="utf-8") as file:
    data = json.load(file)

    for item in data:
        params = item.get("params", {})
