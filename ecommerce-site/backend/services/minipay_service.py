#!/usr/bin/env python3
'''MiniPay Service - QR generation, deadline management'''

try:
    import qrcode
except ImportError:
    qrcode = None
import base64
from io import BytesIO
from datetime import datetime, timedelta
import os
from database.models import Order
from database.db import db

MINIPAY_PHONE = os.getenv('MINIPAY_PHONE', '+1234567890')  # Default demo phone

def generate_order_qr(order_id, amount, customer_name):
    '''Generate MiniPay QR code with order details.'''
    # QR data format: minipay://pay?phone=MINIPAY_PHONE&amount=AMOUNT&ref=ORDER_ID&note=CUSTOMER_NAME
    qr_data = f'minipay://pay?phone={MINIPAY_PHONE}&amount={amount:.2f}&ref={order_id}&note={customer_name[:30]}'
    
    if qrcode is None:
        # Fallback if qrcode package isn't installed: return empty QR data
        return None, qr_data

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for DB storage
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str, qr_data

def set_order_minipay_details(order_id):
    '''Set MiniPay details for new order.'''
    order = Order.query.get(order_id)
    if not order:
        raise ValueError(f'Order {order_id} not found')
    
    # Generate QR
    qr_data, raw_data = generate_order_qr(order.id, order.total, order.customer_name or order.email)
    
    # Set 30min deadline
    order.minipay_phone = MINIPAY_PHONE
    order.minipay_qr_data = qr_data or ''
    order.payment_deadline = datetime.utcnow() + timedelta(minutes=30)
    order.payment_status = 'none'
    
    db.session.commit()
    return order

def is_payment_expired(order_id):
    '''Check if payment deadline expired.'''
    order = Order.query.get(order_id)
    if not order or not order.payment_deadline:
        return False
    return datetime.utcnow() > order.payment_deadline

def verify_payment_match(order_id, submitted_amount, submitted_ref):
    '''Basic fraud check.'''
    order = Order.query.get(order_id)
    if not order:
        return False
    
    amount_match = abs(order.total - submitted_amount) < 0.01
    ref_match = submitted_ref and order.id.lower() in submitted_ref.lower()
    
    return amount_match and ref_match

def get_pending_payments():
    '''Get orders with pending MiniPay confirmations.'''
    return Order.query.filter(
        Order.payment_status == 'pending',
        Order.payment_deadline > datetime.utcnow()
    ).order_by(Order.payment_deadline.asc()).all()

