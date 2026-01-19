from fastapi import APIRouter, Depends, HTTPException, status, Query
from config.database import get_database
from schemas import OrderCreate, OrderResponse, OrderStatusUpdate, PaymentStatusUpdate
from middleware import get_current_user, get_current_admin
from utils.helpers import generate_order_number, calculate_tax, calculate_shipping
from datetime import datetime
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Create a new order"""
    user_id = str(current_user["_id"])
    
    # Calculate totals
    subtotal = sum(item.subtotal for item in order_data.items)
    tax = calculate_tax(subtotal)
    shipping_fee = calculate_shipping()
    total = subtotal + tax + shipping_fee
    
    # Create order
    order_dict = {
        "order_number": generate_order_number(),
        "user_id": user_id,
        "items": [item.dict() for item in order_data.items],
        "shipping_address": order_data.shipping_address.dict(),
        "subtotal": subtotal,
        "tax": tax,
        "shipping_fee": shipping_fee,
        "discount": 0.0,
        "total": total,
        "payment_method": order_data.payment_method,
        "payment_status": "pending",
        "order_status": "pending",
        "notes": order_data.notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.orders.insert_one(order_dict)
    order_dict["_id"] = str(result.inserted_id)
    
    # Update product stock
    for item in order_data.items:
        await db.products.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"stock_quantity": -item.quantity}}
        )
    
    # Clear cart
    await db.carts.update_one(
        {"user_id": user_id},
        {"$set": {"items": [], "updated_at": datetime.utcnow()}}
    )
    
    return OrderResponse(**order_dict)


@router.get("", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get user's orders"""
    user_id = str(current_user["_id"])
    
    cursor = db.orders.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)
    
    for order in orders:
        order["_id"] = str(order["_id"])
    
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get a single order"""
    user_id = str(current_user["_id"])
    
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    # Check ownership (unless admin)
    if order["user_id"] != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    order["_id"] = str(order["_id"])
    return OrderResponse(**order)


@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Update order status (Admin only)"""
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "order_status": status_update.order_status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    updated_order["_id"] = str(updated_order["_id"])
    
    return OrderResponse(**updated_order)


@router.put("/{order_id}/payment", response_model=OrderResponse)
async def update_payment_status(
    order_id: str,
    payment_update: PaymentStatusUpdate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Update payment status (Admin only)"""
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    await db.orders.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "payment_status": payment_update.payment_status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
    updated_order["_id"] = str(updated_order["_id"])
    
    return OrderResponse(**updated_order)
