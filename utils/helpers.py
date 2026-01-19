import re
from typing import Optional


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def generate_order_number() -> str:
    """Generate a unique order number"""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_num = random.randint(1000, 9999)
    return f"BTY{timestamp}{random_num}"


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:.2f}"


def calculate_tax(subtotal: float, tax_rate: float = 0.1) -> float:
    """Calculate tax amount"""
    return round(subtotal * tax_rate, 2)


def calculate_shipping(total_weight: float = 0) -> float:
    """Calculate shipping fee based on weight"""
    if total_weight == 0:
        return 10.0  # Flat rate
    elif total_weight < 5:
        return 10.0
    elif total_weight < 10:
        return 15.0
    else:
        return 20.0


def paginate_params(skip: int = 0, limit: int = 20) -> tuple:
    """Validate and return pagination parameters"""
    skip = max(0, skip)
    limit = min(max(1, limit), 100)  # Max 100 items per page
    return skip, limit
