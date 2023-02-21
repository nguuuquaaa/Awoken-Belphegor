from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from motor.core import AgnosticCollection, AgnosticDatabase, AgnosticClient
from pydantic import BaseModel
from pymongo.errors import BulkWriteError
from collections.abc import Callable
import inspect
import typing

from belphegor import utils

#=============================================================================================================================#

class MongoQueue:
    def __init__(self, collection: "MongoCollectionEX", size: int = 1000, *, ordered: bool = True, callback: Callable[[Exception | None], typing.Any] | None = None):
        self._collection = collection
        self._size = size
        self._ordered = ordered
        self._queue = []
        self._is_closed = False
        self._callback = callback

    async def write(self, item):
        if self._is_closed:
            raise RuntimeError("Queue is closed")
        queue = self._queue
        queue.append(item)
        if len(queue) >= self._size:
            try:
                await self._collection.bulk_write(queue, ordered = self._ordered)
            except BulkWriteError:
                if self._ordered:
                    raise
            queue.clear()

    def clear(self):
        self._queue.clear()

    async def close(self):
        self._is_closed = True
        if self._queue:
            try:
                await self._collection.bulk_write(self._queue, ordered = self._ordered)
            except BulkWriteError:
                if self._ordered:
                    raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._callback is not None:
            maybe_coro = self._callback(exc_value)
            if inspect.isawaitable(maybe_coro):
                await maybe_coro
        if exc_value is not None:
            return False
        else:
            await self.close()
            return True

    def __del__(self):
        utils.ensure_task(self.close())

#=============================================================================================================================#

MotorCollectionBase = typing.cast(type[AgnosticCollection], AsyncIOMotorCollection)
class MongoCollectionEX(MotorCollectionBase):
    def batch_write(self, batch_size: int = 1000, *, ordered: bool = True, callback: Callable[[Exception | None], typing.Any] | None = None) -> MongoQueue:
        """
        Improve database writing performance by automatically spliting write requests into batches.
        """
        return MongoQueue(self, size = batch_size, ordered = ordered, callback = callback)

MotorDatabaseBase = typing.cast(type[AgnosticDatabase], AsyncIOMotorDatabase)
class MongoDatabaseEX(MotorDatabaseBase):
    def __getattr__(self, name) -> MongoCollectionEX:
        return super().__getattr__(name)

    def __getitem__(self, name) -> MongoCollectionEX:
        return MongoCollectionEX(self, name)

MotorClientBase = typing.cast(type[AgnosticClient], AsyncIOMotorClient)
class MongoClientEX(MotorClientBase):
    def __getattr__(self, name) -> MongoDatabaseEX:
        return super().__getattr__(name)

    def __getitem__(self, name) -> MongoDatabaseEX:
        return MongoDatabaseEX(self, name)

#=============================================================================================================================#

class MongoEX(BaseModel):
    client: MongoClientEX
    db: MongoDatabaseEX

    class Config:
        arbitrary_types_allowed = True
