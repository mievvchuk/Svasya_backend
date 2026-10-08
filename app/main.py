from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import connect_to_mongo, close_mongo_connection
from app.products.router import router as products_router
from app.orders.router import router as orders_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()

    yield

    await close_mongo_connection()


app = FastAPI(
    title="Backend API",
    version="1.0.0",
    lifespan=lifespan,
)


app.include_router(products_router)
app.include_router(orders_router)


@app.get("/")
async def root():
    return {
        "message": "API is running"
    }
