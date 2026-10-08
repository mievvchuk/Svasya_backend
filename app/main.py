from fastapi import FastAPI

from app.orders.router import router as orders_router
from app.products.router import router as products_router


app = FastAPI(title="Свась Shop API")


app.include_router(products_router, prefix="/api")
app.include_router(orders_router, prefix="/api")


@app.get("/")
def health_check():
    return {"message": "Свась Shop API is running"}