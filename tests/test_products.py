import asyncio
import unittest

from app import database
from app.products.service import get_available_products, get_product_by_id
from tests.test_orders import FakeDatabase


class ProductsTests(unittest.TestCase):
    def setUp(self):
        self.fake_db = FakeDatabase()
        database.db = self.fake_db

    def tearDown(self):
        database.db = None

    def test_get_available_products(self):
        products = asyncio.run(get_available_products())
        # Only product_tshirt_basic should be returned as product_unavailable is is_available=False
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["id"], "product_tshirt_basic")
        self.assertEqual(products[0]["preview_image"], "https://example.com/tshirt.png")

    def test_get_product_by_id_includes_variants(self):
        product = asyncio.run(get_product_by_id("product_tshirt_basic"))
        self.assertIsNotNone(product)
        self.assertEqual(product["id"], "product_tshirt_basic")
        self.assertEqual(len(product["variants"]), 1)
        variant = product["variants"][0]
        self.assertEqual(variant["id"], "variant_tshirt_black_m")
        self.assertEqual(variant["product_id"], "product_tshirt_basic")
        self.assertEqual(variant["color"], "black")
        self.assertEqual(variant["stock"], 20)

    def test_get_product_by_id_not_found(self):
        product = asyncio.run(get_product_by_id("non_existent_id"))
        self.assertIsNone(product)


if __name__ == "__main__":
    unittest.main()
