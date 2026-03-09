from flask import Blueprint, request, jsonify
from database.models import Product, Category
from sqlalchemy import or_, and_
from utils.responses import success_response, error_response
import json
import os

product_bp = Blueprint('product', __name__)

# Path to products.json for fallback
PRODUCTS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'products.json')

def load_products_from_json():
    """Load products from products.json file"""
    try:
        with open(PRODUCTS_JSON_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def convert_json_product_to_api_format(product_data):
    """Convert JSON product format to API response format"""
    return {
        'id': product_data.get('id'),
        'original_id': product_data.get('id'),  # Include original ID for matching
        'name': product_data.get('name'),
        'price': product_data.get('price'),
        'image_url': product_data.get('image') or product_data.get('image_url'),
        'category_id': None,
        'stock': product_data.get('stock', 100),
        'featured': product_data.get('bestSeller', False),
        'description': product_data.get('description', ''),
        'rating': product_data.get('rating', 4)
    }

@product_bp.route('/products', methods=['GET'])
def get_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search = request.args.get('search', '')
    category_id = request.args.get('category_id')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    query = Product.query.filter_by(active=True)
    
    # If no products in database, use JSON fallback
    db_product_count = query.count()
    if db_product_count == 0:
        products_data = load_products_from_json()
        
        # Apply filters to JSON data
        if search:
            products_data = [p for p in products_data if search.lower() in p.get('name', '').lower() or search.lower() in p.get('description', '').lower()]
        
        if category_id:
            products_data = [p for p in products_data if p.get('category_id') == int(category_id)]
        
        if min_price:
            products_data = [p for p in products_data if p.get('price', 0) >= float(min_price)]
        
        if max_price:
            products_data = [p for p in products_data if p.get('price', 0) <= float(max_price)]
        
        # Sort
        if sort_by == 'price':
            products_data.sort(key=lambda p: p.get('price', 0), reverse=(sort_order == 'desc'))
        elif sort_by == 'name':
            products_data.sort(key=lambda p: p.get('name', ''), reverse=(sort_order == 'desc'))
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_products = products_data[start:end]
        
        result = {
            'products': [convert_json_product_to_api_format(p) for p in paginated_products],
            'total': len(products_data),
            'pages': (len(products_data) + per_page - 1) // per_page,
            'current_page': page
        }
        return success_response(result), 200
    
    # Use database queries
    if search:
        query = query.filter(or_(Product.name.ilike(f'%{search}%'), Product.description.ilike(f'%{search}%')))

    if category_id:
        query = query.filter_by(category_id=category_id)

    if min_price:
        query = query.filter(Product.price >= float(min_price))

    if max_price:
        query = query.filter(Product.price <= float(max_price))

    if sort_by == 'price':
        query = query.order_by(Product.price.asc() if sort_order == 'asc' else Product.price.desc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc() if sort_order == 'asc' else Product.name.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    products = query.paginate(page=page, per_page=per_page, error_out=False)

    result = {
        'products': [{
            'id': p.id,
            'original_id': p.original_id,
            'name': p.name,
            'price': p.price,
            'image_url': p.image_url,
            'category_id': p.category_id,
            'stock': p.stock,
            'featured': p.featured
        } for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': products.page
    }
    return success_response(result), 200

@product_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    if product and product.active:
        category = Category.query.get(product.category_id)
        return success_response({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'category': category.name if category else None,
            'image_url': product.image_url,
            'stock': product.stock,
            'featured': product.featured
        })
    
    # Fallback to JSON
    products_data = load_products_from_json()
    product_data = next((p for p in products_data if p.get('id') == id), None)
    if product_data:
        return success_response(convert_json_product_to_api_format(product_data))
    
    return error_response('Product not found')

@product_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    if categories:
        result = [{'id': c.id, 'name': c.name, 'description': c.description} for c in categories]
        return success_response(result), 200
    
    # Fallback: extract categories from JSON
    products_data = load_products_from_json()
    category_names = set(p.get('category', 'General') for p in products_data)
    result = [{'name': name, 'description': f'{name} products'} for name in category_names]
    return success_response(result), 200

@product_bp.route('/featured', methods=['GET'])
def get_featured_products():
    products = Product.query.filter_by(featured=True, active=True).limit(10).all()
    
    if products:
        result = [{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'image_url': p.image_url
        } for p in products]
        return success_response(result), 200
    
    # Fallback to JSON
    products_data = load_products_from_json()
    featured = [p for p in products_data if p.get('bestSeller', False)][:10]
    result = [convert_json_product_to_api_format(p) for p in featured]
    return success_response(result), 200
