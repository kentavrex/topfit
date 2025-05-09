import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class DBConfig(BaseSettings):
    DB_HOST: str = ""
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_PORT: int = 5432

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class GigachatConfig(BaseSettings):
    GIGACHAT_API_KEY: str = ""
    GIGACHAT_SCOPE: str = "GIGACHAT_API_PERS"


class Settings(BaseSettings):
    moscow_tz: datetime.tzinfo = ZoneInfo("Europe/Moscow")
    db_config: DBConfig = DBConfig()
    TELEGRAM_BOT_TOKEN: str = ""
    ADMIN_ID: int = 0


settings = Settings()


def current_moscow_datetime():
    return datetime.datetime.now(settings.moscow_tz)
