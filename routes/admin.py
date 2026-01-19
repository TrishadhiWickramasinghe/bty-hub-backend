from fastapi import APIRouter, Depends, HTTPException, status, Query
from config.database import get_database
from schemas import UserResponse, OrderResponse
from middleware import get_current_admin
from typing import List, Dict, Any
from datetime import datetime, timedelta
from bson import ObjectId

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_stats(
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Get dashboard statistics"""
    
    # Total users
    total_users = await db.users.count_documents({"role": "customer"})
    
    # Total products
    total_products = await db.products.count_documents({})
    
    # Total orders
    total_orders = await db.orders.count_documents({})
    
    # Total revenue
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    revenue_result = await db.orders.aggregate(pipeline).to_list(length=1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0.0
    
    # Recent orders (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_orders = await db.orders.count_documents({
        "created_at": {"$gte": seven_days_ago}
    })
    
    # Pending orders
    pending_orders = await db.orders.count_documents({
        "order_status": "pending"
    })
    
    # Low stock products (less than 10)
    low_stock = await db.products.count_documents({
        "stock_quantity": {"$lt": 10}
    })
    
    # Top selling products
    top_products_pipeline = [
        {"$unwind": "$items"},
        {
            "$group": {
                "_id": "$items.product_id",
                "total_sold": {"$sum": "$items.quantity"},
                "product_name": {"$first": "$items.product_name"}
            }
        },
        {"$sort": {"total_sold": -1}},
        {"$limit": 5}
    ]
    top_products = await db.orders.aggregate(top_products_pipeline).to_list(length=5)
    
    return {
        "total_users": total_users,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "recent_orders": recent_orders,
        "pending_orders": pending_orders,
        "low_stock_products": low_stock,
        "top_selling_products": top_products
    }


@router.get("/orders", response_model=List[OrderResponse])
async def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Get all orders (Admin only)"""
    query = {}
    if status:
        query["order_status"] = status
    
    cursor = db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit)
    orders = await cursor.to_list(length=limit)
    
    for order in orders:
        order["_id"] = str(order["_id"])
    
    return orders


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Get all users (Admin only)"""
    cursor = db.users.find({"role": "customer"}).sort("created_at", -1).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    
    for user in users:
        user["_id"] = str(user["_id"])
    
    return users


@router.put("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Toggle user active status (Admin only)"""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    new_status = not user.get("is_active", True)
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": new_status, "updated_at": datetime.utcnow()}}
    )
    
    return {"message": f"User {'activated' if new_status else 'deactivated'} successfully"}


@router.get("/sales/analytics")
async def get_sales_analytics(
    start_date: str = Query(None),
    end_date: str = Query(None),
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Get sales analytics (Admin only)"""
    
    # Build date filter
    date_filter = {}
    if start_date:
        date_filter["$gte"] = datetime.fromisoformat(start_date)
    if end_date:
        date_filter["$lte"] = datetime.fromisoformat(end_date)
    
    query = {}
    if date_filter:
        query["created_at"] = date_filter
    
    # Sales by day
    daily_sales_pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "total_sales": {"$sum": "$total"},
                "order_count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    daily_sales = await db.orders.aggregate(daily_sales_pipeline).to_list(length=100)
    
    # Sales by category
    category_sales_pipeline = [
        {"$match": query},
        {"$unwind": "$items"},
        {
            "$lookup": {
                "from": "products",
                "localField": "items.product_id",
                "foreignField": "_id",
                "as": "product"
            }
        },
        {"$unwind": "$product"},
        {
            "$lookup": {
                "from": "categories",
                "localField": "product.category_id",
                "foreignField": "_id",
                "as": "category"
            }
        },
        {"$unwind": "$category"},
        {
            "$group": {
                "_id": "$category.name",
                "total_sales": {"$sum": "$items.subtotal"},
                "quantity_sold": {"$sum": "$items.quantity"}
            }
        },
        {"$sort": {"total_sales": -1}}
    ]
    category_sales = await db.orders.aggregate(category_sales_pipeline).to_list(length=50)
    
    return {
        "daily_sales": daily_sales,
        "category_sales": category_sales
    }


@router.get("/reports/inventory")
async def get_inventory_report(
    db=Depends(get_database),
    current_user: dict = Depends(get_current_admin)
):
    """Get inventory report (Admin only)"""
    
    # Products by stock level
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$switch": {
                        "branches": [
                            {"case": {"$lte": ["$stock_quantity", 0]}, "then": "Out of Stock"},
                            {"case": {"$lte": ["$stock_quantity", 10]}, "then": "Low Stock"},
                            {"case": {"$lte": ["$stock_quantity", 50]}, "then": "Medium Stock"},
                        ],
                        "default": "High Stock"
                    }
                },
                "count": {"$sum": 1},
                "total_value": {"$sum": {"$multiply": ["$price", "$stock_quantity"]}}
            }
        }
    ]
    stock_levels = await db.products.aggregate(pipeline).to_list(length=10)
    
    # Products needing restock
    low_stock_products = await db.products.find({
        "stock_quantity": {"$lt": 10}
    }).to_list(length=50)
    
    for product in low_stock_products:
        product["_id"] = str(product["_id"])
    
    return {
        "stock_levels": stock_levels,
        "low_stock_products": low_stock_products
    }
