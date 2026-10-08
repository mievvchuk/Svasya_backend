from typing import Optional

import app.database as database

from bson import ObjectId


PRODUCTS_COLLECTION = "products"
VARIANTS_COLLECTION = "product_variants"


def _image_url(image_reference: str | None) -> str | None:
    if not image_reference:
        return None
    if ObjectId.is_valid(image_reference):
        return f"/api/products/image/{image_reference}"
    return image_reference


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
        preview_image = _image_url(product.get("preview_image"))
        if preview_image is None:
            preview_variant = await variants_collection.find_one(
                {
                    "product_id": product["id"],
                    "image_url": {"$exists": True, "$nin": [None, ""]},
                },
                sort=[("_id", 1)],
            )
            if preview_variant:
                preview_image = _image_url(preview_variant.get("image_url"))

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
                "image_url": _image_url(variant.get("image_url")),
                "stock": variant["stock"],
            }
            for variant in variants
        ],
    }


async def update_product_image_in_db(
    product_id: str,
    image_id: str,
    variant_id: str | None = None,
) -> bool:
    if database.db is None:
        raise RuntimeError("MongoDB is not connected.")

    if variant_id:
        result = await database.db[VARIANTS_COLLECTION].update_one(
            {"product_id": product_id, "id": variant_id},
            {"$set": {"image_url": image_id}},
        )
    else:
        result = await database.db[PRODUCTS_COLLECTION].update_one(
            {"id": product_id},
            {"$set": {"preview_image": image_id}},
        )

    return result.matched_count > 0