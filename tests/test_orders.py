import asyncio
from datetime import datetime, timezone
import unittest
from types import SimpleNamespace
from fastapi import HTTPException

from app.common.enums import OrderStatus, UserRole
from app.orders.schemas import OrderCreate
from app.orders.service import (
    assign_order_manager,
    create_order,
    get_orders,
    update_order_status,
)


class FakeCollection:
    def __init__(self, documents):
        self.documents = documents

    async def find_one(self, query, *args, **kwargs):
        for document in self.documents:
            match = True
            for k, v in query.items():
                if k == "image_url" and isinstance(v, dict) and "$ne" in v:
                    if document.get(k) is None:
                        match = False
                        break
                    continue
                if document.get(k) != v:
                    match = False
                    break
            if match:
                return document
        return None

    def find(self, query):
        matching = []
        for document in self.documents:
            match = True
            for k, v in query.items():
                if k == "$or":
                    or_ok = False
                    for subq in v:
                        sub_ok = True
                        for sk, sv in subq.items():
                            if isinstance(sv, dict) and "$regex" in sv:
                                doc_val = str(document.get(sk, "")).lower()
                                if sv["$regex"].lower() not in doc_val:
                                    sub_ok = False
                                    break
                            elif document.get(sk) != sv:
                                sub_ok = False
                                break
                        if sub_ok:
                            or_ok = True
                            break
                    if not or_ok:
                        match = False
                        break
                elif isinstance(v, dict):
                    doc_val = document.get(k)
                    if "$gte" in v and (doc_val is None or doc_val < v["$gte"]):
                        match = False
                        break
                    if "$lte" in v and (doc_val is None or doc_val > v["$lte"]):
                        match = False
                        break
                elif document.get(k) != v:
                    match = False
                    break
            if match:
                matching.append(document)

        class Cursor:
            def __init__(self, items):
                self.items = list(items)

            def sort(self, field_or_list, direction=None):
                if isinstance(field_or_list, list) and len(field_or_list) > 0:
                    field, direction = field_or_list[0]
                else:
                    field = field_or_list
                reverse = (direction == -1)
                def sort_key(doc):
                    val = doc.get(field)
                    if val is None:
                        return (0, "")
                    if isinstance(val, (int, float)):
                        return (1, val)
                    if hasattr(val, "isoformat"):
                        return (2, val.isoformat())
                    return (3, str(val))
                self.items.sort(key=sort_key, reverse=reverse)
                return self

            def skip(self, n):
                self.items = self.items[n:]
                return self

            def limit(self, n):
                self.items = self.items[:n]
                return self

            async def to_list(self, length=None):
                return list(self.items)

        return Cursor(matching)

    async def insert_one(self, document):
        doc_copy = dict(document)
        doc_copy["_id"] = f"id-{len(self.documents) + 1}"
        if "id" not in doc_copy or not doc_copy["id"]:
            doc_copy["id"] = str(doc_copy["_id"])
        self.documents.append(doc_copy)
        return SimpleNamespace(inserted_id=doc_copy["_id"])

    async def update_one(self, filter_query, update_query, upsert=False):
        doc = await self.find_one(filter_query)
        if doc:
            if "$inc" in update_query:
                for k, v in update_query["$inc"].items():
                    doc[k] = doc.get(k, 0) + v
            if "$set" in update_query:
                for k, v in update_query["$set"].items():
                    doc[k] = v
        elif upsert:
            new_doc = dict(filter_query)
            if "$set" in update_query:
                new_doc.update(update_query["$set"])
            new_doc["_id"] = f"id-{len(self.documents) + 1}"
            if "id" not in new_doc:
                new_doc["id"] = new_doc["_id"]
            self.documents.append(new_doc)
            return SimpleNamespace(modified_count=1, upserted_id=new_doc["_id"])
        return SimpleNamespace(modified_count=1 if doc else 0)

    async def delete_one(self, filter_query):
        doc = await self.find_one(filter_query)
        if doc and doc in self.documents:
            self.documents.remove(doc)
            return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)

    async def delete_many(self, filter_query):
        to_remove = []
        for doc in self.documents:
            match = True
            for k, v in filter_query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                to_remove.append(doc)
        for doc in to_remove:
            self.documents.remove(doc)
        return SimpleNamespace(deleted_count=len(to_remove))


class FakeDatabase:
    def __init__(self):
        now = datetime.now(timezone.utc)
        self.collections = {
            "products": FakeCollection(
                [
                    {
                        "id": "product_tshirt_basic",
                        "name": "Basic T-Shirt",
                        "description": "Comfortable basic cotton shirt",
                        "category": "tshirt",
                        "price": 24.99,
                        "is_available": True,
                        "created_at": now,
                    },
                    {
                        "id": "product_unavailable",
                        "name": "Unavailable Shirt",
                        "description": "Not currently sold",
                        "category": "tshirt",
                        "price": 19.99,
                        "is_available": False,
                        "created_at": now,
                    },
                ]
            ),
            "product_variants": FakeCollection(
                [
                    {
                        "id": "variant_tshirt_black_m",
                        "product_id": "product_tshirt_basic",
                        "color": "black",
                        "size": "M",
                        "image_url": "https://example.com/tshirt.png",
                        "stock": 20,
                    },
                    {
                        "id": "variant_unavailable",
                        "product_id": "product_unavailable",
                        "color": "black",
                        "size": "M",
                        "image_url": "https://example.com/unavailable.png",
                        "stock": 10,
                    },
                ]
            ),
            "users": FakeCollection(
                [
                    {
                        "id": "mgr_1",
                        "name": "Manager One",
                        "email": "mgr1@example.com",
                        "role": UserRole.MANAGER.value,
                    }
                ]
            ),
            "orders": FakeCollection([]),
        }

    def __getitem__(self, collection_name):
        return self.collections[collection_name]


class CreateOrderTests(unittest.TestCase):
    def setUp(self):
        self.database = FakeDatabase()

    def test_create_order_success_and_stock_decremented(self):
        order_data = OrderCreate(
            customer_name="Test Customer",
            phone="+380991234567",
            email="test@example.com",
            items=[
                {
                    "variant_id": "variant_tshirt_black_m",
                    "quantity": 2,
                }
            ],
        )

        result = asyncio.run(create_order(self.database, order_data, user_id="user_123"))

        self.assertEqual(result["id"], "id-1")
        self.assertEqual(result["total_price"], 49.98)
        self.assertEqual(result["status"], OrderStatus.NEW.value)
        self.assertEqual(result["user_id"], "user_123")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["quantity"], 2)

        # Check stock was actually decremented in database (20 - 2 = 18)
        variant = asyncio.run(
            self.database["product_variants"].find_one({"id": "variant_tshirt_black_m"})
        )
        self.assertEqual(variant["stock"], 18)

    def test_create_order_aggregates_duplicates_and_rejects_insufficient_stock(self):
        # Variant has stock 20. Requesting 15 + 10 = 25 should fail
        order_data = OrderCreate(
            customer_name="Greedy Customer",
            phone="+380991234567",
            email="greedy@example.com",
            items=[
                {"variant_id": "variant_tshirt_black_m", "quantity": 15},
                {"variant_id": "variant_tshirt_black_m", "quantity": 10},
            ],
        )

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(create_order(self.database, order_data))

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Not enough stock", ctx.exception.detail)

    def test_create_order_rejects_unavailable_product(self):
        order_data = OrderCreate(
            customer_name="Buyer",
            phone="+380991234567",
            email="buyer@example.com",
            items=[{"variant_id": "variant_unavailable", "quantity": 1}],
        )

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(create_order(self.database, order_data))

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("is not available", ctx.exception.detail)

    def test_update_status_and_assign_manager(self):
        order_data = OrderCreate(
            customer_name="Buyer",
            phone="+380991234567",
            email="buyer@example.com",
            items=[{"variant_id": "variant_tshirt_black_m", "quantity": 1}],
        )
        created = asyncio.run(create_order(self.database, order_data))

        # Update status to CONTACTED
        updated = asyncio.run(
            update_order_status(self.database, created["id"], OrderStatus.CONTACTED.value)
        )
        self.assertEqual(updated["status"], OrderStatus.CONTACTED.value)

        # Assign manager
        assigned = asyncio.run(
            assign_order_manager(self.database, created["id"], "mgr_1")
        )
        self.assertEqual(assigned["assigned_manager_id"], "mgr_1")


if __name__ == "__main__":
    unittest.main()
