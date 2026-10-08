from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class OrderCreateItem(BaseModel):
    variant_id: str
    quantity: int =Field(gt=0)

class OrderCreate(BaseModel):
    customer_name: str =Field(min_length=1)
    phone: str = Field(min_length=1)
    email: EmailStr
    items: list[OrderCreateItem]=Field(min_length=1)

class OrderItemResponse(BaseModel):
    product_id: str
    variant_id: str
    name: str
    color: str
    size: str | None=None
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
    items: list[OrderItemResponse]
