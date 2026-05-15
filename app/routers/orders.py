from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..dependencies import require_auth
from ..models.order import Order
from ..models.user import User
from ..schemas.order import OrderCreate, OrderUpdate, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Order",
    operation_id="create_order",
)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    _: Optional[User] = Depends(require_auth),
):
    order = Order(**payload.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.post(
    "/batch",
    response_model=List[OrderResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Batch Create Orders",
    operation_id="batch_create_orders",
)
def batch_create_orders(
    payload: List[OrderCreate],
    db: Session = Depends(get_db),
    _: Optional[User] = Depends(require_auth),
):
    if not payload:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch must not be empty")
    if len(payload) > 100:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Batch size cannot exceed 100")
    orders = [Order(**item.model_dump()) for item in payload]
    db.add_all(orders)
    db.commit()
    for order in orders:
        db.refresh(order)
    return orders


@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List Orders",
    operation_id="list_orders",
)
def list_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: Optional[User] = Depends(require_auth),
):
    if limit > 500:
        limit = 500
    return db.query(Order).offset(skip).limit(limit).all()


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get Order by ID",
    operation_id="get_order",
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: Optional[User] = Depends(require_auth),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.put(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Update Order",
    operation_id="update_order",
)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    _: Optional[User] = Depends(require_auth),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(order, field, value)
    db.commit()
    db.refresh(order)
    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Order",
    operation_id="delete_order",
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    _: Optional[User] = Depends(require_auth),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    db.delete(order)
    db.commit()
