# BTY-HUB Backend API

Modern FastAPI backend for BTY-HUB e-commerce platform.

## Features

- ✅ User Authentication & Authorization (JWT)
- ✅ Product Management (CRUD)
- ✅ Shopping Cart
- ✅ Order Management
- ✅ Wishlist
- ✅ Product Reviews & Ratings
- ✅ Admin Dashboard & Analytics
- ✅ File Upload (Product/Category Images)
- ✅ Category Management
- ✅ Sales Analytics & Reports
- ✅ Inventory Management

## Tech Stack

- **FastAPI** - Modern, fast web framework
- **MongoDB** - NoSQL database
- **Motor** - Async MongoDB driver
- **Pydantic** - Data validation
- **JWT** - Authentication
- **Bcrypt** - Password hashing

## Project Structure

```
bty-hub-backend/
├── config/
│   ├── __init__.py
│   ├── settings.py          # Application settings
│   └── database.py          # Database connection
├── schemas/
│   ├── __init__.py
│   ├── user.py              # User schemas
│   ├── product.py           # Product & category schemas
│   ├── cart.py              # Cart schemas
│   ├── order.py             # Order schemas
│   └── wishlist.py          # Wishlist schemas
├── routes/
│   ├── __init__.py
│   ├── auth.py              # Authentication routes
│   ├── products.py          # Product & category routes
│   ├── cart.py              # Shopping cart routes
│   ├── orders.py            # Order routes
│   ├── wishlist.py          # Wishlist routes
│   ├── reviews.py           # Review routes
│   ├── admin.py             # Admin routes
│   └── upload.py            # File upload routes
├── middleware/
│   ├── __init__.py
│   └── auth.py              # Authentication middleware
├── utils/
│   ├── __init__.py
│   ├── security.py          # Password & JWT utilities
│   └── helpers.py           # Helper functions
├── uploads/                 # Uploaded files directory
├── .env                     # Environment variables
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
├── main.py                 # Application entry point
└── README.md              # This file
```

## Installation

1. **Clone the repository**

```bash
cd bty-hub-backend
```

2. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Start MongoDB**

```bash
# Make sure MongoDB is running on localhost:27017
# Or update MONGODB_URL in .env
```

6. **Run the application**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token

### Products

- `GET /api/v1/products` - Get all products (with filters)
- `GET /api/v1/products/{id}` - Get product by ID
- `POST /api/v1/products` - Create product (Admin)
- `PUT /api/v1/products/{id}` - Update product (Admin)
- `DELETE /api/v1/products/{id}` - Delete product (Admin)

### Categories

- `GET /api/v1/categories` - Get all categories
- `POST /api/v1/categories` - Create category (Admin)

### Cart

- `GET /api/v1/cart` - Get user's cart
- `POST /api/v1/cart/add` - Add item to cart
- `PUT /api/v1/cart/item/{product_id}` - Update cart item
- `DELETE /api/v1/cart/item/{product_id}` - Remove from cart
- `DELETE /api/v1/cart/clear` - Clear cart

### Orders

- `POST /api/v1/orders` - Create order
- `GET /api/v1/orders` - Get user's orders
- `GET /api/v1/orders/{id}` - Get order by ID
- `PUT /api/v1/orders/{id}/status` - Update order status (Admin)
- `PUT /api/v1/orders/{id}/payment` - Update payment status (Admin)

### Wishlist

- `GET /api/v1/wishlist` - Get user's wishlist
- `POST /api/v1/wishlist/add` - Add to wishlist
- `DELETE /api/v1/wishlist/item/{product_id}` - Remove from wishlist

### Reviews

- `POST /api/v1/reviews` - Create review
- `GET /api/v1/reviews/product/{product_id}` - Get product reviews
- `DELETE /api/v1/reviews/{id}` - Delete review

### Admin

- `GET /api/v1/admin/dashboard` - Get dashboard statistics
- `GET /api/v1/admin/orders` - Get all orders
- `GET /api/v1/admin/users` - Get all users
- `PUT /api/v1/admin/users/{id}/toggle-status` - Toggle user status
- `GET /api/v1/admin/sales/analytics` - Get sales analytics
- `GET /api/v1/admin/reports/inventory` - Get inventory report

### Upload

- `POST /api/v1/upload/product-image` - Upload product image (Admin)
- `POST /api/v1/upload/category-image` - Upload category image (Admin)

## Environment Variables

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=bty_hub

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME=BTY-HUB API
DEBUG=True
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000"]

# Upload
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE=5242880
```

## Authentication

The API uses JWT Bearer token authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your_token_here>
```

## Creating an Admin User

To create an admin user, manually update a user in MongoDB:

```javascript
db.users.updateOne({ email: "admin@btyhub.com" }, { $set: { role: "admin" } });
```

## Development

```bash
# Run with auto-reload
uvicorn main:app --reload

# Run tests (if available)
pytest

# Format code
black .

# Lint code
flake8
```

## Production Deployment

1. **Set environment variables**
   - Use strong SECRET_KEY
   - Set DEBUG=False
   - Configure proper CORS_ORIGINS

2. **Use production ASGI server**

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

3. **Set up reverse proxy** (Nginx)

4. **Enable HTTPS**

5. **Monitor logs and performance**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Support

For issues and questions, please create an issue in the repository.

---

Built with ❤️ for BTY-HUB E-Commerce Platform
