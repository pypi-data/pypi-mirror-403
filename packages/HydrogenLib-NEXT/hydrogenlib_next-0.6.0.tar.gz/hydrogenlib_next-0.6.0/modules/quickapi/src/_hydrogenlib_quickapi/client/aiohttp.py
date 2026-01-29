from typing import AsyncIterator

import aiohttp

from .models.request import Request
from .models.response import AbstractResponse, AbstractStreamReader

from _hydrogenlib_core.typefunc import dict_unpack


class AiohttpStreamReader(AbstractStreamReader):
    def __init__(self, stream_reader: aiohttp.StreamReader):
        self._stream_reader = stream_reader

    async def iter_chunks(self, chunk_size: int = None) -> AsyncIterator[bytes]:
        return self._stream_reader.iter_chunked(chunk_size)

    async def read(self, n=-1) -> bytes:
        return await self._stream_reader.read(n)

    async def readany(self) -> bytes:
        return await self._stream_reader.readany()

    async def close(self) -> None:
        pass

    def at_eof(self) -> bool:
        return self._stream_reader.at_eof()

    def is_eof(self) -> bool:
        return self._stream_reader.is_eof()

    def __aiter__(self):
        return self._stream_reader.iter_any()


class AiohttpResponse(AbstractResponse):
    @property
    async def content(self) -> bytes:
        return await self._resp.content.read()

    @property
    async def text(self) -> str:
        return await self._resp.text()

    @property
    async def json(self):
        return await self._resp.json()

    @property
    def status_code(self) -> int:
        return self._resp.status

    async def aclose(self) -> None:
        self._resp.close()

    @property
    def stream_reader(self) -> AbstractStreamReader:
        return AiohttpStreamReader(self._resp.content)

    def __init__(self, response: aiohttp.ClientResponse):
        self._resp = response


async def request(request_info: Request, session: aiohttp.ClientSession):
    return session.request(
        request_info.method,
        **dict_unpack(

        )
    )
