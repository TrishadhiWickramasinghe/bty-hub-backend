from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    CASH_ON_DELIVERY = "cod"


class ShippingAddress(BaseModel):
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str = "USA"


class OrderItem(BaseModel):
    product_id: str
    product_name: str
    product_image: Optional[str] = None
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)
    subtotal: float


class OrderCreate(BaseModel):
    shipping_address: ShippingAddress
    payment_method: PaymentMethod
    items: List[OrderItem]
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: str = Field(alias="_id")
    order_number: str
    user_id: str
    items: List[OrderItem]
    shipping_address: ShippingAddress
    subtotal: float
    tax: float = 0.0
    shipping_fee: float = 0.0
    discount: float = 0.0
    total: float
    payment_method: PaymentMethod
    payment_status: PaymentStatus = PaymentStatus.PENDING
    order_status: OrderStatus = OrderStatus.PENDING
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class OrderStatusUpdate(BaseModel):
    order_status: OrderStatus


class PaymentStatusUpdate(BaseModel):
    payment_status: PaymentStatus
