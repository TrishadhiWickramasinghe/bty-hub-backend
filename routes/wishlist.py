from fastapi import APIRouter, Depends, HTTPException, status
from config.database import get_database
from schemas import WishlistResponse, AddToWishlistRequest
from middleware import get_current_user
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/wishlist", tags=["Wishlist"])


@router.get("", response_model=WishlistResponse)
async def get_wishlist(
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get user's wishlist"""
    user_id = str(current_user["_id"])
    
    wishlist = await db.wishlists.find_one({"user_id": user_id})
    
    if not wishlist:
        # Create empty wishlist
        wishlist = {
            "user_id": user_id,
            "items": []
        }
        await db.wishlists.insert_one(wishlist)
    
    # Populate product details
    wishlist_items = []
    
    for item in wishlist.get("items", []):
        try:
            product = await db.products.find_one({"_id": ObjectId(item["product_id"])})
            if product:
                wishlist_items.append({
                    "product_id": str(product["_id"]),
                    "product_name": product["name"],
                    "product_price": product["price"],
                    "product_image": product.get("images", [None])[0],
                    "added_at": item.get("added_at", datetime.utcnow())
                })
        except:
            continue
    
    return WishlistResponse(
        user_id=user_id,
        items=wishlist_items,
        total_items=len(wishlist_items)
    )


@router.post("/add", response_model=WishlistResponse)
async def add_to_wishlist(
    request: AddToWishlistRequest,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Add item to wishlist"""
    user_id = str(current_user["_id"])
    
    # Verify product exists
    try:
        product = await db.products.find_one({"_id": ObjectId(request.product_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Get or create wishlist
    wishlist = await db.wishlists.find_one({"user_id": user_id})
    
    if not wishlist:
        wishlist = {
            "user_id": user_id,
            "items": []
        }
        await db.wishlists.insert_one(wishlist)
        wishlist = await db.wishlists.find_one({"user_id": user_id})
    
    # Check if product already in wishlist
    items = wishlist.get("items", [])
    product_exists = any(item["product_id"] == request.product_id for item in items)
    
    if not product_exists:
        items.append({
            "product_id": request.product_id,
            "added_at": datetime.utcnow()
        })
        
        await db.wishlists.update_one(
            {"user_id": user_id},
            {"$set": {"items": items}}
        )
    
    return await get_wishlist(db, current_user)


@router.delete("/item/{product_id}", response_model=WishlistResponse)
async def remove_from_wishlist(
    product_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Remove item from wishlist"""
    user_id = str(current_user["_id"])
    
    wishlist = await db.wishlists.find_one({"user_id": user_id})
    
    if not wishlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    
    items = [item for item in wishlist.get("items", []) if item["product_id"] != product_id]
    
    await db.wishlists.update_one(
        {"user_id": user_id},
        {"$set": {"items": items}}
    )
    
    return await get_wishlist(db, current_user)
