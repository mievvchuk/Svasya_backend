from datetime import datetime, timezone

from fastapi import HTTPException
from pymongo.database import Database

from app.orders.schemas import OrderCreate


def find_variant(product: dict, variant_id: str) -> dict | None:
    variants = product.get("variants", [])

    for variant in variants:
        if variant.get("id") == variant_id:
            return variant

    return None


def create_order(db: Database, order_data: OrderCreate) -> dict:
    products_collection = db["products"]
    orders_collection = db["orders"]

    order_items = []
    total_price = 0.0

    for item in order_data.items:
        product = products_collection.find_one(
            {"variants.id": item.variant_id}
        )

        if product is None:
            raise HTTPException(
                status_code=404,
                detail=f"Variant '{item.variant_id}' not found",
            )

        if not product.get("is_available", False):
            raise HTTPException(
                status_code=400,
                detail=f"Product '{product.get('name')}' is not available",
            )

        variant = find_variant(product, item.variant_id)

        if variant is None:
            raise HTTPException(
                status_code=404,
                detail=f"Variant '{item.variant_id}' not found",
            )

        stock = variant.get("stock", 0)

        if stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for '{product.get('name')}'",
            )

        price = float(product.get("price", 0))

        total_price += price * item.quantity

        order_items.append(
            {
                "product_id": str(product["_id"]),
                "variant_id": item.variant_id,
                "name": product.get("name"),
                "color": variant.get("color"),
                "size": variant.get("size"),
                "quantity": item.quantity,
                "price": price,
            }
        )

    order_document = {
        "customer_name": order_data.customer_name,
        "phone": order_data.phone,
        "email": str(order_data.email),
        "total_price": total_price,
        "status": "new",
        "created_at": datetime.now(timezone.utc),
        "items": order_items,
    }

    result = orders_collection.insert_one(order_document)

    return {
        "id": str(result.inserted_id),
        **order_document,
    }