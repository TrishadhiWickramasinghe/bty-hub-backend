from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None


class CategoryResponse(CategoryBase):
    id: str = Field(alias="_id")
    slug: str
    product_count: int = 0
    created_at: datetime
    
    class Config:
        populate_by_name = True


class ProductBase(BaseModel):
    name: str
    description: str
    price: float = Field(gt=0)
    category_id: str
    brand: Optional[str] = None
    sku: Optional[str] = None
    stock_quantity: int = Field(ge=0, default=0)
    images: List[str] = []
    tags: List[str] = []


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    category_id: Optional[str] = None
    brand: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: str = Field(alias="_id")
    slug: str
    average_rating: float = 0.0
    review_count: int = 0
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True


class ReviewBase(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    product_id: str


class ReviewResponse(ReviewBase):
    id: str = Field(alias="_id")
    user_id: str
    product_id: str
    user_name: str
    created_at: datetime
    
    class Config:
        populate_by_name = True
