from fastapi import APIRouter, HTTPException, status

from app.products.schemas import (
    ProductDetailResponse,
    ProductListResponse,
)
from app.products.service import (
    get_available_products,
    get_product_by_id,
)


router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)


@router.get(
    "",
    response_model=list[ProductListResponse],
)
async def get_products():
    """
    Get all available products.
    """
    return await get_available_products()


@router.get(
    "/{product_id}",
    response_model=ProductDetailResponse,
)
async def get_product(product_id: str):
    """
    Get product details with all variants.
    """
    product = await get_product_by_id(product_id)

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product