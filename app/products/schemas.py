from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ProductCategory


class ProductVariant(BaseModel):
    id: str
    color: str
    size: str
    image_url: str
    stock: int = Field(ge=0)


class Product(BaseModel):
    id: str
    name: str
    description: str
    category: ProductCategory
    price: float = Field(ge=0)
    is_available: bool
    created_at: datetime
    variants: list[ProductVariant]
