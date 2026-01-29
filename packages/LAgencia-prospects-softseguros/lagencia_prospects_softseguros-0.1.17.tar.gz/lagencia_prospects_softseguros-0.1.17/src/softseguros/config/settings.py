import os
from functools import lru_cache
from typing import List

from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LOG_LEVEL: str

    # credentials libertador
    GRANT_TYPE: str
    CLIENT_ID_ESTRELLA: str
    CLIENT_SECRET_ESTRELLA: str

    CLIENT_ID_LIVIN: str
    CLIENT_SECRET_LIVIN: str

    CLIENT_ID_CASTILLO: str
    CLIENT_SECRET_CASTILLO: str

    CLIENT_ID_VILLACRUZ: str
    CLIENT_SECRET_VILLACRUZ: str

    # credentials softseguros
    USERNAME_SOFTSEGUROS: str
    USERNAME_PASSWORD_SOFTSEGUROS: str

    # credentials softin
    TOKEN_SOFTIN_VILLACRUZ: str
    TOKEN_SOFTIN_CASTILLO: str
    TOKEN_SOFTIN_ESTRELLA: str

    # credentials DB
    URL_SQLSERVER_SEGUROS_BOLIVAR_ALEPH: str


    # phones for notifications
    PHONES_PROD: List[str]
    PHONES_DEV: List[str]

    # api key gemini:
    GOOGLE_API_KEY: str

    model_config = SettingsConfigDict(
        # env_file=_optional_env_file(),
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Carga configuración la primera vez que una tarea lo necesita.
    Invócalo dentro del callable de cada tarea (runtime, no import).
    """
    try:
        # print(f"{_optional_env_file()=}")
        s = Settings()

        # logger.info(f"[settings] PYTHON_ENV_ORION={s.model_config.get('env_file')}")
        logger.info(f"[settings] PYTHON_ENV_ORION={os.getenv('PYTHON_ENV_ORION')=}")
        logger.debug(f"[settings] LOG_LEVEL={s.LOG_LEVEL}")
        return s
    except Exception as e:
        logger.error(f"[settings] Error cargando settings: {e}")
        raise
