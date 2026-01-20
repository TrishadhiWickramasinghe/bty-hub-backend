from fastapi import APIRouter, Depends, HTTPException, status
from config.database import get_database
from schemas import CartResponse, AddToCartRequest, UpdateCartItemRequest
from middleware import get_current_user
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/cart", tags=["Cart"])


@router.get("", response_model=CartResponse)
async def get_cart(
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Get user's cart"""
    user_id = str(current_user["_id"])
    
    # Get cart
    cart = await db.carts.find_one({"user_id": user_id})
    
    if not cart:
        # Create empty cart
        cart = {
            "user_id": user_id,
            "items": [],
            "total_items": 0,
            "total_price": 0.0,
            "updated_at": datetime.utcnow()
        }
        await db.carts.insert_one(cart)
    
    # Populate product details
    cart_items = []
    total_items = 0
    total_price = 0.0
    
    for item in cart.get("items", []):
        try:
            product = await db.products.find_one({"_id": ObjectId(item["product_id"])})
            if product:
                subtotal = product["price"] * item["quantity"]
                cart_items.append({
                    "product_id": str(product["_id"]),
                    "product_name": product["name"],
                    "product_price": product["price"],
                    "product_image": product.get("images", [None])[0],
                    "quantity": item["quantity"],
                    "subtotal": subtotal
                })
                total_items += item["quantity"]
                total_price += subtotal
        except:
            continue
    
    return CartResponse(
        user_id=user_id,
        items=cart_items,
        total_items=total_items,
        total_price=total_price,
        updated_at=cart.get("updated_at", datetime.utcnow())
    )


@router.post("/add", response_model=CartResponse)
async def add_to_cart(
    request: AddToCartRequest,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Add item to cart"""
    user_id = str(current_user["_id"])
    
    # Verify product exists
    try:
        product = await db.products.find_one({"_id": ObjectId(request.product_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Check stock
    if product.get("stock_quantity", 0) < request.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
    
    # Get or create cart
    cart = await db.carts.find_one({"user_id": user_id})
    
    if not cart:
        cart = {
            "user_id": user_id,
            "items": [],
            "updated_at": datetime.utcnow()
        }
        await db.carts.insert_one(cart)
        cart = await db.carts.find_one({"user_id": user_id})
    
    # Check if product already in cart
    items = cart.get("items", [])
    product_found = False
    
    for item in items:
        if item["product_id"] == request.product_id:
            item["quantity"] += request.quantity
            product_found = True
            break
    
    if not product_found:
        items.append({
            "product_id": request.product_id,
            "quantity": request.quantity
        })
    
    # Update cart
    await db.carts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "items": items,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Return updated cart
    return await get_cart(db, current_user)


@router.put("/item/{product_id}", response_model=CartResponse)
async def update_cart_item(
    product_id: str,
    request: UpdateCartItemRequest,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Update cart item quantity"""
    user_id = str(current_user["_id"])
    
    cart = await db.carts.find_one({"user_id": user_id})
    
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    
    items = cart.get("items", [])
    
    if request.quantity == 0:
        # Remove item
        items = [item for item in items if item["product_id"] != product_id]
    else:
        # Update quantity
        item_found = False
        for item in items:
            if item["product_id"] == product_id:
                item["quantity"] = request.quantity
                item_found = True
                break
        
        if not item_found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not in cart")
    
    # Update cart
    await db.carts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "items": items,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return await get_cart(db, current_user)


@router.delete("/item/{product_id}", response_model=CartResponse)
async def remove_from_cart(
    product_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Remove item from cart"""
    user_id = str(current_user["_id"])
    
    cart = await db.carts.find_one({"user_id": user_id})
    
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    
    items = [item for item in cart.get("items", []) if item["product_id"] != product_id]
    
    await db.carts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "items": items,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return await get_cart(db, current_user)


@router.delete("/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Clear cart"""
    user_id = str(current_user["_id"])
    
    await db.carts.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "items": [],
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return None
