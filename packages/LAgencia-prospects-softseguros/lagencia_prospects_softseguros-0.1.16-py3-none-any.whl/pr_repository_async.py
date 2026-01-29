import asyncio

from sqlalchemy import select

from pr_async_db import SessionAsyncLocalSoftseguros  # noqa: F401
from softseguros.database.models.models import ProspectsLibertador, ProspectsSoftin, ProspectsToSecure  # noqa: F401


async def main():
    result = []
    async with SessionAsyncLocalSoftseguros() as session:
        stmt = select(ProspectsLibertador)
        result = session.scalars(stmt).all()
    return result


if __name__ == "__main__":
    resut = asyncio.run(main)
    print(resut)
