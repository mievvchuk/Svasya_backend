import uuid
from datetime import datetime, timezone
from typing import Optional

import app.database as database

from bson import ObjectId
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app import database
from app.products.schemas import ProductCreate, ProductUpdate, VariantCreate


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
def _get_db(db: Optional[AsyncIOMotorDatabase] = None) -> AsyncIOMotorDatabase:
    actual_db = db if db is not None else database.db
    if actual_db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not connected",
        )
    return actual_db


async def get_available_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = "newest",
    limit: Optional[int] = None,
    skip: int = 0,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> list[dict]:
    db = _get_db(db)
    products_collection = db[PRODUCTS_COLLECTION]
    variants_collection = db[VARIANTS_COLLECTION]

    query: dict = {"is_available": True}

    # 1. Search by name or description
    if search and search.strip():
        s = search.strip()
        query["$or"] = [
            {"name": {"$regex": s, "$options": "i"}},
            {"description": {"$regex": s, "$options": "i"}},
        ]

    # 2. Filter by category
    if category:
        cat_val = category.value if hasattr(category, "value") else str(category)
        query["category"] = cat_val

    # 3. Filter by price range
    price_filter = {}
    if min_price is not None:
        price_filter["$gte"] = float(min_price)
    if max_price is not None:
        price_filter["$lte"] = float(max_price)
    if price_filter:
        query["price"] = price_filter

    # 4. Sorting
    sort_mapping = {
        "newest": [("created_at", -1)],
        "price_asc": [("price", 1)],
        "price_desc": [("price", -1)],
        "name": [("name", 1)],
    }
    sort_order = sort_mapping.get(sort_by, [("created_at", -1)])

    cursor = products_collection.find(query).sort(sort_order)
    if skip > 0:
        cursor = cursor.skip(skip)
    if limit is not None and limit > 0:
        cursor = cursor.limit(limit)

    products = await cursor.to_list(length=None)

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
        elif "preview_image" in product:
            preview_image = product.get("preview_image")

        result.append(
            {
                "id": product["id"],
                "name": product["name"],
                "description": product.get("description", ""),
                "category": product["category"],
                "price": product["price"],
                "is_available": product["is_available"],
                "preview_image": preview_image,
            }
        )

    return result


async def get_product_by_id(
    product_id: str,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> Optional[dict]:
    db = _get_db(db)
    products_collection = db[PRODUCTS_COLLECTION]
    variants_collection = db[VARIANTS_COLLECTION]

    query = {"id": product_id}
    product = await products_collection.find_one(query)
    if product is None:
        try:
            product = await products_collection.find_one({"_id": ObjectId(product_id)})
        except (InvalidId, TypeError):
            product = None

    if product is None:
        return None

    actual_id = product["id"]
    variants = await variants_collection.find(
        {"product_id": actual_id}
    ).sort("_id", 1).to_list(length=None)

    return {
        "id": product["id"],
        "name": product["name"],
        "description": product.get("description", ""),
        "category": product["category"],
        "price": product["price"],
        "is_available": product["is_available"],
        "created_at": product["created_at"],
        "variants": [
            {
                "id": variant["id"],
                "product_id": variant.get("product_id", actual_id),
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
# =========================================================================
# ADMIN OPERATIONS
# =========================================================================

async def create_product(
    data: ProductCreate,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> dict:
    db = _get_db(db)
    products_collection = db[PRODUCTS_COLLECTION]

    product_id = data.id
    if not product_id:
        slug = data.name.strip().lower().replace(" ", "_").replace("-", "_")
        product_id = f"product_{slug}_{uuid.uuid4().hex[:6]}"

    existing = await products_collection.find_one({"id": product_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with id '{product_id}' already exists",
        )

    product_doc = {
        "id": product_id,
        "name": data.name.strip(),
        "description": data.description.strip(),
        "category": data.category.value if hasattr(data.category, "value") else data.category,
        "price": round(float(data.price), 2),
        "is_available": data.is_available,
        "preview_image": data.preview_image,
        "created_at": datetime.now(timezone.utc),
    }

    result = await products_collection.insert_one(product_doc)
    product_doc["_id"] = result.inserted_id
    product_doc["variants"] = []
    return product_doc


async def update_product(
    product_id: str,
    data: ProductUpdate,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> dict:
    db = _get_db(db)
    products_collection = db[PRODUCTS_COLLECTION]

    product = await get_product_by_id(product_id, db)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )

    update_fields = {}
    if data.name is not None:
        update_fields["name"] = data.name.strip()
    if data.description is not None:
        update_fields["description"] = data.description.strip()
    if data.category is not None:
        update_fields["category"] = data.category.value if hasattr(data.category, "value") else data.category
    if data.price is not None:
        update_fields["price"] = round(float(data.price), 2)
    if data.is_available is not None:
        update_fields["is_available"] = data.is_available
    if data.preview_image is not None:
        update_fields["preview_image"] = data.preview_image

    if update_fields:
        await products_collection.update_one(
            {"id": product["id"]},
            {"$set": update_fields},
        )

    return await get_product_by_id(product["id"], db)


async def delete_product(
    product_id: str,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> dict:
    db = _get_db(db)
    products_collection = db[PRODUCTS_COLLECTION]
    variants_collection = db[VARIANTS_COLLECTION]

    product = await get_product_by_id(product_id, db)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )

    # Delete product and all associated variants
    await products_collection.delete_one({"id": product["id"]})
    await variants_collection.delete_many({"product_id": product["id"]})

    return {"message": f"Product '{product['id']}' and its variants deleted successfully"}


async def create_variant(
    product_id: str,
    data: VariantCreate,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> dict:
    db = _get_db(db)
    variants_collection = db[VARIANTS_COLLECTION]

    product = await get_product_by_id(product_id, db)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' not found",
        )

    variant_id = data.id
    if not variant_id:
        size_part = str(data.size).lower() if data.size else "onesize"
        color_part = data.color.lower().replace(" ", "_")
        variant_id = f"variant_{product['id']}_{color_part}_{size_part}_{uuid.uuid4().hex[:4]}"

    existing = await variants_collection.find_one({"id": variant_id})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Variant with id '{variant_id}' already exists",
        )

    variant_doc = {
        "id": variant_id,
        "product_id": product["id"],
        "color": data.color.strip(),
        "size": data.size.strip() if data.size else None,
        "image_url": data.image_url.strip(),
        "stock": data.stock,
    }

    await variants_collection.insert_one(variant_doc)
    return variant_doc


async def update_variant_stock(
    variant_id: str,
    stock_delta: int,
    mode: str = "set",
    db: Optional[AsyncIOMotorDatabase] = None,
) -> dict:
    db = _get_db(db)
    variants_collection = db[VARIANTS_COLLECTION]

    variant = await variants_collection.find_one({"id": variant_id})
    if not variant:
        try:
            variant = await variants_collection.find_one({"_id": ObjectId(variant_id)})
        except (InvalidId, TypeError):
            variant = None

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant '{variant_id}' not found",
        )

    current_stock = variant.get("stock", 0)
    if mode == "add":
        new_stock = max(0, current_stock + stock_delta)
    else:  # mode == "set"
        new_stock = max(0, stock_delta)

    filter_doc = {"_id": variant["_id"]} if "_id" in variant else {"id": variant["id"]}
    await variants_collection.update_one(
        filter_doc,
        {"$set": {"stock": new_stock}},
    )

    variant["stock"] = new_stock
    return {
        "id": variant["id"],
        "product_id": variant["product_id"],
        "color": variant["color"],
        "size": variant.get("size"),
        "stock": new_stock,
        "previous_stock": current_stock,
        "mode": mode,
    }


async def delete_variant(
    variant_id: str,
    db: Optional[AsyncIOMotorDatabase] = None,
) -> dict:
    db = _get_db(db)
    variants_collection = db[VARIANTS_COLLECTION]

    variant = await variants_collection.find_one({"id": variant_id})
    if not variant:
        try:
            variant = await variants_collection.find_one({"_id": ObjectId(variant_id)})
        except (InvalidId, TypeError):
            variant = None

    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant '{variant_id}' not found",
        )

    filter_doc = {"_id": variant["_id"]} if "_id" in variant else {"id": variant["id"]}
    await variants_collection.delete_one(filter_doc)

    return {"message": f"Variant '{variant['id']}' deleted successfully"}
