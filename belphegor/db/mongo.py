from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from motor.core import AgnosticClient, AgnosticDatabase, AgnosticCollection

#=============================================================================================================================#

AsyncIOMotorCollection: type[AgnosticCollection] = AsyncIOMotorCollection
class MongoCollectionEX(AsyncIOMotorCollection):
    pass

AsyncIOMotorDatabase: type[AgnosticDatabase] = AsyncIOMotorDatabase
class MongoDatabaseEX(AsyncIOMotorDatabase):
    def __getattr__(self, name) -> MongoCollectionEX:
        return super().__getattr__(name)

    def __getitem__(self, name) -> MongoCollectionEX:
        return MongoCollectionEX(self, name)

AsyncIOMotorClient: type[AgnosticClient] = AsyncIOMotorClient
class MongoClientEX(AsyncIOMotorClient):
    def __getattr__(self, name) -> MongoDatabaseEX:
        return super().__getattr__(name)

    def __getitem__(self, name) -> MongoDatabaseEX:
        return MongoDatabaseEX(self, name)
