import asyncio
import unittest

from app import database
from app.common.enums import ProductCategory
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

    def test_search_products(self):
        # Match "cotton" in description
        res_match = asyncio.run(get_available_products(search="cotton"))
        self.assertEqual(len(res_match), 1)
        self.assertEqual(res_match[0]["id"], "product_tshirt_basic")

        # Non-matching keyword
        res_none = asyncio.run(get_available_products(search="jacket"))
        self.assertEqual(len(res_none), 0)

    def test_filter_category_and_price(self):
        # Match category tshirt
        res_cat = asyncio.run(get_available_products(category=ProductCategory.TSHIRT))
        self.assertEqual(len(res_cat), 1)

        # Match price range: min_price 20, max_price 30 (product is 24.99)
        res_price_ok = asyncio.run(get_available_products(min_price=20.0, max_price=30.0))
        self.assertEqual(len(res_price_ok), 1)

        # Filter out with price range: min_price 50
        res_price_high = asyncio.run(get_available_products(min_price=50.0))
        self.assertEqual(len(res_price_high), 0)

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
