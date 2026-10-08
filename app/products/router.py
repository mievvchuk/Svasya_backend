from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import database
from app.common.enums import ProductCategory, UserRole
from app.products.schemas import (
    ProductCreate,
    ProductDetailResponse,
    ProductListResponse,
    ProductUpdate,
    VariantCreate,
    VariantStockUpdate,
)
from app.products.service import (
    create_product,
    create_variant,
    delete_product,
    delete_variant,
    get_available_products,
    get_product_by_id,
    update_product,
    update_variant_stock,
)
from app.users.auth import require_roles


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


def get_db():
    if database.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not connected",
        )
    return database.db


# =========================================================================
# PUBLIC CATALOG ENDPOINTS
# =========================================================================

@router.get(
    "",
    response_model=list[ProductListResponse],
    summary="Get available products with search, category/price filters, and sorting",
)
async def get_products(
    search: Optional[str] = Query(None, description="Search keyword in name or description"),
    category: Optional[ProductCategory] = Query(None, description="Filter by category (e.g. tshirt, hoodie)"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    sort_by: Optional[Literal["newest", "price_asc", "price_desc", "name"]] = Query(
        "newest", description="Sorting option: newest, price_asc, price_desc, name"
    ),
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum items to return"),
    skip: int = Query(0, ge=0, description="Items to skip (pagination offset)"),
    db=Depends(get_db),
):
    """
    Get all available products for the catalog with optional search and filters.
    """
    return await get_available_products(
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        limit=limit,
        skip=skip,
        db=db,
    )


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="Get product details with all its variants",
)
async def get_product(product_id: str, db=Depends(get_db)):
    """
    Get product details with all variants (colors, sizes, stock).
    """
    product = await get_product_by_id(product_id, db)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


# =========================================================================
# ADMIN CATALOG & INVENTORY MANAGEMENT
# =========================================================================

@router.post(
    "",
    response_model=ProductDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create a new product",
)
async def create_product_endpoint(
    product_data: ProductCreate,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await create_product(product_data, db)


@router.patch(
    "/{product_id}",
    response_model=ProductDetailResponse,
    summary="[Admin] Update product details, price, or availability (is_available)",
)
async def update_product_endpoint(
    product_id: str,
    update_data: ProductUpdate,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await update_product(product_id, update_data, db)


@router.delete(
    "/{product_id}",
    summary="[Admin] Delete product and all its variants",
)
async def delete_product_endpoint(
    product_id: str,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await delete_product(product_id, db)


@router.post(
    "/{product_id}/variants",
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Add a new variant (color, size, stock) to a product",
)
async def create_variant_endpoint(
    product_id: str,
    variant_data: VariantCreate,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await create_variant(product_id, variant_data, db)


@router.patch(
    "/variants/{variant_id}/stock",
    summary="[Admin] Replenish or adjust variant inventory stock (modes: 'set' or 'add')",
)
async def update_stock_endpoint(
    variant_id: str,
    stock_data: VariantStockUpdate,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await update_variant_stock(
        variant_id=variant_id,
        stock_delta=stock_data.stock,
        mode=stock_data.mode,
        db=db,
    )


@router.delete(
    "/variants/{variant_id}",
    summary="[Admin] Delete a specific product variant",
)
async def delete_variant_endpoint(
    variant_id: str,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await delete_variant(variant_id, db)