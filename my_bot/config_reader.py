from functools import lru_cache
from pathlib import Path


from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field, model_validator, HttpUrl


class Settings(BaseSettings):
    CITY: str = Field(default="Москва")
    YANDEX_TOKEN: SecretStr = SecretStr("YANDEX_TOKEN")
    YANDEXMETEO_URL: HttpUrl = Field(default=None)
    BOT_TOKEN: SecretStr = SecretStr("BOT_TOKEN")
    DB_NAME: str | None = Field(default=None)
    DB_URI: str | None = Field(default=None)
    FOLDER_LOG: Path = Field(default="logs/")
    DEBUG: bool = Field(default=False)
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    @classmethod
    def get_path(cls, path: Path) -> Path:
        file_path = Path(__file__).parent / path
        file_path.mkdir(exist_ok=True, parents=True)
        abs_path = file_path.absolute()
        return abs_path


    @model_validator(mode='after')
    def change_path(self):
        """
        Метод класса для корректировки путей.
        :return:
        """
        self.FOLDER_LOG = self.get_path(self.FOLDER_LOG)
        self.DB_URI = f"sqlite+aiosqlite:///{self.DB_NAME}"

        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings: Settings = get_settings()
