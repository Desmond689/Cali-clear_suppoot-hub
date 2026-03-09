from flask import Blueprint, request, jsonify
from database.models import Wishlist, Product
from database.db import db
from utils.responses import success_response, error_response
from utils.helpers import generate_cart_id
from services.product_service import get_product_by_id

wishlist_bp = Blueprint('wishlist', __name__)

def get_wishlist_id():
    wishlist_id = request.cookies.get('wishlist_id')
    if not wishlist_id:
        wishlist_id = generate_cart_id()  # Reuse generate_cart_id for simplicity
    return wishlist_id

@wishlist_bp.route('/wishlist', methods=['GET'])
def get_wishlist():
    wishlist_id = get_wishlist_id()
    wishlist_items = Wishlist.query.filter_by(id=wishlist_id).all()
    result = []
    for item in wishlist_items:
        product = get_product_by_id(item.product_id)
        if product and product.active:
            result.append({
                'product_id': item.product_id,
                'name': product.name,
                'price': product.price,
                'image_url': product.image_url
            })
    response = success_response(result)
    response.set_cookie('wishlist_id', wishlist_id, httponly=True, max_age=30*24*3600)  # 30 days
    return response, 200

@wishlist_bp.route('/wishlist/add', methods=['POST'])
def add_to_wishlist():
    wishlist_id = get_wishlist_id()
    data = request.get_json()
    product_id = data.get('product_id')

    product = get_product_by_id(product_id)
    if not product or not product.active:
        return error_response('Product not found or inactive'), 404

    wishlist_item = Wishlist.query.filter_by(id=wishlist_id, product_id=product_id).first()
    if not wishlist_item:
        wishlist_item = Wishlist(id=wishlist_id, product_id=product_id)
        db.session.add(wishlist_item)
        db.session.commit()
        response = success_response({'message': 'Added to wishlist'})
        response.set_cookie('wishlist_id', wishlist_id, httponly=True, max_age=30*24*3600)
        return response, 201
    response = success_response({'message': 'Already in wishlist'})
    response.set_cookie('wishlist_id', wishlist_id, httponly=True, max_age=30*24*3600)
    return response, 200

@wishlist_bp.route('/wishlist/remove', methods=['DELETE'])
def remove_from_wishlist():
    wishlist_id = get_wishlist_id()
    data = request.get_json()
    product_id = data.get('product_id')

    wishlist_item = Wishlist.query.filter_by(id=wishlist_id, product_id=product_id).first()
    if wishlist_item:
        db.session.delete(wishlist_item)
        db.session.commit()
        response = success_response({'message': 'Removed from wishlist'})
        response.set_cookie('wishlist_id', wishlist_id, httponly=True, max_age=30*24*3600)
        return response, 200
    response = error_response('Not in wishlist')
    response.set_cookie('wishlist_id', wishlist_id, httponly=True, max_age=30*24*3600)
    return response, 404
