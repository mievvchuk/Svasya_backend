from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.common.enums import ProductCategory, ProductColor, ProductSize


class ProductVariantResponse(BaseModel):
    id: str
    color: ProductColor
    size: Optional[ProductSize] = None
    image_url: str
    stock: int


class ProductListResponse(BaseModel):
    id: str
    name: str
    description: str
    category: ProductCategory
    price: float
    is_available: bool
    preview_image: Optional[str] = None


class ProductDetailResponse(BaseModel):
    id: str
    name: str
    description: str
    category: ProductCategory
    price: float
    is_available: bool
    created_at: datetime
    variants: list[ProductVariantResponse]