from asyncpg import Pool
from typing import Protocol

__all__ = ["DB"]


class DB(Protocol):

    @property
    def pool(self) -> Pool: ...

    async def connect(self) -> None: ...

    async def close(self) -> None: ...
