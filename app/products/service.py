from typing import Optional

from app import database
from app.database import db

PRODUCTS_COLLECTION = "products"
VARIANTS_COLLECTION = "product_variants"


async def get_available_products() -> list[dict]:
    if database.db is None:
        raise RuntimeError("MongoDB is not connected.")

    products_collection = database.db[PRODUCTS_COLLECTION]
    variants_collection = database.db[VARIANTS_COLLECTION]

    products = await products_collection.find(
        {"is_available": True}
    ).sort("created_at", -1).to_list(length=None)

    result = []

    for product in products:
        product_id = product["id"]

        preview_variant = await variants_collection.find_one(
            {
                "product_id": product_id,
                "image_url": {"$ne": None},
            },
            sort=[("_id", 1)],
        )

        preview_image = None

        if preview_variant:
            preview_image = preview_variant.get("image_url")

        result.append(
            {
                "id": product["id"],
                "name": product["name"],
                "description": product["description"],
                "category": product["category"],
                "price": product["price"],
                "is_available": product["is_available"],
                "preview_image": preview_image,
            }
        )

    return result


async def get_product_by_id(product_id: str) -> Optional[dict]:
    if database.db is None:
        raise RuntimeError("MongoDB is not connected.")

    products_collection = database.db[PRODUCTS_COLLECTION]
    variants_collection = database.db[VARIANTS_COLLECTION]

    product = await products_collection.find_one(
        {"id": product_id}
    )

    if product is None:
        return None

    variants = await variants_collection.find(
        {"product_id": product_id}
    ).sort("_id", 1).to_list(length=None)

    return {
        "id": product["id"],
        "name": product["name"],
        "description": product["description"],
        "category": product["category"],
        "price": product["price"],
        "is_available": product["is_available"],
        "created_at": product["created_at"],
        "variants": [
            {
                "id": variant["id"],
                "color": variant["color"],
                "size": variant.get("size"),
                "image_url": variant["image_url"],
                "stock": variant["stock"],
            }
            for variant in variants
        ],
    }
async def update_product_image_in_db(product_id: str, image_url: str) -> bool:
    """
    Оновлює поле preview_image для конкретного товару.
    """
    # УВАГА: Якщо твій id у базі - це ObjectId, то зміни запит на: 
    # {"_id": ObjectId(product_id)} (і додай `from bson import ObjectId`)
    
    result = await db.products.update_one(
        {"id": product_id}, 
        {"$set": {"preview_image": image_url}}
    )
    return result.modified_count > 0