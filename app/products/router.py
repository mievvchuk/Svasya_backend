from fastapi import APIRouter, HTTPException

from app.products.schemas import Product


router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[Product], responses={501: {"description": "Not implemented"}})
def get_products() -> list[Product]:
    raise HTTPException(status_code=501, detail="Products API is not implemented yet")


@router.get(
    "/{product_id}",
    response_model=Product,
    responses={501: {"description": "Not implemented"}},
)
def get_product(product_id: str) -> Product:
    raise HTTPException(status_code=501, detail="Products API is not implemented yet")
