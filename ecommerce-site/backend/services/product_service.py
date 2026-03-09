from database.models import Product
from database.db import db

def get_all_products():
    return Product.query.all()

def get_product_by_id(product_id):
    return Product.query.get(product_id)

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
