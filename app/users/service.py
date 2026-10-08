import uuid
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.common.enums import UserRole
from app.users.auth import hash_password, verify_password
from app.users.schemas import (
    UserCreateStaffRequest,
    UserRegisterRequest,
    UserUpdateAdminRequest,
)


USERS_COLLECTION = "users"


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> dict | None:
    return await db[USERS_COLLECTION].find_one({"email": email.strip().lower()})


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> dict | None:
    user = await db[USERS_COLLECTION].find_one({"id": user_id})
    if user is None:
        try:
            user = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
        except (InvalidId, TypeError):
            user = None
    return user


async def create_user(
    db: AsyncIOMotorDatabase,
    user_data: UserRegisterRequest | UserCreateStaffRequest,
    role: UserRole = UserRole.CUSTOMER,
) -> dict:
    normalized_email = user_data.email.strip().lower()
    existing_user = await get_user_by_email(db, normalized_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed = hash_password(user_data.password)

    user_document = {
        "id": user_id,
        "email": normalized_email,
        "hashed_password": hashed,
        "name": user_data.name.strip(),
        "phone": user_data.phone.strip(),
        "role": role.value if hasattr(role, "value") else role,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }

    result = await db[USERS_COLLECTION].insert_one(user_document)
    user_document["_id"] = result.inserted_id
    return user_document


async def authenticate_user(
    db: AsyncIOMotorDatabase,
    email: str,
    password: str,
) -> dict:
    normalized_email = email.strip().lower()
    user = await get_user_by_email(db, normalized_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user


async def get_contact_managers(db: AsyncIOMotorDatabase) -> list[dict]:
    """
    Get active managers for customer contact and support.
    """
    cursor = db[USERS_COLLECTION].find(
        {"role": UserRole.MANAGER.value, "is_active": True}
    ).sort("name", 1)

    managers = await cursor.to_list(length=None)
    return [
        {
            "id": m["id"],
            "name": m["name"],
            "email": m["email"],
            "phone": m["phone"],
        }
        for m in managers
    ]


# =========================================================================
# ADMIN USER MANAGEMENT
# =========================================================================

async def get_all_users(
    db: AsyncIOMotorDatabase,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
) -> list[dict]:
    query = {}
    if role is not None:
        query["role"] = role.value if hasattr(role, "value") else role
    if is_active is not None:
        query["is_active"] = is_active

    cursor = db[USERS_COLLECTION].find(query).sort("created_at", -1)
    return await cursor.to_list(length=None)


async def update_user_by_admin(
    db: AsyncIOMotorDatabase,
    user_id: str,
    update_data: UserUpdateAdminRequest,
) -> dict:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    update_fields = {}
    if update_data.name is not None:
        update_fields["name"] = update_data.name.strip()
    if update_data.phone is not None:
        update_fields["phone"] = update_data.phone.strip()
    if update_data.role is not None:
        update_fields["role"] = update_data.role.value if hasattr(update_data.role, "value") else update_data.role
    if update_data.is_active is not None:
        update_fields["is_active"] = update_data.is_active

    if update_fields:
        filter_doc = {"_id": user["_id"]} if "_id" in user else {"id": user["id"]}
        await db[USERS_COLLECTION].update_one(filter_doc, {"$set": update_fields})
        user.update(update_fields)

    return user


async def delete_user_by_admin(
    db: AsyncIOMotorDatabase,
    user_id: str,
) -> dict:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{user_id}' not found",
        )

    filter_doc = {"_id": user["_id"]} if "_id" in user else {"id": user["id"]}
    await db[USERS_COLLECTION].delete_one(filter_doc)
    return {"message": f"User '{user_id}' deleted successfully"}


async def seed_default_users(db: AsyncIOMotorDatabase) -> None:
    """
    Ensure default admin and manager users exist for testing & management.
    """
    admin_email = "admin@svasya.ua"
    manager_email = "manager@svasya.ua"

    if not await get_user_by_email(db, admin_email):
        await db[USERS_COLLECTION].insert_one(
            {
                "id": "user_admin_default",
                "email": admin_email,
                "hashed_password": hash_password("Admin123!"),
                "name": "Головний Адміністратор",
                "phone": "+380501112233",
                "role": UserRole.ADMIN.value,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
        )
        print("Default admin created: admin@svasya.ua")

    if not await get_user_by_email(db, manager_email):
        await db[USERS_COLLECTION].insert_one(
            {
                "id": "user_manager_default",
                "email": manager_email,
                "hashed_password": hash_password("Manager123!"),
                "name": "Менеджер Олена (Служба підтримки)",
                "phone": "+380671234567",
                "role": UserRole.MANAGER.value,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }
        )
        print("Default manager created: manager@svasya.ua")
