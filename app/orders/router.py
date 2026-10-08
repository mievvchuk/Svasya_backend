from fastapi import APIRouter

from app.database import db
from app.orders.schemas import OrderCreate, OrderResponse
from app.orders.service import create_order


router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


@router.post("", response_model=OrderResponse, status_code=201)
def create_order_endpoint(order_data: OrderCreate):
    return create_order(db, order_data)