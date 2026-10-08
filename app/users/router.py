from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import database
from app.common.enums import UserRole
from app.users.auth import create_access_token, get_current_user, require_roles
from app.users.schemas import (
    ManagerContactResponse,
    TokenResponse,
    UserCreateStaffRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateAdminRequest,
)
from app.users.service import (
    authenticate_user,
    create_user,
    delete_user_by_admin,
    get_all_users,
    get_contact_managers,
    update_user_by_admin,
)


router = APIRouter(
    prefix="/api",
    tags=["Auth & Users"],
)


def get_db():
    if database.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not connected",
        )
    return database.db


@router.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new customer account",
)
async def register(
    user_data: UserRegisterRequest,
    db=Depends(get_db),
):
    user = await create_user(db, user_data, role=UserRole.CUSTOMER)
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Login with email and password",
)
async def login(
    credentials: UserLoginRequest,
    db=Depends(get_db),
):
    user = await authenticate_user(db, credentials.email, credentials.password)
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current logged in user profile",
)
async def get_me(
    current_user: dict = Depends(get_current_user),
):
    return current_user


@router.get(
    "/users/managers",
    response_model=list[ManagerContactResponse],
    summary="Get contact managers for customer communication",
)
async def list_contact_managers(
    db=Depends(get_db),
):
    return await get_contact_managers(db)


# =========================================================================
# ADMIN USER MANAGEMENT
# =========================================================================

@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="[Admin] Get list of all users with optional filters",
)
async def list_all_users(
    role: Optional[UserRole] = Query(None, description="Filter by role: admin, manager, customer"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await get_all_users(db, role=role, is_active=is_active)


@router.post(
    "/users/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Create a new staff member (Admin or Manager)",
)
async def create_staff(
    staff_data: UserCreateStaffRequest,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await create_user(db, staff_data, role=staff_data.role)


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="[Admin] Update user role, active status, name, or phone",
)
async def update_user(
    user_id: str,
    update_data: UserUpdateAdminRequest,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await update_user_by_admin(db, user_id, update_data)


@router.delete(
    "/users/{user_id}",
    summary="[Admin] Delete a user account",
)
async def delete_user(
    user_id: str,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await delete_user_by_admin(db, user_id)
