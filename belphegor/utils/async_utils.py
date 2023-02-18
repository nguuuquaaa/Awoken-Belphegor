import asyncio
from typing import TypeVar, Generic
from collections.abc import AsyncIterator, AsyncIterable, Iterable, Awaitable
import collections

#=============================================================================================================================#

_T = TypeVar("_T")
_S = TypeVar("_S")

class AsyncIterWrapper(AsyncIterator[_T]):
    def __init__(self, coro: Awaitable[Iterable[_T]]):
        async def do_stuff():
            ret = await coro
            for item in ret:
                yield item
        self.coro = do_stuff()

    def __aiter__(self) -> AsyncIterator[_T]:
        return self

    async def __anext__(self) -> _T:
        return await self.coro.__anext__()

class WorkItem(Generic[_T, _S]):
    def __init__(self, item: _T):
        self.item = item
        self.result = asyncio.Future()

    def set_result(self, item: _S):
        self.result.set_result(item)

class WorkQueue(Generic[_T, _S]):
    def __init__(self):
        self._queue = collections.deque()

    async def work(self, item: _T) -> _S:
        ...

#=============================================================================================================================#

async def async_iter(iterable: Iterable[_T] | AsyncIterable[_T]) -> AsyncIterator[_T]:
    if isinstance(iterable, Iterable):
        for item in iterable:
            yield item
    elif isinstance(iterable, AsyncIterable):
        async for item in iterable:
            yield item
    else:
        raise TypeError(f"'{type(iterable)}' object is not iterable")

async def async_enumerate(iterable: AsyncIterable[_T]) -> AsyncIterator[_T]:
    i = 0
    async for item in iterable:
        yield i, item
        i += 1

def ensure_task(task: Awaitable[_T]) -> _T:
    async def run_task():
        return await task

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(run_task())
    else:
        return asyncio.create_task(run_task())
