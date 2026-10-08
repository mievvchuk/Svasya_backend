import unittest
from types import SimpleNamespace

from app.orders.schemas import OrderCreate
from app.orders.service import create_order


class FakeCollection:
    def __init__(self, documents):
        self.documents = documents

    async def find_one(self, query):
        key, value = next(iter(query.items()))

        for document in self.documents:
            if document.get(key) == value:
                return document

        return None

    async def insert_one(self, document):
        self.documents.append(document)
        return SimpleNamespace(inserted_id="order-1")


class FakeDatabase:
    def __init__(self):
        self.collections = {
            "products": FakeCollection(
                [
                    {
                        "id": "product_tshirt_basic",
                        "name": "Basic T-Shirt",
                        "price": 24.99,
                        "is_available": True,
                    }
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
                    }
                ]
            ),
            "orders": FakeCollection([]),
        }

    def __getitem__(self, collection_name):
        return self.collections[collection_name]


def run_immediate(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value

    raise AssertionError("Test coroutine unexpectedly suspended")


class CreateOrderTests(unittest.TestCase):
    def test_create_order_uses_separate_variant_collection(self):
        database = FakeDatabase()
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

        result = run_immediate(create_order(database, order_data))

        self.assertEqual(result["id"], "order-1")
        self.assertEqual(result["total_price"], 49.98)
        self.assertEqual(
            result["items"],
            [
                {
                    "product_id": "product_tshirt_basic",
                    "variant_id": "variant_tshirt_black_m",
                    "name": "Basic T-Shirt",
                    "color": "black",
                    "size": "M",
                    "quantity": 2,
                    "price": 24.99,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
