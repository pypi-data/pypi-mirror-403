from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from softseguros import config

URL_SQLSERVER_SEGUROS_BOLIVAR_ALEPH = config.URL_SQLSERVER_SEGUROS_BOLIVAR_ALEPH

engine = create_async_engine(
    URL_SQLSERVER_SEGUROS_BOLIVAR_ALEPH,
    echo=False,
)

SessionAsyncLocalSoftseguros = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session_seguros_bolivar() -> AsyncGenerator[AsyncSession, None, None]:
    """Crea una sesión y la libera automáticamente al salir del contexto."""
    async with SessionAsyncLocalSoftseguros() as session:
        session_id = id(session)
        logger.info(f"Sesión creada con ID: {session_id}")
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
