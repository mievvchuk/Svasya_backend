from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from app.config import settings

client: AsyncIOMotorClient | None = None
db = None
fs: AsyncIOMotorGridFSBucket | None = None


async def connect_to_mongo():
    global client, db, fs

    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    fs = AsyncIOMotorGridFSBucket(db)

    await client.admin.command("ping")

    print("Connected to MongoDB")


async def close_mongo_connection():
    global client

    if client:
        client.close()

        print("MongoDB connection closed")