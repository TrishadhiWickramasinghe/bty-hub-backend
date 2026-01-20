from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CartItemBase(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)


class CartItemResponse(CartItemBase):
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    subtotal: float


class CartResponse(BaseModel):
    user_id: str
    items: List[CartItemResponse] = []
    total_items: int = 0
    total_price: float = 0.0
    updated_at: datetime


class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, default=1)


class UpdateCartItemRequest(BaseModel):
    quantity: int = Field(ge=0)
