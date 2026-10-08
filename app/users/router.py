from fastapi import APIRouter, Depends, HTTPException, status

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
)
from app.users.service import (
    authenticate_user,
    create_user,
    get_contact_managers,
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


@router.post(
    "/users/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new staff member (Admin or Manager). Admin role only.",
)
async def create_staff(
    staff_data: UserCreateStaffRequest,
    db=Depends(get_db),
    _admin: dict = Depends(require_roles(UserRole.ADMIN)),
):
    return await create_user(db, staff_data, role=staff_data.role)
