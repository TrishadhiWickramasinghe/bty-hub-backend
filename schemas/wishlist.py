from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class WishlistItemResponse(BaseModel):
    product_id: str
    product_name: str
    product_price: float
    product_image: Optional[str] = None
    added_at: datetime


class WishlistResponse(BaseModel):
    user_id: str
    items: List[WishlistItemResponse] = []
    total_items: int = 0


class AddToWishlistRequest(BaseModel):
    product_id: str
