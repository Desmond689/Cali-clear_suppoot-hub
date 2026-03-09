import json
from database.db import db
from database.models import Category, Product

def seed_data():
    # Load products from products.json
    with open('../data/products.json', 'r') as f:
        products_data = json.load(f)

    # Create categories
    categories = {}
    for product_data in products_data:
        category_name = product_data.get('category', 'General')
        if category_name not in categories:
            category = Category(name=category_name, description=f'{category_name} products')
            db.session.add(category)
            categories[category_name] = category

    db.session.commit()  # Commit to get IDs

    # Create products
    for product_data in products_data:
        category_name = product_data.get('category', 'General')
        category = categories[category_name]
        product = Product(
            original_id=product_data.get('id'),  # Store original ID from JSON
            name=product_data['name'],
            description=product_data.get('description', ''),
            price=product_data['price'],
            category_id=category.id,
            image_url=product_data.get('image', ''),
            stock=product_data.get('stock', 100),
            featured=product_data.get('bestSeller', False)
        )
        db.session.add(product)

    db.session.commit()
