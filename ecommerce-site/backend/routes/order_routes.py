from flask import Blueprint, request, jsonify
from database.models import Order, OrderItem, Cart, Product, Message, PaymentMethod, AdminNotification
from utils.responses import success_response, error_response
from utils.helpers import generate_order_number, calculate_cart_total
from services.email_service import send_order_confirmation_email, send_shipping_update
from services.product_service import get_product_by_id
from database.db import db
from datetime import datetime
import json

order_bp = Blueprint('order', __name__)

@order_bp.route('/orders/<order_id>/tracking', methods=['GET'])
def get_order_tracking(order_id):
    """Return a small summary of an order for customer tracking page.

    The frontend expects a wrapped JSON ({status,message,data:{...}}), and the
    `data` object should contain the fields used by `tracking.html`.
    """
    email = request.args.get('email')
    if not email:
        return error_response('Email required'), 400

    order = Order.query.get(order_id)
    if not order or order.email != email:
        return error_response('Order not found'), 404

    result = {
        'order_number': order.id,
        'order_date': order.created_at.isoformat() if order.created_at else None,
        'status': order.status,
        'tracking_number': order.tracking_number,
        'carrier': order.carrier,
        'shipping_address': order.shipping_address,
        'customer_name': order.customer_name,
        'city': order.city,
        'zip_code': order.zip_code,
        'estimated_delivery': None,
        'shipping_method': None
    }
    return success_response(result), 200

@order_bp.route('/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')
    email = data.get('email')
    tracking_number = data.get('tracking_number')
    carrier = data.get('carrier')

    order = Order.query.get(order_id)
    if not order or order.email != email:
        return error_response('Order not found'), 404

    # Customers can only cancel orders — all other status changes require admin
    allowed_customer_statuses = {'cancelled'}
    if new_status not in allowed_customer_statuses:
        return error_response('Status change not allowed'), 403

    order.status = new_status
    db.session.commit()

    # Send update email
    try:
        send_shipping_update(order_id, email, new_status, tracking_number, carrier)
    except Exception as e:
        print(f'Warning: Could not send shipping update email: {e}')

    return success_response({'message': 'Order status updated'}), 200

@order_bp.route('/orders', methods=['GET'])
def get_orders():
    email = request.args.get('email')
    if not email:
        return error_response('Email required'), 400
    # Do not show payment-request-only orders until payment is verified (per user request)
    orders = Order.query.filter_by(email=email).filter(Order.status != 'payment_requested').order_by(Order.created_at.desc()).all()
    
    # Get item counts in bulk
    order_ids = [o.id for o in orders]
    item_counts = {}
    if order_ids:
        from sqlalchemy import func
        counts = db.session.query(
            OrderItem.order_id, func.count(OrderItem.id)
        ).filter(OrderItem.order_id.in_(order_ids)).group_by(OrderItem.order_id).all()
        item_counts = {oid: cnt for oid, cnt in counts}
    
    result = [{
        'id': o.id,
        'total': o.total,
        'status': o.status,
        'tracking_number': o.tracking_number,
        'carrier': o.carrier,
        'item_count': item_counts.get(o.id, 0),
        'created_at': o.created_at.isoformat()
    } for o in orders]
    return success_response(result), 200

@order_bp.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    order_items = OrderItem.query.filter_by(order_id=order_id).all()
    items = [{
        'product_id': i.product_id,
        'quantity': i.quantity,
        'price': i.price
    } for i in order_items]
    result = {
        'id': order.id,
        'email': order.email,
        'total': order.total,
        'status': order.status,
        'payment_status': order.payment_status,
        'shipping_address': order.shipping_address,
        'tracking_number': order.tracking_number,
        'carrier': order.carrier,
        'created_at': order.created_at.isoformat(),
        'items': items
    }
    return success_response(result), 200

@order_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    email = data.get('email')
    shipping_address = data.get('shipping_address')
    customer_name = data.get('customer_name', '')
    city = data.get('city', '')
    zip_code = data.get('zip_code', '')
    items = data.get('items', [])
    total = data.get('total', 0)
    payment_method_slug = data.get('payment_method', '')

    print(f"[ORDER] Received order request - email: {email}, items: {len(items) if items else 0}, total: {total}, payment_method: {payment_method_slug}")
    
    if not email or not shipping_address:
        print("[ORDER] Missing email or shipping address")
        return error_response('Email and shipping address required'), 400

    if not items:
        print("[ORDER] No items in cart")
        return error_response('Cart is empty'), 400

    # Look up payment method
    pm = None
    if payment_method_slug:
        pm = PaymentMethod.query.filter_by(slug=payment_method_slug, active=True).first()

    # Calculate total and check stock
    calculated_total = 0.0
    order_items = []
    for item in items:
        product = get_product_by_id(item.get('product_id') or item.get('id'))
        if not product or not product.active or product.stock < item.get('quantity', 1):
            return error_response(f'Product {item.get("product_id") or item.get("id")} unavailable'), 400
        qty = item.get('quantity', 1)
        price = item.get('price', product.price)
        calculated_total += price * qty
        order_items.append({
            'product_id': product.id,
            'quantity': qty,
            'price': price,
            'name': product.name
        })

    # Use provided total or calculate from items
    final_total = total if total > 0 else calculated_total

    # Create order
    order_number = generate_order_number()
    order = Order(
        id=order_number,
        email=email,
        total=final_total,
        shipping_address=shipping_address,
        customer_name=customer_name,
        city=city,
        zip_code=zip_code,
        payment_status='requested',
        status='payment_requested',
        payment_method_id=pm.id if pm else None,
        payment_method_name=pm.name if pm else payment_method_slug or 'Not Selected'
    )
    db.session.add(order)

    # Create order items
    for item in order_items:
        order_item = OrderItem(
            order_id=order_number,
            product_id=item['product_id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(order_item)

    # Do NOT decrement stock until payment verification
    db.session.commit()

    # === AUTO-CREATE CHAT MESSAGES ===
    # 1. Auto order message from customer
    items_text = ', '.join([f"{it['name']} x{it['quantity']}" for it in order_items])
    order_msg_text = (
        f"🛒 New Order\n"
        f"Products: {items_text}\n"
        f"Total: ${final_total:.2f}\n"
        f"Order ID: #{order_number}\n"
        f"Payment Method: {pm.name if pm else 'Not Selected'}"
    )
    order_message = Message(
        customer_email=email,
        customer_name=customer_name,
        message=order_msg_text,
        message_type='order',
        order_id=order_number,
        status='new'
    )
    db.session.add(order_message)
    db.session.commit()

    # 2. Bot auto-reply - acknowledgment
    bot_thanks = Message(
        customer_email=email,
        customer_name='Bot',
        message=(
            f"Thanks for your order 🙌\nOrder #{order_number} received.\n"
            "Our team will now prepare your payment details and send them in this chat shortly."
        ),
        message_type='bot',
        order_id=order_number,
        status='replied',
        admin_reply=None,
        replied_at=datetime.utcnow()
    )
    db.session.add(bot_thanks)
    db.session.commit()

    # 3. Post order status message (no automatic payment gateway details)
    order_status_msg = Message(
        customer_email=email,
        customer_name='Bot',
        message=(
            "Please wait while we assign your order to our payment team.\n"
            "You will receive payment instructions here in chat once a payment method is ready."
        ),
        message_type='status_update',
        order_id=order_number,
        status='replied',
        replied_at=datetime.utcnow()
    )
    db.session.add(order_status_msg)
    db.session.commit()
    
    # 4. Create admin notification for new order
    items_text = ', '.join([f"{it['name']} x{it['quantity']}" for it in order_items])
    admin_notif = AdminNotification(
        notification_type='new_order',
        title=f'New Order #{order_number}',
        body=(
            f"Customer: {customer_name or email}\n"
            f"Products: {items_text}\n"
            f"Total: ${final_total:.2f}\n"
            f"Payment: {pm.name if pm else 'Not Selected'}"
        ),
        order_id=order_number
    )
    db.session.add(admin_notif)
    db.session.commit()
    
    # Prepare order details for email
    order_details = {
        'order_id': order_number,
        'total': final_total,
        'status': order.status
    }

    # Send confirmation emails to customer and admin
    try:
        send_order_confirmation_email(
            order_id=order_number,
            customer_email=email,
            order_details=order_details,
            items=order_items,
            shipping_address=shipping_address,
            payment_method=pm.name if pm else payment_method_slug or 'Not Selected'
        )
    except Exception as e:
        print(f'Warning: Could not send order confirmation email: {e}')

    return success_response({
        'order_id': order_number,
        'message': 'Order created',
        'payment_method': pm.slug if pm else None,
        'payment_method_name': pm.name if pm else None
    }), 201

