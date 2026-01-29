from abc import ABC, abstractmethod
from typing import AsyncGenerator, AsyncIterable


class AbstractStreamReader(ABC, AsyncIterable[bytes]):
    @abstractmethod
    async def iter_chunks(self, chunk_size: int = None) -> AsyncIterable[bytes]: ...

    @abstractmethod
    async def read(self, n=-1) -> bytes: ...

    @abstractmethod
    async def readany(self) -> bytes: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    def at_eof(self) -> bool: ...

    @abstractmethod
    def is_eof(self) -> bool: ...
