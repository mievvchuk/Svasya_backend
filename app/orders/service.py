from typing import Optional

from app.database import db


PRODUCTS_COLLECTION = "products"
VARIANTS_COLLECTION = "product_variants"


async def get_available_products() -> list[dict]:
    products_collection = db[PRODUCTS_COLLECTION]
    variants_collection = db[VARIANTS_COLLECTION]

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
    products_collection = db[PRODUCTS_COLLECTION]
    variants_collection = db[VARIANTS_COLLECTION]

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