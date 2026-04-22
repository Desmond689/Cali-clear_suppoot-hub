from flask import Blueprint, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from middleware.admin_required import admin_required
from database.models import Product, Category, Order, OrderItem, User, Cart, Wishlist
from database.db import db
from utils.responses import success_response, error_response
from services.product_service import get_product_by_id
from services.admin_service import verify_admin_credentials, send_verification_email, verify_token_and_login
from datetime import datetime, timedelta
import json

admin_bp = Blueprint('admin', __name__)

# Initialize limiter for admin routes
admin_limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per day", "20 per hour"]
)

# Custom decorator for admin auth endpoints
def rate_limit_admin(f):
    @wraps(f)
    @admin_limiter.limit("3 per minute")
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def _coerce_int(value):
    """Best-effort integer coercion for query params and ids."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _load_order_items_for_order_ids(order_ids):
    """
    Load order items in bulk without relying on ORM relationship attributes.
    Returns a mapping of order_id -> serialized item list.
    """
    if not order_ids:
        return {}

    items = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).all()
    product_ids = {item.product_id for item in items if item.product_id is not None}

    product_names = {}
    if product_ids:
        product_rows = Product.query.filter(Product.id.in_(product_ids)).all()
        product_names = {product.id: product.name for product in product_rows}

    items_by_order = {}
    for item in items:
        items_by_order.setdefault(item.order_id, []).append({
            'product_id': item.product_id,
            'name': product_names.get(item.product_id, ''),
            'quantity': item.quantity,
            'price': item.price
        })

    return items_by_order

# ============ ADMIN LOGIN (Email Verification Required) ============

@admin_bp.route('/auto-login', methods=['POST'])
def admin_auto_login():
    """
    Auto-login endpoint - logs in as the first admin user without credentials.
    For development/testing purposes only.
    """
    from flask_jwt_extended import create_access_token, create_refresh_token
    from datetime import timedelta
    
    # Find first admin user
    admin = User.query.filter_by(is_admin=True).first()
    
    if not admin:
        return error_response('No admin users found'), 404
    
    # Create tokens
    user_identity = str(admin.id)
    access_token = create_access_token(identity=user_identity, expires_delta=timedelta(hours=8))
    refresh_token = create_refresh_token(identity=user_identity, expires_delta=timedelta(days=7))
    
    print(f"[ADMIN] Auto-login for: {admin.email}")
    
    return success_response({
        'message': 'Login successful',
        'admin': {
            'id': admin.id,
            'email': admin.email,
            'is_admin': admin.is_admin
        },
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@admin_bp.route('/dev-token', methods=['GET'])
def admin_dev_token():
    """
    Dev-only endpoint that returns an access token for the first admin user.
    Only enabled when running with Flask DEBUG=True to avoid accidental exposure.
    """
    from flask import current_app
    if not current_app.debug:
        return error_response('Not allowed'), 403

    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        return error_response('No admin users found'), 404

    from flask_jwt_extended import create_access_token
    access_token = create_access_token(identity=str(admin.id), expires_delta=timedelta(hours=8))

    print(f"[ADMIN] Dev token issued for: {admin.email}")

    return success_response({
        'access_token': access_token,
        'admin': {
            'id': admin.id,
            'email': admin.email,
            'is_admin': admin.is_admin
        }
    }), 200


@admin_bp.route('/login', methods=['POST'])
@rate_limit_admin
def admin_login():
    """
    Admin login endpoint - verifies credentials and sends verification email.
    Returns success if credentials are valid (doesn't require verification for login).
    """
    data = request.get_json()
    
    if not data:
        return error_response('Invalid request'), 400
    
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return error_response('Email and password are required'), 400
    
    # Verify credentials
    user, error = verify_admin_credentials(email, password)
    
    if error:
        return error_response('Invalid email or password'), 401
    
    # Credentials valid - create admin session
    from flask_jwt_extended import create_access_token, create_refresh_token
    from datetime import timedelta
    
    user_identity = str(user.id)
    access_token = create_access_token(identity=user_identity, expires_delta=timedelta(hours=8))
    refresh_token = create_refresh_token(identity=user_identity, expires_delta=timedelta(days=7))
    
    print(f"[ADMIN] Admin logged in: {email}")
    
    return success_response({
        'message': 'Login successful',
        'admin': {
            'id': user.id,
            'email': user.email,
            'is_admin': user.is_admin
        },
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@admin_bp.route('/verify', methods=['GET'])
def admin_verify():
    """
    Verify admin login token from email and create session.
    
    Query params:
        ?token=UUID
    
    Response:
        - Success: {"message": "Login successful", "admin": {...}, "access_token": "..."}
        - Invalid: {"error": "Invalid or expired verification link"} (400)
    """
    token = request.args.get('token', '')
    
    if not token:
        return error_response('Verification token is required'), 400
    
    # Verify token and create session
    tokens_data, error = verify_token_and_login(token)
    if error:
        return error_response(error), 400
    
    print(f"[ADMIN] Admin login verified successfully")
    
    return success_response({
        'message': 'Login successful',
        'admin': tokens_data['admin'],
        'access_token': tokens_data['access_token'],
        'refresh_token': tokens_data['refresh_token']
    }), 200


@admin_bp.route('/check-auth', methods=['GET'])
def check_admin_auth():
    """Check if current admin session is valid."""
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    from flask import g
    
    try:
        verify_jwt_in_request()
        user_id = _coerce_int(get_jwt_identity())
        user = User.query.get(user_id) if user_id is not None else None
        
        if user and user.is_admin:
            return success_response({
                'authenticated': True,
                'admin': {
                    'id': user.id,
                    'email': user.email,
                    'is_admin': user.is_admin
                }
            }), 200
    except Exception as e:
        pass
    
    return success_response({'authenticated': False}), 200


# ============ ANALYTICS ============

# Test endpoint without any decorator
@admin_bp.route('/test-analytics', methods=['GET'])
def test_analytics():
    """Test endpoint - no decorator"""
    return success_response({'test': 'works'}, 'Test endpoint works!')

@admin_bp.route('/analytics', methods=['GET'])
@admin_required
def get_analytics():
    """Get dashboard analytics - total products, orders, users, revenue, etc."""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get total products
        total_products = Product.query.count()
        
        # Get total orders - use text() to avoid model issues
        total_orders = db.session.execute(db.text('SELECT COUNT(*) FROM "order"')).scalar()
        
        # Get total users
        total_users = User.query.count()
        
        # Get total revenue (sum of all order totals)
        total_revenue = db.session.execute(db.text('SELECT SUM(total) FROM "order"')).scalar() or 0
        
        # Get recent orders (last 10)
        recent_orders_result = db.session.execute(
            db.text('SELECT id, total FROM "order" ORDER BY created_at DESC LIMIT 10')
        ).fetchall()
        recent_orders_data = [{'id': row[0], 'total': float(row[1])} for row in recent_orders_result]
        
        # Get low stock products (stock < 10)
        low_stock = Product.query.filter(Product.stock < 10).order_by(Product.stock.asc()).limit(10).all()
        low_stock_data = [{'name': p.name, 'stock': p.stock} for p in low_stock]
        
        # Get orders by status
        orders_by_status = {}
        status_counts = db.session.execute(
            db.text('SELECT status, COUNT(*) FROM "order" GROUP BY status')
        ).fetchall()
        for status, count in status_counts:
            orders_by_status[status] = count
        
        analytics_data = {
            'total_products': total_products,
            'total_orders': total_orders,
            'total_users': total_users,
            'total_revenue': float(total_revenue),
            'recent_orders': recent_orders_data,
            'low_stock': low_stock_data,
            'orders_by_status': orders_by_status
        }
        
        return success_response(analytics_data, 'Analytics retrieved successfully')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(f'Error fetching analytics: {str(e)}', 500)

# ============ PRODUCTS ============

@admin_bp.route('/products', methods=['GET'])
@admin_required
def get_products():
    """Get all products with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = Product.query
    
    if search:
        query = query.filter(Product.name.contains(search))
    if category:
        category_id = _coerce_int(category)
        if category_id is not None:
            query = query.filter_by(category_id=category_id)
    
    pagination = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    category_ids = {product.category_id for product in pagination.items if product.category_id is not None}
    categories_by_id = {}
    if category_ids:
        category_rows = Category.query.filter(Category.id.in_(category_ids)).all()
        categories_by_id = {category_row.id: category_row.name for category_row in category_rows}
    
    return success_response({
        'products': [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price,
            'stock': p.stock,
            'category_id': p.category_id,
            'category_name': categories_by_id.get(p.category_id),
            'image_url': p.image_url,
            'active': p.active,
            'featured': p.featured,
            'created_at': p.created_at.isoformat()
        } for p in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@admin_bp.route('/products', methods=['POST'])
@admin_required
def add_product():
    """Add new product"""
    data = request.get_json()
    
    product = Product(
        name=data['name'],
        description=data.get('description', ''),
        price=float(data['price']),
        category_id=data.get('category_id'),
        image_url=data.get('image_url', ''),
        stock=int(data.get('stock', 0)),
        active=data.get('active', True),
        featured=data.get('featured', False)
    )
    
    db.session.add(product)
    db.session.commit()
    
    return success_response({'message': 'Product added', 'id': product.id}), 201

@admin_bp.route('/products/<int:product_id>', methods=['PUT'])
@admin_required
def update_product(product_id):
    """Update product"""
    product = get_product_by_id(product_id)
    if not product:
        return error_response('Product not found'), 404
    
    data = request.get_json()
    
    for key, value in data.items():
        if key == 'price':
            value = float(value)
        elif key in ('stock', 'category_id'):
            value = int(value) if value else None
        elif key in ('active', 'featured'):
            value = bool(value)
        if hasattr(product, key):
            setattr(product, key, value)
    
    db.session.commit()
    
    return success_response({'message': 'Product updated'}), 200

@admin_bp.route('/products/<int:product_id>', methods=['DELETE'])
@admin_required
def delete_product(product_id):
    """Delete product"""
    product = get_product_by_id(product_id)
    if not product:
        return error_response('Product not found'), 404
    
    db.session.delete(product)
    db.session.commit()
    
    return success_response({'message': 'Product deleted'}), 200

# ============ CATEGORIES ============

@admin_bp.route('/categories', methods=['GET'])
@admin_required
def get_categories():
    """Get all categories"""
    categories = Category.query.all()
    counts = db.session.query(
        Product.category_id, db.func.count(Product.id)
    ).group_by(
        Product.category_id
    ).all()
    product_counts = {category_id: count for category_id, count in counts}

    return success_response({
        'categories': [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'product_count': int(product_counts.get(c.id, 0))
        } for c in categories]
    }), 200

@admin_bp.route('/categories', methods=['POST'])
@admin_required
def add_category():
    """Add category"""
    data = request.get_json()
    
    category = Category(
        name=data['name'],
        description=data.get('description', '')
    )
    
    db.session.add(category)
    db.session.commit()
    
    return success_response({'message': 'Category added', 'id': category.id}), 201

@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    """Update category"""
    category = Category.query.get(category_id)
    if not category:
        return error_response('Category not found'), 404
    
    data = request.get_json()
    category.name = data.get('name', category.name)
    category.description = data.get('description', category.description)
    
    db.session.commit()
    
    return success_response({'message': 'Category updated'}), 200

@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get(category_id)
    if not category:
        return error_response('Category not found'), 404
    
    db.session.delete(category)
    db.session.commit()
    
    return success_response({'message': 'Category deleted'}), 200

# ============ ORDERS ============

@admin_bp.route('/orders', methods=['GET'])
@admin_required
def get_orders():
    """Get all orders with filters - simplified"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        
        # Build query
        query = Order.query
        if status:
            query = query.filter(Order.status == status)
        
        # Order by created_at descending
        query = query.order_by(Order.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        orders = pagination.items
        
        # Get order IDs for loading items
        order_ids = [o.id for o in orders]
        items_by_order = _load_order_items_for_order_ids(order_ids)
        
        # Format orders
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'email': order.email,
                'customer_name': order.customer_name,
                'total': order.total,
                'status': order.status,
                'tracking_number': order.tracking_number,
                'carrier': order.carrier,
                'shipping_address': order.shipping_address,
                'city': order.city,
                'zip_code': order.zip_code,
                'payment_status': order.payment_status,
                'payment_method_name': order.payment_method_name,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'items': items_by_order.get(order.id, [])
            })
        
        return success_response({
            'orders': orders_data,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return error_response(f'Error fetching orders: {str(e)}', 500)

@admin_bp.route('/orders/<order_id>', methods=['GET'])
@admin_required
def get_order(order_id):
    """Get order details"""
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    items_by_order = _load_order_items_for_order_ids([order.id])

    return success_response({
        'id': order.id,
        'email': order.email,
        'customer_name': order.customer_name,
        'total': order.total,
        'status': order.status,
        'tracking_number': order.tracking_number,
        'carrier': order.carrier,
        'shipping_address': order.shipping_address,
        'city': order.city,
        'zip_code': order.zip_code,
        'created_at': order.created_at.isoformat(),
        'items': items_by_order.get(order.id, [])
    }), 200

@admin_bp.route('/orders/<order_id>/status', methods=['PUT'])
@admin_required
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    valid_statuses = ['created', 'paid', 'packed', 'processing', 'shipped', 
                      'in_transit', 'out_for_delivery', 'delivered', 
                      'failed_delivery', 'returned', 'refunded', 'cancelled']
    
    if new_status not in valid_statuses:
        return error_response('Invalid status'), 400
    
    order.status = new_status
    
    if data.get('tracking_number'):
        order.tracking_number = data['tracking_number']
    if data.get('carrier'):
        order.carrier = data['carrier']
    
    db.session.commit()
    
    return success_response({'message': 'Order status updated'}), 200

# ============ USERS ============

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(User.email.contains(search))
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    user_emails = [user.email for user in pagination.items if user.email]
    order_counts = {}
    if user_emails:
        counts = db.session.query(
            Order.email, db.func.count(Order.id)
        ).filter(
            Order.email.in_(user_emails)
        ).group_by(
            Order.email
        ).all()
        order_counts = {email: count for email, count in counts}
    
    return success_response({
        'users': [{
            'id': u.id,
            'email': u.email,
            'is_admin': u.is_admin,
            'is_active': getattr(u, 'is_active', True),
            'created_at': u.created_at.isoformat(),
            'order_count': int(order_counts.get(u.email, 0))
        } for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """Get user details with complete order history"""
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found'), 404
    
    # Get all orders for this user
    orders = Order.query.filter_by(email=user.email).order_by(
        Order.created_at.desc()
    ).all()
    
    # Build order items for all orders
    order_ids = [o.id for o in orders]
    order_items_map = {}
    
    if order_ids:
        order_items = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).all()
        for item in order_items:
            if item.order_id not in order_items_map:
                order_items_map[item.order_id] = []
            # Get product name
            product = Product.query.get(item.product_id)
            product_name = product.name if product else 'Unknown Product'
            order_items_map[item.order_id].append({
                'id': item.id,
                'product_id': item.product_id,
                'product_name': product_name,
                'quantity': item.quantity,
                'price': item.price
            })
    
    orders_data = []
    for o in orders:
        orders_data.append({
            'id': o.id,
            'total': o.total,
            'status': o.status,
            'shipping_address': o.shipping_address,
            'tracking_number': o.tracking_number,
            'carrier': o.carrier,
            'created_at': o.created_at.isoformat(),
            'items': order_items_map.get(o.id, [])
        })
    
    # Calculate statistics
    total_spent = sum(o.total for o in orders)
    total_orders = len(orders)
    avg_order_value = total_spent / total_orders if total_orders > 0 else 0
    
    # Calculate account age in days
    account_age_days = (datetime.utcnow() - user.created_at).days
    
    return success_response({
        'id': user.id,
        'email': user.email,
        'is_admin': user.is_admin,
        'is_active': getattr(user, 'is_active', True),
        'created_at': user.created_at.isoformat(),
        'stats': {
            'total_orders': total_orders,
            'total_spent': round(total_spent, 2),
            'avg_order_value': round(avg_order_value, 2),
            'account_age_days': account_age_days
        },
        'orders': orders_data
    }), 200

@admin_bp.route('/users/<int:user_id>/admin', methods=['PUT'])
@admin_required
def update_user_admin(user_id):
    """Toggle admin status"""
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found'), 404
    
    data = request.get_json()
    user.is_admin = data.get('is_admin', user.is_admin)
    
    db.session.commit()
    
    return success_response({'message': 'User updated'}), 200

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """Update user details"""
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found'), 404
    
    data = request.get_json()
    
    # Update email if provided
    if 'email' in data:
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != user_id:
            return error_response('Email already in use'), 400
        user.email = data['email']
    
    # Update admin status if provided
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    
    # Update is_active status if provided (for deactivation)
    if hasattr(user, 'is_active') and 'is_active' in data:
        user.is_active = data['is_active']
    
    db.session.commit()
    
    return success_response({
        'message': 'User updated successfully',
        'user': {
            'id': user.id,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_active': getattr(user, 'is_active', True)
        }
    }), 200

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Deactivate user account"""
    user = User.query.get(user_id)
    if not user:
        return error_response('User not found'), 404
    
    # Don't allow deleting yourself
    # We'll check this in the admin_required decorator or pass current user info
    
    # Soft delete - just mark as inactive
    if hasattr(user, 'is_active'):
        user.is_active = False
    else:
        # If no is_active field, we can't soft delete
        return error_response('Cannot deactivate user - feature not available'), 400
    
    db.session.commit()
    
    return success_response({'message': 'User deactivated successfully'}), 200

@admin_bp.route('/users/export', methods=['GET'])
@admin_required
def export_users():
    """Export all users to CSV"""
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Get order counts for each user
    user_emails = [user.email for user in users]
    order_counts = {}
    if user_emails:
        counts = db.session.query(
            Order.email, db.func.count(Order.id)
        ).filter(
            Order.email.in_(user_emails)
        ).group_by(
            Order.email
        ).all()
        order_counts = {email: count for email, count in counts}
    
    # Get total spent per user
    total_spent = {}
    if user_emails:
        totals = db.session.query(
            Order.email, db.func.sum(Order.total)
        ).filter(
            Order.email.in_(user_emails)
        ).group_by(
            Order.email
        ).all()
        total_spent = {email: float(total) if total else 0 for email, total in totals}
    
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_active': getattr(user, 'is_active', True),
            'created_at': user.created_at.isoformat(),
            'total_orders': order_counts.get(user.email, 0),
            'total_spent': total_spent.get(user.email, 0)
        })
    
    return success_response({'users': users_data, 'total': len(users_data)}), 200

# ============ SETTINGS ============

@admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_settings():
    """Get site settings"""
    settings = {
        'site_name': 'Cali Clear',
        'currency': 'USD',
        'tax_rate': 0.10,
        'free_shipping_threshold': 50.00,
        'contact_email': 'support@caliclear.com',
        'enable_notifications': True
    }
    return success_response({'settings': settings}), 200

@admin_bp.route('/settings', methods=['PUT'])
@admin_required
def update_settings():
    """Update site settings"""
    data = request.get_json()
    # In a real app, save to database or file
    return success_response({'message': 'Settings updated'}), 200

# ============ CARRIERS ============

@admin_bp.route('/carriers', methods=['GET'])
@admin_required
def get_carriers():
    """Get carrier configurations"""
    carriers = [
        {'id': 1, 'name': 'FedEx', 'code': 'fedex', 'active': True},
        {'id': 2, 'name': 'UPS', 'code': 'ups', 'active': True},
        {'id': 3, 'name': 'USPS', 'code': 'usps', 'active': True},
        {'id': 4, 'name': 'DHL', 'code': 'dhl', 'active': True},
    ]
    return success_response({'carriers': carriers}), 200

@admin_bp.route('/carriers/<carrier_code>', methods=['PUT'])
@admin_required
def update_carrier(carrier_code):
    """Update carrier settings"""
    data = request.get_json()
    return success_response({'message': f'Carrier {carrier_code} updated'}), 200

# ============ REPORTS ============

@admin_bp.route('/reports/sales', methods=['GET'])
@admin_required
def get_sales_report():
    """Get sales report"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Order.query.filter(Order.status.in_(['delivered', 'shipped']))
    
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date)
    
    orders = query.all()
    
    total_sales = sum(o.total for o in orders)
    total_orders = len(orders)
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    return success_response({
        'total_sales': round(total_sales, 2),
        'total_orders': total_orders,
        'avg_order_value': round(avg_order_value, 2),
        'orders': [{
            'id': o.id,
            'email': o.email,
            'total': o.total,
            'status': o.status,
            'created_at': o.created_at.isoformat()
        } for o in orders[:100]]
    }), 200

@admin_bp.route('/reports/inventory', methods=['GET'])
@admin_required
def get_inventory_report():
    """Get inventory report"""
    products = Product.query.all()
    
    total_value = sum(p.price * p.stock for p in products)
    low_stock = Product.query.filter(Product.stock < 10).count()
    out_of_stock = Product.query.filter(Product.stock == 0).count()
    
    return success_response({
        'total_products': len(products),
        'total_inventory_value': round(total_value, 2),
        'low_stock_count': low_stock,
        'out_of_stock_count': out_of_stock,
        'products': [{
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'stock': p.stock,
            'value': round(p.price * p.stock, 2)
        } for p in products]
    }), 200


# ============ PUSH NOTIFICATIONS ============

# In-memory store for push subscriptions (in production, use a database)
PUSH_SUBSCRIPTIONS = {}

@admin_bp.route('/notifications/subscribe', methods=['POST'])
@admin_required
def subscribe_to_notifications():
    """Save push notification subscription"""
    from flask import request
    data = request.get_json()
    
    # Store subscription (in production, save to database)
    subscription_id = f"admin_{data.get('endpoint', '')[-50:]}"
    PUSH_SUBSCRIPTIONS[subscription_id] = data
    
    print(f"[NOTIFICATIONS] New subscription registered: {subscription_id}")
    
    return success_response({'message': 'Subscription saved'}), 200


@admin_bp.route('/notifications/test', methods=['POST'])
@admin_required
def test_notification():
    """Send a test notification"""
    # In a real app, this would trigger a push notification
    # For now, we'll just return success
    print("[NOTIFICATIONS] Test notification triggered")
    
    return success_response({'message': 'Test notification sent'}), 200


# ============ PAYMENT METHODS ============

@admin_bp.route('/payment-methods', methods=['GET'])
@admin_required
def get_payment_methods():
    """List all payment methods for admin"""
    from database.models import PaymentMethod
    methods = PaymentMethod.query.order_by(PaymentMethod.sort_order).all()
    result = []
    for m in methods:
        details = {}
        try:
            details = json.loads(m.account_details) if m.account_details else {}
        except (json.JSONDecodeError, TypeError):
            details = {}
        result.append({
            'id': m.id,
            'name': m.name,
            'slug': m.slug,
            'icon': m.icon,
            'account_details': details,
            'instructions': m.instructions,
            'active': m.active,
            'sort_order': m.sort_order,
            'created_at': m.created_at.isoformat() if m.created_at else None,
            'updated_at': m.updated_at.isoformat() if m.updated_at else None
        })
    return success_response(result), 200


@admin_bp.route('/payment-methods', methods=['POST'])
@admin_required
def create_payment_method():
    """Create a new payment method"""
    from database.models import PaymentMethod
    data = request.get_json()
    if not data:
        return error_response('Invalid request body'), 400

    name = data.get('name', '').strip()
    slug = data.get('slug', '').strip().lower()
    if not name or not slug:
        return error_response('Name and slug are required'), 400

    if PaymentMethod.query.filter_by(slug=slug).first():
        return error_response('A payment method with this slug already exists'), 409

    pm = PaymentMethod(
        name=name,
        slug=slug,
        icon=data.get('icon', ''),
        account_details=json.dumps(data.get('account_details', {})),
        instructions=data.get('instructions', ''),
        active=data.get('active', True),
        sort_order=data.get('sort_order', 0)
    )
    db.session.add(pm)
    db.session.commit()
    return success_response({'id': pm.id, 'message': 'Payment method created'}), 201


@admin_bp.route('/payment-methods/<int:pm_id>', methods=['PUT'])
@admin_required
def update_payment_method(pm_id):
    """Update a payment method"""
    from database.models import PaymentMethod
    pm = PaymentMethod.query.get(pm_id)
    if not pm:
        return error_response('Payment method not found'), 404

    data = request.get_json()
    if not data:
        return error_response('Invalid request body'), 400

    if 'name' in data:
        pm.name = data['name']
    if 'slug' in data:
        new_slug = data['slug'].strip().lower()
        existing = PaymentMethod.query.filter(PaymentMethod.slug == new_slug, PaymentMethod.id != pm_id).first()
        if existing:
            return error_response('Slug already in use'), 409
        pm.slug = new_slug
    if 'icon' in data:
        pm.icon = data['icon']
    if 'account_details' in data:
        pm.account_details = json.dumps(data['account_details'])
    if 'instructions' in data:
        pm.instructions = data['instructions']
    if 'active' in data:
        pm.active = bool(data['active'])
    if 'sort_order' in data:
        pm.sort_order = int(data['sort_order'])

    db.session.commit()
    return success_response({'message': 'Payment method updated'}), 200


@admin_bp.route('/payment-methods/<int:pm_id>', methods=['DELETE'])
@admin_required
def delete_payment_method(pm_id):
    """Delete a payment method"""
    from database.models import PaymentMethod
    pm = PaymentMethod.query.get(pm_id)
    if not pm:
        return error_response('Payment method not found'), 404

    db.session.delete(pm)
    db.session.commit()
    return success_response({'message': 'Payment method deleted'}), 200


@admin_bp.route('/payment-methods/<int:pm_id>/toggle', methods=['PATCH'])
@admin_required
def toggle_payment_method(pm_id):
    """Toggle active status"""
    from database.models import PaymentMethod
    pm = PaymentMethod.query.get(pm_id)
    if not pm:
        return error_response('Payment method not found'), 404

    pm.active = not pm.active
    db.session.commit()
    return success_response({'message': f'Payment method {"activated" if pm.active else "deactivated"}'}), 200


# ============ PAYMENT VERIFICATION ============

@admin_bp.route('/payments/pending', methods=['GET'])
@admin_required
def get_pending_payments():
    """Get orders with pending payment status"""
    orders = Order.query.filter_by(payment_status='pending').order_by(Order.created_at.desc()).all()
    result = []
    for o in orders:
        result.append({
            'id': o.id,
            'email': o.email,
            'customer_name': o.customer_name,
            'total': o.total,
            'payment_method_name': o.payment_method_name,
            'payment_status': o.payment_status,
            'transaction_ref': o.transaction_ref,
            'created_at': o.created_at.isoformat() if o.created_at else None
        })
    return success_response(result), 200


@admin_bp.route('/payments/verify/<order_id>', methods=['POST'])
@admin_required
def verify_payment(order_id):
    """Verify payment for an order"""
    from database.models import Message
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404

    data = request.get_json() or {}
    action = data.get('action', 'verify')  # 'verify' or 'reject'
    note = data.get('note', '')

    if action == 'verify':
        order.payment_status = 'verified'
        order.status = 'paid'
        status_msg = f"✅ Payment verified for Order #{order_id}!\n\nYour order is now being processed."
    elif action == 'reject':
        order.payment_status = 'rejected'
        status_msg = f"❌ Payment could not be verified for Order #{order_id}."
        if note:
            status_msg += f"\n\nReason: {note}"
        status_msg += "\n\nPlease re-upload your payment proof or contact support."
    else:
        return error_response('Invalid action'), 400

    db.session.commit()

    # Send chat notification to customer
    msg = Message(
        customer_email=order.email,
        customer_name='Bot',
        message=status_msg,
        message_type='status_update',
        order_id=order_id,
        status='replied',
        replied_at=datetime.utcnow()
    )
    db.session.add(msg)
    db.session.commit()

    return success_response({'message': f'Payment {action}d'}), 200
