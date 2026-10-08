from datetime import datetime

from pydantic import BaseModel, Field

from app.common.enums import ProductCategory


class ProductVariant(BaseModel):
    id: str
    color: str
    size: str | None
    image_url: str | None
    stock: int = Field(ge=0)


class ProductListResponse(BaseModel):
    id: str
    name: str
    description: str
    category: ProductCategory
    price: float = Field(ge=0)
    is_available: bool
    preview_image: str | None


class ProductDetailResponse(BaseModel):
    id: str
    name: str
    description: str
    category: ProductCategory
    price: float = Field(ge=0)
    is_available: bool
    created_at: datetime
    variants: list[ProductVariant]


Product = ProductDetailResponse