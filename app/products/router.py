from typing import Optional

from bson import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from gridfs.errors import NoFile

from app import database
from app.common.enums import ProductCategory, UserRole
from app.products.schemas import (
    ProductCreate,
    ProductDetailResponse,
    ProductListResponse,
    ProductUpdate,
    ProductVariant,
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
    update_product_image_in_db,
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
    summary="Get available products (with optional search)",
)
async def get_products(
    search: Optional[str] = Query(None, description="Search keyword in name or description"),
    db=Depends(get_db),
):
    """
    Get all available products for the catalog with optional search.
    """
    return await get_available_products(
        search=search,
        db=db,
    )


@router.get(
    "/image/{image_id}",
    response_class=StreamingResponse,
    summary="Stream an uploaded product image from GridFS",
)
async def get_product_image(image_id: str):
    if not ObjectId.is_valid(image_id):
        raise HTTPException(status_code=400, detail="Invalid image ID")

    if database.fs is None:
        raise HTTPException(status_code=500, detail="GridFS is not initialized")

    try:
        grid_out = await database.fs.open_download_stream(ObjectId(image_id))
    except NoFile:
        raise HTTPException(status_code=404, detail="Image not found")

    async def stream_generator():
        while True:
            chunk = await grid_out.readchunk()
            if not chunk:
                break
            yield chunk

    content_type = (
        grid_out.metadata.get("content_type", "image/jpeg")
        if grid_out.metadata
        else "image/jpeg"
    )

    return StreamingResponse(stream_generator(), media_type=content_type)


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
# IMAGES & ADMIN MANAGEMENT
# =========================================================================

@router.post(
    "/{product_id}/image",
    status_code=status.HTTP_200_OK,
    summary="Upload product image to GridFS and link to product or variant",
)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    variant_id: str | None = None,
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    if database.fs is None:
        raise HTTPException(status_code=500, detail="GridFS is not initialized")

    contents = await file.read()
    file_id = await database.fs.upload_from_stream(
        file.filename or "upload",
        contents,
        metadata={"content_type": content_type},
    )

    image_id = str(file_id)
    image_url = f"/api/products/image/{image_id}"
    linked = False
    try:
        updated = await update_product_image_in_db(
            product_id,
            image_id,
            variant_id,
        )
        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Product or variant not found",
            )
        linked = True
    finally:
        if not linked:
            await database.fs.delete(file_id)

    return {
        "message": "Image uploaded successfully",
        "image_id": image_id,
        "image_url": image_url,
        "target": f"variant {variant_id}" if variant_id else "main product",
    }


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
    response_model=ProductVariant,
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
