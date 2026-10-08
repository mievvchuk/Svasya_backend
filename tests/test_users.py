import asyncio
import unittest
from fastapi import HTTPException

from app.common.enums import UserRole
from app.users.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.users.schemas import UserRegisterRequest
from app.users.service import (
    authenticate_user,
    create_user,
    get_contact_managers,
    seed_default_users,
)
from tests.test_orders import FakeCollection, FakeDatabase


class UsersTests(unittest.TestCase):
    def setUp(self):
        self.database = FakeDatabase()

    def test_password_hashing(self):
        raw = "SecretPassword123"
        hashed = hash_password(raw)
        self.assertNotEqual(raw, hashed)
        self.assertTrue(verify_password(raw, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_jwt_token_flow(self):
        data = {"sub": "user_42", "role": "admin"}
        token = create_access_token(data)
        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "user_42")
        self.assertEqual(decoded["role"], "admin")

    def test_register_and_authenticate(self):
        user_data = UserRegisterRequest(
            email="ivan@example.com",
            password="Password123!",
            name="Іван Іваненко",
            phone="+380509998877",
        )
        created = asyncio.run(create_user(self.database, user_data))
        self.assertEqual(created["email"], "ivan@example.com")
        self.assertEqual(created["role"], UserRole.CUSTOMER.value)

        # Authenticate successfully
        auth_user = asyncio.run(
            authenticate_user(self.database, "ivan@example.com", "Password123!")
        )
        self.assertEqual(auth_user["id"], created["id"])

        # Authenticate with wrong password
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(authenticate_user(self.database, "ivan@example.com", "WrongPassword"))
        self.assertEqual(ctx.exception.status_code, 401)

        # Duplicate email
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(create_user(self.database, user_data))
        self.assertEqual(ctx.exception.status_code, 400)

    def test_seed_and_get_contact_managers(self):
        asyncio.run(seed_default_users(self.database))

        managers = asyncio.run(get_contact_managers(self.database))
        self.assertGreaterEqual(len(managers), 1)
        self.assertTrue(any(m["email"] == "manager@svasya.ua" for m in managers))


if __name__ == "__main__":
    unittest.main()
