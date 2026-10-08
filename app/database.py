from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


client: AsyncIOMotorClient | None = None
db = None


async def connect_to_mongo():
    global client, db

    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]

    await client.admin.command("ping")

    print("Connected to MongoDB")


async def close_mongo_connection():
    global client

    if client:
        client.close()

        print("MongoDB connection closed")