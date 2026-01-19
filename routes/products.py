from fastapi import APIRouter, Depends, HTTPException, status, Query
from config.database import get_database
from schemas import ProductResponse, ProductCreate, ProductUpdate, CategoryResponse, CategoryCreate
from middleware import get_current_admin, optional_authentication
from utils.helpers import slugify, paginate_params
from datetime import datetime
from bson import ObjectId
from typing import List, Optional

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = Query("created_at", regex="^(name|price|created_at|rating)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db=Depends(get_database)
):
    """Get all products with filtering and pagination"""
    skip, limit = paginate_params(skip, limit)
    
    # Build query
    query = {"is_active": True}
    
    if category_id:
        query["category_id"] = category_id
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"tags": {"$in": [search]}}
        ]
    
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    
    # Sort
    sort_direction = 1 if sort_order == "asc" else -1
    
    # Get products
    cursor = db.products.find(query).sort(sort_by, sort_direction).skip(skip).limit(limit)
    products = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for product in products:
        product["_id"] = str(product["_id"])
    
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db=Depends(get_database)):
    """Get a single product by ID"""
    try:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    product["_id"] = str(product["_id"])
    return ProductResponse(**product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Create a new product (Admin only)"""
    # Verify category exists
    try:
        category = await db.categories.find_one({"_id": ObjectId(product_data.category_id)})
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category ID")
    
    # Create product
    product_dict = product_data.dict()
    product_dict["slug"] = slugify(product_data.name)
    product_dict["average_rating"] = 0.0
    product_dict["review_count"] = 0
    product_dict["is_active"] = True
    product_dict["created_at"] = datetime.utcnow()
    product_dict["updated_at"] = datetime.utcnow()
    
    result = await db.products.insert_one(product_dict)
    product_dict["_id"] = str(result.inserted_id)
    
    # Update category product count
    await db.categories.update_one(
        {"_id": ObjectId(product_data.category_id)},
        {"$inc": {"product_count": 1}}
    )
    
    return ProductResponse(**product_dict)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Update a product (Admin only)"""
    try:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Update data
    update_data = product_data.dict(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
        
        if "name" in update_data:
            update_data["slug"] = slugify(update_data["name"])
        
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
    
    # Get updated product
    updated_product = await db.products.find_one({"_id": ObjectId(product_id)})
    updated_product["_id"] = str(updated_product["_id"])
    
    return ProductResponse(**updated_product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Delete a product (Admin only)"""
    try:
        result = await db.products.delete_one({"_id": ObjectId(product_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    return None


# Category routes
category_router = APIRouter(prefix="/categories", tags=["Categories"])


@category_router.get("", response_model=List[CategoryResponse])
async def get_categories(db=Depends(get_database)):
    """Get all categories"""
    cursor = db.categories.find()
    categories = await cursor.to_list(length=100)
    
    for category in categories:
        category["_id"] = str(category["_id"])
    
    return categories


@category_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Create a new category (Admin only)"""
    category_dict = category_data.dict()
    category_dict["slug"] = slugify(category_data.name)
    category_dict["product_count"] = 0
    category_dict["created_at"] = datetime.utcnow()
    
    result = await db.categories.insert_one(category_dict)
    category_dict["_id"] = str(result.inserted_id)
    
    return CategoryResponse(**category_dict)
