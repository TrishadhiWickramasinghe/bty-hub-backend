from fastapi import APIRouter, Depends, HTTPException, status
from config.database import get_database
from schemas import ReviewCreate, ReviewResponse
from middleware import get_current_user
from datetime import datetime
from bson import ObjectId
from typing import List

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Create a product review"""
    user_id = str(current_user["_id"])
    
    # Verify product exists
    try:
        product = await db.products.find_one({"_id": ObjectId(review_data.product_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")
    
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    
    # Check if user already reviewed this product
    existing_review = await db.reviews.find_one({
        "user_id": user_id,
        "product_id": review_data.product_id
    })
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product"
        )
    
    # Create review
    review_dict = review_data.dict()
    review_dict["user_id"] = user_id
    review_dict["user_name"] = current_user.get("full_name", current_user.get("username"))
    review_dict["created_at"] = datetime.utcnow()
    
    result = await db.reviews.insert_one(review_dict)
    review_dict["_id"] = str(result.inserted_id)
    
    # Update product rating
    pipeline = [
        {"$match": {"product_id": review_data.product_id}},
        {"$group": {
            "_id": None,
            "avg_rating": {"$avg": "$rating"},
            "count": {"$sum": 1}
        }}
    ]
    stats = await db.reviews.aggregate(pipeline).to_list(length=1)
    
    if stats:
        await db.products.update_one(
            {"_id": ObjectId(review_data.product_id)},
            {
                "$set": {
                    "average_rating": round(stats[0]["avg_rating"], 1),
                    "review_count": stats[0]["count"]
                }
            }
        )
    
    return ReviewResponse(**review_dict)


@router.get("/product/{product_id}", response_model=List[ReviewResponse])
async def get_product_reviews(
    product_id: str,
    db=Depends(get_database)
):
    """Get all reviews for a product"""
    try:
        ObjectId(product_id)  # Validate ID format
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid product ID")
    
    cursor = db.reviews.find({"product_id": product_id}).sort("created_at", -1)
    reviews = await cursor.to_list(length=100)
    
    for review in reviews:
        review["_id"] = str(review["_id"])
    
    return reviews


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    db=Depends(get_database),
    current_user: dict = Depends(get_current_user)
):
    """Delete a review (owner or admin only)"""
    user_id = str(current_user["_id"])
    
    try:
        review = await db.reviews.find_one({"_id": ObjectId(review_id)})
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review ID")
    
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    
    # Check ownership
    if review["user_id"] != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    # Delete review
    product_id = review["product_id"]
    await db.reviews.delete_one({"_id": ObjectId(review_id)})
    
    # Update product rating
    pipeline = [
        {"$match": {"product_id": product_id}},
        {"$group": {
            "_id": None,
            "avg_rating": {"$avg": "$rating"},
            "count": {"$sum": 1}
        }}
    ]
    stats = await db.reviews.aggregate(pipeline).to_list(length=1)
    
    if stats:
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$set": {
                    "average_rating": round(stats[0]["avg_rating"], 1),
                    "review_count": stats[0]["count"]
                }
            }
        )
    else:
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"average_rating": 0.0, "review_count": 0}}
        )
    
    return None
