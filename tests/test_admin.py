import asyncio
import unittest
from fastapi import HTTPException

from app.common.enums import ProductCategory, UserRole
from app.products.schemas import (
    ProductCreate,
    ProductUpdate,
    VariantCreate,
)
from app.products.service import (
    create_product,
    create_variant,
    delete_product,
    delete_variant,
    get_product_by_id,
    update_product,
    update_variant_stock,
)
from app.users.schemas import (
    UserRegisterRequest,
    UserUpdateAdminRequest,
)
from app.users.service import (
    create_user,
    delete_user_by_admin,
    get_all_users,
    update_user_by_admin,
)
from tests.test_orders import FakeDatabase


class AdminFeaturesTests(unittest.TestCase):
    def setUp(self):
        self.database = FakeDatabase()

    def test_admin_create_update_delete_product(self):
        # 1. Create product
        prod_data = ProductCreate(
            name="Нове Худі Оверсайз",
            description="Тепле оверсайз худі з принтом",
            category=ProductCategory.HOODIE,
            price=65.00,
            is_available=True,
        )
        created = asyncio.run(create_product(prod_data, db=self.database))
        self.assertIn("product_нове_худі_оверсайз", created["id"])
        self.assertEqual(created["price"], 65.0)

        # 2. Update product
        update_data = ProductUpdate(
            price=59.99,
            is_available=False,
        )
        updated = asyncio.run(update_product(created["id"], update_data, db=self.database))
        self.assertEqual(updated["price"], 59.99)
        self.assertFalse(updated["is_available"])

        # 3. Delete product
        del_res = asyncio.run(delete_product(created["id"], db=self.database))
        self.assertIn("deleted successfully", del_res["message"])

        # Check it is no longer found
        found = asyncio.run(get_product_by_id(created["id"], db=self.database))
        self.assertIsNone(found)

    def test_admin_manage_variants_and_stock(self):
        # 1. Add variant to basic tshirt
        variant_data = VariantCreate(
            color="red",
            size="L",
            image_url="https://example.com/red.png",
            stock=10,
        )
        new_variant = asyncio.run(
            create_variant("product_tshirt_basic", variant_data, db=self.database)
        )
        self.assertEqual(new_variant["color"], "red")
        self.assertEqual(new_variant["stock"], 10)

        # 2. Update stock: mode 'add' (+25 items arrived)
        stock_add_res = asyncio.run(
            update_variant_stock(new_variant["id"], stock_delta=25, mode="add", db=self.database)
        )
        self.assertEqual(stock_add_res["stock"], 35)

        # 3. Update stock: mode 'set' (inventory count set to exactly 50)
        stock_set_res = asyncio.run(
            update_variant_stock(new_variant["id"], stock_delta=50, mode="set", db=self.database)
        )
        self.assertEqual(stock_set_res["stock"], 50)

        # 4. Delete variant
        del_v = asyncio.run(delete_variant(new_variant["id"], db=self.database))
        self.assertIn("deleted successfully", del_v["message"])

    def test_admin_user_management(self):
        # 1. Register a test customer
        user_data = UserRegisterRequest(
            email="vasyl@example.com",
            password="Password123!",
            name="Василь",
            phone="+380990001122",
        )
        user = asyncio.run(create_user(self.database, user_data))

        # 2. List all users
        all_users = asyncio.run(get_all_users(self.database))
        self.assertGreaterEqual(len(all_users), 2)  # mgr_1 from mock + new vasyl

        # 3. Admin promotes user to MANAGER
        promote = UserUpdateAdminRequest(role=UserRole.MANAGER)
        updated_user = asyncio.run(
            update_user_by_admin(self.database, user["id"], promote)
        )
        self.assertEqual(updated_user["role"], UserRole.MANAGER.value)

        # 4. Admin deactivates user
        deactivate = UserUpdateAdminRequest(is_active=False)
        updated_user2 = asyncio.run(
            update_user_by_admin(self.database, user["id"], deactivate)
        )
        self.assertFalse(updated_user2["is_active"])

        # 5. Delete user
        del_user = asyncio.run(delete_user_by_admin(self.database, user["id"]))
        self.assertIn("deleted successfully", del_user["message"])


if __name__ == "__main__":
    unittest.main()
