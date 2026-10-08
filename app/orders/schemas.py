from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.enums import OrderStatus


class OrderCreateItem(BaseModel):
    variant_id: str
    quantity: int = Field(gt=0, description="Quantity must be greater than 0")


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1)
    phone: str = Field(min_length=1)
    email: EmailStr
    items: list[OrderCreateItem] = Field(min_length=1)

    @field_validator("customer_name", "phone")
    @classmethod
    def strip_and_check_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or contain only whitespace")
        return stripped


class OrderItemResponse(BaseModel):
    product_id: str
    variant_id: str
    product_variant_id: str | None = None
    name: str
    color: str
    size: str | None = None
    quantity: int
    price: float


class OrderResponse(BaseModel):
    id: str
    customer_name: str
    phone: str
    email: EmailStr
    total_price: float
    status: str
    created_at: datetime
    user_id: str | None = None
    assigned_manager_id: str | None = None
    items: list[OrderItemResponse]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderAssignManager(BaseModel):
    manager_id: str
