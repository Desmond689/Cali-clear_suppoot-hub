import uuid
from datetime import datetime

def generate_cart_id():
    return str(uuid.uuid4())

def generate_order_number():
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def calculate_cart_total(cart_items):
    total = 0.0
    for item in cart_items:
        total += item['price'] * item['quantity']
    return total

def validate_email_format(email):
    # Simple validation, can use validators module
    return '@' in email and '.' in email
