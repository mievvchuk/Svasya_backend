from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app import database
from app.common.enums import OrderStatus, UserRole
from app.orders.schemas import (
    OrderAssignManager,
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)
from app.orders.service import (
    assign_order_manager,
    create_order,
    get_order_by_id,
    get_orders,
    update_order_status,
)
from app.users.auth import (
    get_current_user,
    get_optional_current_user,
    require_roles,
)


router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)


def get_db():
    if database.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB is not connected",
        )
    return database.db


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new order (guest or authenticated customer)",
)
async def create_order_endpoint(
    order_data: OrderCreate,
    current_user: Optional[dict] = Depends(get_optional_current_user),
    db=Depends(get_db),
):
    user_id = current_user["id"] if current_user else None
    return await create_order(db, order_data, user_id=user_id)


@router.get(
    "",
    response_model=list[OrderResponse],
    summary="List orders (customers view own orders; managers/admins view all)",
)
async def list_orders(
    status_filter: Optional[OrderStatus] = Query(None, alias="status"),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    user_role = current_user.get("role")
    if user_role == UserRole.CUSTOMER.value:
        # Customers can only see their own orders
        return await get_orders(
            db,
            user_id=current_user["id"],
            status_filter=status_filter.value if status_filter else None,
        )

    # Managers and Admins can see all orders
    return await get_orders(
        db,
        user_id=None,
        status_filter=status_filter.value if status_filter else None,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get single order details by ID",
)
async def get_single_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    order = await get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' not found",
        )

    user_role = current_user.get("role")
    if user_role == UserRole.CUSTOMER.value and order.get("user_id") != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this order",
        )

    return order


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Update order status (Manager or Admin role)",
)
async def update_status_endpoint(
    order_id: str,
    update_data: OrderStatusUpdate,
    db=Depends(get_db),
    _manager: dict = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN)),
):
    return await update_order_status(db, order_id, update_data.status.value)


@router.patch(
    "/{order_id}/assign",
    response_model=OrderResponse,
    summary="Assign order to a manager for contact/processing (Manager or Admin role)",
)
async def assign_manager_endpoint(
    order_id: str,
    assign_data: OrderAssignManager,
    db=Depends(get_db),
    _manager: dict = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN)),
):
    return await assign_order_manager(db, order_id, assign_data.manager_id)