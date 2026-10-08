from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.common.enums import OrderStatus, UserRole
from app.orders.schemas import OrderCreate


PRODUCTS_COLLECTION = "products"
VARIANTS_COLLECTION = "product_variants"
ORDERS_COLLECTION = "orders"
USERS_COLLECTION = "users"


def _format_order(order: dict) -> dict:
    order_id = order.get("id")
    if not order_id and "_id" in order:
        order_id = str(order["_id"])
    return {
        "id": order_id,
        "customer_name": order.get("customer_name"),
        "phone": order.get("phone"),
        "email": order.get("email"),
        "total_price": order.get("total_price", 0.0),
        "status": order.get("status", "new"),
        "created_at": order.get("created_at"),
        "user_id": order.get("user_id"),
        "assigned_manager_id": order.get("assigned_manager_id"),
        "items": [
            {
                "product_id": item.get("product_id"),
                "variant_id": item.get("variant_id"),
                "product_variant_id": item.get("product_variant_id") or item.get("variant_id"),
                "name": item.get("name"),
                "color": item.get("color"),
                "size": item.get("size"),
                "quantity": item.get("quantity"),
                "price": item.get("price"),
            }
            for item in order.get("items", [])
        ],
    }


async def create_order(
    db: AsyncIOMotorDatabase,
    order_data: OrderCreate,
    user_id: Optional[str] = None,
) -> dict:
    products_collection = db[PRODUCTS_COLLECTION]
    variants_collection = db[VARIANTS_COLLECTION]
    orders_collection = db[ORDERS_COLLECTION]

    # 1. Aggregate requested quantities to protect against duplicate items in single request
    variant_totals: dict[str, int] = defaultdict(int)
    for item in order_data.items:
        variant_totals[item.variant_id] += item.quantity

    # 2. Fetch and validate each variant and product
    variants_map = {}
    products_map = {}

    for variant_id, total_quantity in variant_totals.items():
        variant = await variants_collection.find_one({"id": variant_id})
        if variant is None:
            try:
                variant = await variants_collection.find_one({"_id": ObjectId(variant_id)})
            except (InvalidId, TypeError):
                variant = None

        if variant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Variant '{variant_id}' not found",
            )

        product = await products_collection.find_one({"id": variant["product_id"]})
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product for variant '{variant_id}' not found",
            )

        if not product.get("is_available", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product '{product.get('name')}' is not available",
            )

        stock = variant.get("stock", 0)
        if stock < total_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for '{product.get('name')}'. Available: {stock}, requested: {total_quantity}",
            )

        variants_map[variant_id] = variant
        products_map[variant["product_id"]] = product

    # 3. Decrement stock for variants in the database
    for variant_id, total_quantity in variant_totals.items():
        variant = variants_map[variant_id]
        filter_doc = {"_id": variant["_id"]} if "_id" in variant else {"id": variant["id"]}
        await variants_collection.update_one(
            filter_doc,
            {"$inc": {"stock": -total_quantity}},
        )

    # 4. Build order items and calculate total price
    order_items = []
    total_price = 0.0

    for item in order_data.items:
        variant = variants_map[item.variant_id]
        product = products_map[variant["product_id"]]
        price = float(product.get("price", 0))

        total_price += price * item.quantity

        order_items.append(
            {
                "product_id": product["id"],
                "variant_id": item.variant_id,
                "product_variant_id": item.variant_id,
                "name": product.get("name"),
                "color": variant.get("color"),
                "size": variant.get("size"),
                "quantity": item.quantity,
                "price": price,
            }
        )

    total_price = round(total_price, 2)

    order_document = {
        "customer_name": order_data.customer_name,
        "phone": order_data.phone,
        "email": str(order_data.email),
        "total_price": total_price,
        "status": OrderStatus.NEW.value,
        "created_at": datetime.now(timezone.utc),
        "user_id": user_id,
        "assigned_manager_id": None,
        "items": order_items,
    }

    result = await orders_collection.insert_one(order_document)
    order_id = str(result.inserted_id)
    order_document["id"] = order_id

    # Sync the generated id into the document in DB if needed
    await orders_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"id": order_id}},
    )

    return _format_order(order_document)


async def get_orders(
    db: AsyncIOMotorDatabase,
    user_id: Optional[str] = None,
    status_filter: Optional[str] = None,
) -> list[dict]:
    query = {}
    if user_id:
        query["user_id"] = user_id
    if status_filter:
        query["status"] = status_filter

    orders_cursor = db[ORDERS_COLLECTION].find(query).sort("created_at", -1)
    orders = await orders_cursor.to_list(length=None)
    return [_format_order(order) for order in orders]


async def get_order_by_id(
    db: AsyncIOMotorDatabase,
    order_id: str,
) -> dict | None:
    query = {"id": order_id}
    order = await db[ORDERS_COLLECTION].find_one(query)

    if order is None:
        try:
            order = await db[ORDERS_COLLECTION].find_one({"_id": ObjectId(order_id)})
        except (InvalidId, TypeError):
            order = None

    if order is None:
        return None
    return _format_order(order)


async def update_order_status(
    db: AsyncIOMotorDatabase,
    order_id: str,
    new_status: str,
) -> dict:
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )

    await db[ORDERS_COLLECTION].update_one(
        {"id": order["id"]},
        {"$set": {"status": new_status}},
    )

    order["status"] = new_status
    return order


async def assign_order_manager(
    db: AsyncIOMotorDatabase,
    order_id: str,
    manager_id: str,
) -> dict:
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )

    manager = await db[USERS_COLLECTION].find_one({"id": manager_id})
    if not manager or manager.get("role") not in [UserRole.MANAGER.value, UserRole.ADMIN.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User '{manager_id}' is not an active manager or admin",
        )

    await db[ORDERS_COLLECTION].update_one(
        {"id": order["id"]},
        {"$set": {"assigned_manager_id": manager_id}},
    )

    order["assigned_manager_id"] = manager_id
    return order