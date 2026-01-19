from fastapi import APIRouter, Depends, HTTPException, status, Query
from config.database import get_database
from schemas import ProductResponse, ProductCreate, ProductUpdate, CategoryResponse, CategoryCreate
from middleware import get_current_admin, optional_authentication
from utils.helpers import slugify
from utils.pagination import PaginationParams, SortParams, FilterParams, PaginatedResponse
from datetime import datetime
from bson import ObjectId
from typing import List, Optional

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=dict)
async def get_products(
    pagination: PaginationParams = Depends(),
    sort: SortParams = Depends(),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search in name, description, tags"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    rating_min: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    db=Depends(get_database)
):
    """Get all products with advanced pagination, filtering, and sorting"""
    
    # Build query
    query = {"is_active": True}
    
    # Category filter
    if category_id:
        query["category_id"] = category_id
    
    # Search filter
    if search:
        query.update(FilterParams.build_search_query(search, ["name", "description", "tags"]))
    
    # Price range filter
    if min_price is not None or max_price is not None:
        query.update(FilterParams.build_range_query(min_price, max_price, "price"))
    
    # Stock filter
    if in_stock is not None:
        if in_stock:
            query["stock_quantity"] = {"$gt": 0}
        else:
            query["stock_quantity"] = {"$lte": 0}
    
    # Rating filter
    if rating_min is not None:
        query["average_rating"] = {"$gte": rating_min}
    
    # Get total count
    total = await db.products.count_documents(query)
    
    # Get sorted products with pagination
    sort_field, sort_direction = sort.to_tuple()
    cursor = db.products.find(query).sort(sort_field, sort_direction).skip(pagination.skip).limit(pagination.limit)
    products = await cursor.to_list(length=pagination.limit)
    
    # Convert ObjectId to string
    for product in products:
        product["_id"] = str(product["_id"])
    
    paginated = PaginatedResponse(products, total, pagination.skip, pagination.limit)
    return paginated.to_dict()


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


@category_router.get("", response_model=dict)
async def get_categories(
    pagination: PaginationParams = Depends(),
    sort: SortParams = Depends(),
    search: Optional[str] = Query(None, description="Search in category name"),
    db=Depends(get_database)
):
    """Get all categories with pagination, filtering, and sorting"""
    query = {}
    
    if search:
        query.update(FilterParams.build_search_query(search, ["name"]))
    
    total = await db.categories.count_documents(query)
    
    sort_field, sort_direction = sort.to_tuple()
    cursor = db.categories.find(query).sort(sort_field, sort_direction).skip(pagination.skip).limit(pagination.limit)
    categories = await cursor.to_list(length=pagination.limit)
    
    for category in categories:
        category["_id"] = str(category["_id"])
    
    paginated = PaginatedResponse(categories, total, pagination.skip, pagination.limit)
    return paginated.to_dict()


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
