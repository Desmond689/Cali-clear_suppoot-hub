from flask import Blueprint, request, jsonify, send_file
from database.models import Order, PaymentConfirmation
from database.db import db
from utils.responses import success_response, error_response
from services.minipay_service import set_order_minipay_details, verify_payment_match
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import io

minipay_bp = Blueprint('minipay', __name__)

UPLOAD_FOLDER = 'backend/static/uploads/screenshots'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@minipay_bp.route('/details/<order_id>', methods=['GET'])
def get_minipay_details(order_id):
    \"\"\"Get MiniPay payment page data for order (QR, deadline, etc)\"\"\"
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    if order.payment_status != 'none':
        return error_response('Payment already initiated'), 400
    
    # Generate/setup MiniPay details
    set_order_minipay_details(order_id)
    
    return success_response({
        'order_id': order.id,
        'amount': order.total,
        'deadline': order.payment_deadline.isoformat() if order.payment_deadline else None,
        'phone': order.minipay_phone,
        'qr_data': order.minipay_qr_data,  # base64 PNG
        'qr_url': f'/api/minipay/qr/{order.id}',  # for img src
        'ref': order.id  # Use order ID as ref
    })

@minipay_bp.route('/qr/<order_id>')
def get_qr_image(order_id):
    \"\"\"Serve QR image for frontend img src.\"\"\"
    order = Order.query.get(order_id)
    if not order or not order.minipay_qr_data:
        return '', 404
    
    # Decode base64 to image
    img_data = base64.b64decode(order.minipay_qr_data)
    img = Image.open(BytesIO(img_data))
    
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

@minipay_bp.route('/confirmation', methods=['POST'])
def submit_payment_confirmation():
    \"\"\"Customer submits payment proof.\"\"\"
    data = request.get_json()
    order_id = data.get('order_id')
    amount_sent = data.get('amount_sent')
    transaction_ref = data.get('transaction_ref')
    
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    if is_payment_expired(order_id):
        return error_response('Payment deadline expired'), 400
    
    # Basic fraud check
    if not verify_payment_match(order_id, amount_sent, transaction_ref):
        return error_response('Payment details do not match order'), 400
    
    # Create confirmation record
    confirmation = PaymentConfirmation(
        order_id=order_id,
        amount_sent=amount_sent,
        transaction_ref=transaction_ref
    )
    db.session.add(confirmation)
    
    # Update order status
    order.payment_status = 'pending'
    order.status = 'pending_payment_verification'
    
    db.session.commit()
    
    return success_response({
        'message': 'Confirmation submitted. Awaiting admin verification.',
        'confirmation_id': confirmation.id
    })

@minipay_bp.route('/confirmation/<int:confirmation_id>', methods=['POST'])
def upload_screenshot(confirmation_id):
    \"\"\"Upload screenshot (optional)\"\"\"
    if 'screenshot' not in request.files:
        return error_response('No file'), 400
    
    file = request.files['screenshot']
    if file.filename == '':
        return error_response('No file selected'), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(f\"{confirmation_id}_{file.filename}\")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        confirmation = PaymentConfirmation.query.get(confirmation_id)
        if confirmation:
            confirmation.screenshot_path = filepath
            db.session.commit()
            return success_response({'message': 'Screenshot uploaded'})
    
    return error_response('Invalid file'), 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def is_payment_expired(order_id):
    from services.minipay_service import is_payment_expired
    return is_payment_expired(order_id)

