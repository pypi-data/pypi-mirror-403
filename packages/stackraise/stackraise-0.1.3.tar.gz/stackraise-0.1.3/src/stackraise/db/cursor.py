from __future__ import annotations

from ast import Not
from contextlib import asynccontextmanager
from functools import reduce
from typing import AsyncIterable, Awaitable, Callable, Self
from pymongo.asynchronous.cursor import AsyncCursor as InnerCursor
from pymongo.asynchronous.command_cursor import AsyncCommandCursor as InnerCommandCursor
from stackraise.db.adapter import Adapter
from fastapi.responses import StreamingResponse
from .protocols import SortLike, ensure_mongo_sort




class CursorIterator[T]:
    __slots__ = ("_inner", "_adapter")

    def __init__(
        self,
        adapter: Adapter[T],
        inner: InnerCursor | InnerCommandCursor,

    ):
        self._adapter = adapter
        self._inner = inner
 
    def __aiter__(self):
        return self

    async def __anext__(self) -> T:
        item = await self._inner.next()
        return self._adapter.parse_item(item)

    async def close(self):
        await self._inner.close()


class CursorMixin[T]:
    async def aiter(self) -> CursorIterator[T]:
        """Returns an async iterator over the cursor."""
        raise NotImplementedError(
            "This method should be implemented in subclasses to return an async context manager for the cursor."
        )
    
    

    @asynccontextmanager
    async def cursor(self):
        iter = await self.aiter()
        try:
            yield iter
        finally:
            await iter.close()

    async def first(self) -> T | None:
        async with self.cursor() as cursor:
            async for x in cursor:
                return x

    async def last(self) -> T | None:
        async with self.cursor() as cursor:
            x = None
            async for x in cursor:
                continue
            return x
        
    async def single(self) -> T:
        async with self.cursor() as cursor:
            try:
                item = await cursor.__anext__()
            except StopAsyncIteration:
                raise ValueError("Expected a single item, but got none.")
            try:
                await cursor.__anext__()
            except StopAsyncIteration:
                return item
            raise ValueError("Expected a single item, but got multiple items.")
    
    async def all(self):
        """Returns all items in the cursor as a list."""
        async with self.cursor() as cursor:
            return [x async for x in cursor]

    as_list = all

    async def as_bytes(self):
        async with self.cursor() as cursor:
            items = [x async for x in cursor]
            return cursor._adapter.list.dump_json(items)

    async def as_str(self):
        return (await self.as_bytes()).decode("utf-8")

    def as_stream(
        self, status_code=200, headers: dict[str, str] | None = None, **kwargs
    ) -> StreamingResponse:
        """Returns a streaming response that yields JSON items."""

        async def generate():
            async with self.cursor() as cursor:
                yield b"["
                first = True
                async for item in cursor:
                    if not first:
                        yield b","
                    first = False
                    yield cursor._adapter.item.dump_json(item, **kwargs)
                yield b"]"

        return StreamingResponse(
            content=generate(),
            status_code=status_code,
            media_type="application/json",
            headers=headers,
        )


# results
class FindCursor[T](CursorMixin[T]):

    __slots__ = ("_inner",)

    def __init__(
        self,
        adapter: Adapter[T],
        inner: Callable[[], InnerCursor],
    ):
        self._adapter = adapter
        self._inner = inner

    async def aiter(self):
        return CursorIterator(self._adapter, self._inner())

    def skip(self, count: int) -> Self:
        inner = self._inner
        def inner_wrap() -> InnerCursor:
            return inner().skip(count)
        return self.__class__(self._adapter, inner_wrap)

    def limit(self, count: int) -> Self:
        inner = self._inner
        def inner_wrap() -> InnerCursor:
            return inner().limit(count)
        return self.__class__(self._adapter, inner_wrap)

    def sort(self, sort: SortLike) -> Self:
        inner = self._inner
        def inner_wrap() -> InnerCursor:
            return inner().sort(ensure_mongo_sort(sort))
        return self.__class__(self._adapter, inner_wrap)


# class AggregationCursor[T](CursorResult[T]):

#     __slots__ = ("_inner", "_adapter", "_started")

#     def __init__(
#         self,
#         adapter: Adapter[T],
#         inner: Callable[[], Awaitable[InnerCommandCursor]],
#     ):
#         super().__init__(adapter)
#         self._inner = inner

#     async def aiter(self) -> CursorIterator[T]:
#         return CursorIterator(self._adapter, await self._inner())

#     def result_type[U](self, type: type[U]) -> AggregationCursor[U]:
#         return self.__class__(self._inner, Adapter(type))





# class CursorBase[T]:
#     __slots__ = ("_adapter",)
#     _adapter: Adapter[T]

#     def __init__(self, adapter: Adapter[T]):
#         self._adapter = adapter

#     def __aiter__(self):
#         return self

#     def __await__(self):
#         return self.as_list().__await__()

#     async def first(self) -> T | None:
#         async for x in self:
#             return x

#     async def last(self) -> T | None:  # Single
#         x = None
#         async for x in self:
#             continue
#         return x

#     async def as_list(self) -> list[T]:
#         return [x async for x in self]

#     async def as_bytes(self):
#         return self._adapter.list.dump_json(await self.as_list())

#     async def as_str(self):
#         return (await self.as_bytes()).decode("utf-8")

#     def as_stream(
#         self, status_code=200, headers: dict[str, str] | None = None, **kwargs
#     ) -> StreamingResponse:
#         """Returns a streaming response that yields JSON items."""

#         async def generate():
#             yield b"["
#             first = True
#             async for item in self:
#                 if not first:
#                     yield b","
#                 first = False
#                 yield self._adapter.item.dump_json(item, **kwargs)
#             yield b"]"

#         return StreamingResponse(
#             content=generate(),
#             status_code=status_code,
#             media_type="application/json",
#             headers=headers,
#         )

