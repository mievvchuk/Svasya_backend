from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import database
from app.config import settings
from app.orders.router import router as orders_router
from app.products.router import router as products_router

from app.users.router import router as users_router
from app.users.service import seed_default_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect_to_mongo()
    if database.db is not None:
        try:
            await seed_default_users(database.db)
        except Exception as e:
            print(f"Warning: Could not seed default users: {e}")

    yield

    await database.close_mongo_connection()


app = FastAPI(
    title="SVAS Merch Shop API",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if "*" not in settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Primary endpoints with /api prefix
app.include_router(products_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(users_router)

# Compatibility endpoints without /api prefix (supports direct /orders and /products)
app.include_router(products_router)
app.include_router(orders_router)


@app.get("/")
async def root():
    return {
        "message": "SVAS API is running",
        "docs": "/docs",
    }
