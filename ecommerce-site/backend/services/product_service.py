from database.models import Product
from database.db import db
import json
import os

PRODUCTS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'products.json')

def load_products_from_json():
    try:
        with open(PRODUCTS_JSON_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def get_all_products():
    return Product.query.all()

def get_product_by_id(product_id):
    # Try database first
    product = Product.query.get(product_id)
    if product:
        return product
    
    # Fallback to JSON
    products_data = load_products_from_json()
    for p in products_data:
        if p.get('id') == product_id:
            class JSONProduct:
                def __init__(self, data):
                    self.id = data.get('id')
                    self.name = data.get('name', 'Unknown')
                    self.price = data.get('price', 0)
                    self.stock = data.get('stock', 100)
                    self.active = True
                    self.description = data.get('description', '')
                    self.image_url = data.get('image', '')
            return JSONProduct(p)
    return None

def add_product(name, description, price, category, image_url=None):
    product = Product(name=name, description=description, price=price, category=category, image_url=image_url)
    db.session.add(product)
    db.session.commit()
    return product

def update_product(product_id, **kwargs):
    product = Product.query.get(product_id)
    if product:
        for key, value in kwargs.items():
            setattr(product, key, value)
        db.session.commit()
        return product
    return None

def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return True
    return False