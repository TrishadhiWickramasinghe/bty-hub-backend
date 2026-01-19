from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import settings, Database
from routes import api_router
from pathlib import Path
import os

app = FastAPI(
    title=settings.APP_NAME,
    description="Modern E-Commerce Platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
upload_dir = Path(settings.UPLOAD_DIR)
upload_dir.mkdir(exist_ok=True)

# Mount static files
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/static", StaticFiles(directory=settings.UPLOAD_DIR), name="static")


@app.on_event("startup")
async def startup_db_client():
    """Connect to MongoDB on startup"""
    await Database.connect_db()
    print("✅ Application started successfully")


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    await Database.close_db()
    print("👋 Application shutting down")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to BTY-HUB API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }


# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI!"}