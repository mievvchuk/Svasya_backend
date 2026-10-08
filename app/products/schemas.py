from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.common.enums import ProductCategory


class ProductVariant(BaseModel):
    id: str
    product_id: str | None = None
    color: str
    size: str | None
    image_url: str
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


class ProductCreate(BaseModel):
    id: str | None = Field(default=None, description="Custom ID slug, e.g. 'product_tshirt_custom'. Auto-generated if empty.")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    category: ProductCategory
    price: float = Field(ge=0)
    is_available: bool = True
    preview_image: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: ProductCategory | None = None
    price: float | None = Field(default=None, ge=0)
    is_available: bool | None = None
    preview_image: str | None = None


class VariantCreate(BaseModel):
    id: str | None = Field(default=None, description="Custom ID slug. Auto-generated if empty.")
    color: str = Field(min_length=1)
    size: str | None = None
    image_url: str = Field(min_length=1)
    stock: int = Field(default=0, ge=0)


class VariantStockUpdate(BaseModel):
    stock: int = Field(description="Number of items to set or add")
    mode: Literal["set", "add"] = Field(
        default="set",
        description="'set' to overwrite stock, 'add' to increment existing stock (e.g. receiving a new batch)",
    )
