from fastapi import APIRouter, HTTPException, status, File, UploadFile
from fastapi.responses import StreamingResponse
from bson import ObjectId
from gridfs.errors import NoFile

# Правильний імпорт підключення до БД
import app.database as database 

from app.products.schemas import (
    ProductDetailResponse,
    ProductListResponse,
)
from app.products.service import (
    get_available_products,
    get_product_by_id,
    update_product_image_in_db
)

router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
)

@router.get("", response_model=list[ProductListResponse])
async def get_products():
    return await get_available_products()

@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product(product_id: str):
    product = await get_product_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/{product_id}/image", status_code=status.HTTP_200_OK)
async def upload_product_image(product_id: str, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    if database.fs is None:
        raise HTTPException(status_code=500, detail="GridFS is not initialized")

    # Читаємо файл у байти, щоб безпечно передати в базу
    contents = await file.read()

    # Записуємо файл у GridFS
    file_id = await database.fs.upload_from_stream(
        file.filename,
        contents,
        metadata={"content_type": file.content_type}
    )

    # Формуємо URL для отримання картинки
    image_url = f"/api/products/image/{str(file_id)}"

    # Оновлюємо товар
    updated = await update_product_image_in_db(product_id, image_url)
    
    if not updated:
        await database.fs.delete(file_id)
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Image uploaded successfully", "preview_image": image_url}


@router.get("/image/{image_id}", response_class=StreamingResponse)
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

    content_type = grid_out.metadata.get("content_type", "image/jpeg") if grid_out.metadata else "image/jpeg"

    return StreamingResponse(stream_generator(), media_type=content_type)