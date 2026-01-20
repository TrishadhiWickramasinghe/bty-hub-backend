from fastapi import APIRouter
from routes import auth, products, cart, orders, wishlist, admin, upload, reviews

api_router = APIRouter()

# Include all routes
api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(products.category_router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(wishlist.router)
api_router.include_router(reviews.router)
api_router.include_router(admin.router)
api_router.include_router(upload.router)
