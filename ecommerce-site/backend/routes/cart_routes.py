from flask import Blueprint, request, jsonify
from database.models import Cart, Product
from database.db import db
from utils.responses import success_response, error_response
from utils.helpers import generate_cart_id
import json
import os

cart_bp = Blueprint('cart', __name__)

# Path to products.json for fallback
PRODUCTS_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'products.json')

def load_products_from_json():
    """Load products from products.json file"""
    try:
        with open(PRODUCTS_JSON_PATH, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def get_product_from_db_or_json(product_id):
    """Get product from database, fallback to JSON"""
    product = Product.query.get(product_id)
    if product:
        return product
    
    # Fallback to JSON
    products_data = load_products_from_json()
    product_data = next((p for p in products_data if p.get('id') == product_id), None)
    if product_data:
        return type('Product', (), {
            'id': product_data.get('id'),
            'name': product_data.get('name'),
            'price': product_data.get('price', 0),
            'image_url': product_data.get('image') or product_data.get('image_url', ''),
            'stock': product_data.get('stock', 100),
            'active': True
        })()
    
    return None

def get_cart_id():
    cart_id = request.cookies.get('cart_id')
    if not cart_id:
        cart_id = generate_cart_id()
    return cart_id

@cart_bp.route('/cart', methods=['GET'])
def get_cart():
    cart_id = get_cart_id()
    print(f'[CART DEBUG] get_cart called, cart_id: {cart_id}')
    cart_items = Cart.query.filter_by(id=cart_id).all()
    print(f'[CART DEBUG] Found {len(cart_items)} items in cart')
    result = []
    for item in cart_items:
        product = get_product_from_db_or_json(item.product_id)
        if product and product.active and product.stock >= item.quantity:
            # Get the original_id from products.json for frontend matching
            original_id = getattr(product, 'original_id', None) or item.product_id
            result.append({
                'product_id': item.product_id,
                'original_id': original_id,  # Include original ID for matching with products.json
                'name': product.name,
                'price': product.price,
                'quantity': item.quantity,
                'image_url': product.image_url
            })
    print(f'[CART DEBUG] Returning {len(result)} items')
    response = success_response(result)
    response.set_cookie('cart_id', cart_id, httponly=True, max_age=30*24*3600)
    return response, 200

@cart_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    cart_id = get_cart_id()
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1)
    
    print(f'[CART DEBUG] add_to_cart called, cart_id: {cart_id}, product_id: {product_id}, quantity: {quantity}')

    product = get_product_from_db_or_json(product_id)
    if not product or not product.active:
        print(f'[CART DEBUG] Product not found or inactive: {product_id}')
        return error_response('Product not found or inactive'), 404

    if product.stock < quantity:
        return error_response('Insufficient stock'), 400

    cart_item = Cart.query.filter_by(id=cart_id, product_id=product_id).first()
    if cart_item:
        if product.stock < cart_item.quantity + quantity:
            return error_response('Insufficient stock'), 400
        cart_item.quantity += quantity
        print(f'[CART DEBUG] Updated existing cart item, new quantity: {cart_item.quantity}')
    else:
        cart_item = Cart(id=cart_id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
        print(f'[CART DEBUG] Added new cart item')
    db.session.commit()
    response = success_response({'message': 'Added to cart'})
    response.set_cookie('cart_id', cart_id, httponly=True, max_age=30*24*3600)
    return response, 201

@cart_bp.route('/cart/update', methods=['PUT'])
def update_cart():
    cart_id = get_cart_id()
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 0)

    cart_item = Cart.query.filter_by(id=cart_id, product_id=product_id).first()
    if not cart_item:
        return error_response('Item not in cart'), 404

    product = get_product_from_db_or_json(product_id)
    if quantity > 0:
        if product.stock < quantity:
            return error_response('Insufficient stock'), 400
        cart_item.quantity = quantity
    else:
        db.session.delete(cart_item)
    db.session.commit()
    response = success_response({'message': 'Cart updated'})
    response.set_cookie('cart_id', cart_id, httponly=True, max_age=30*24*3600)
    return response, 200

@cart_bp.route('/cart/remove', methods=['DELETE'])
def remove_from_cart():
    cart_id = get_cart_id()
    data = request.get_json()
    product_id = data.get('product_id')

    cart_item = Cart.query.filter_by(id=cart_id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        response = success_response({'message': 'Removed from cart'})
        response.set_cookie('cart_id', cart_id, httponly=True, max_age=30*24*3600)
        return response, 200
    return error_response('Item not in cart'), 404

@cart_bp.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    """Clear all items from the cart"""
    cart_id = get_cart_id()
    print(f'[CART DEBUG] clear_cart called, cart_id: {cart_id}')
    Cart.query.filter_by(id=cart_id).delete()
    db.session.commit()
    response = success_response({'message': 'Cart cleared'})
    response.set_cookie('cart_id', cart_id, httponly=True, max_age=30*24*3600)
    return response, 200
