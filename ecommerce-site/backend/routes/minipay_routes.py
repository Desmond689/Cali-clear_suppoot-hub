#!/usr/bin/env python3
"""MiniPay Routes - Complete payment flow API"""

from flask import Blueprint, request, jsonify, send_file
from database.models import Order, OrderItem, PaymentConfirmation, Product
from database.db import db
from utils.responses import success_response, error_response
from services.minipay_service import (
    generate_order_qr, 
    set_order_minipay_details, 
    is_payment_expired,
    verify_payment_match,
    get_pending_payments,
    MINIPAY_PHONE
)
from services.email_service import send_payment_confirmation_email, send_payment_verified_email, send_payment_rejected_email
from datetime import datetime, timedelta
import base64
import io

minipay_bp = Blueprint('minipay', __name__)

# ============ ORDER MINIPAY SETUP ============

@minipay_bp.route('/setup/<order_id>', methods=['POST'])
def setup_minipay_order(order_id):
    """Setup MiniPay details for an order"""
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    try:
        # Set MiniPay details (generates QR, sets deadline)
        set_order_minipay_details(order_id)
        
        return success_response({
            'message': 'MiniPay details generated',
            'order_id': order_id,
            'minipay_phone': order.minipay_phone,
            'payment_deadline': order.payment_deadline.isoformat() if order.payment_deadline else None
        }), 200
    except Exception as e:
        return error_response(str(e)), 500


@minipay_bp.route('/order/<order_id>', methods=['GET'])
def get_order_payment_info(order_id):
    """Get order payment information including QR code"""
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    # Check if payment is expired
    is_expired = is_payment_expired(order_id) if order.payment_status in ['none', 'pending'] else False
    
    # Get QR code as base64
    qr_data = None
    if order.minipay_qr_data:
        qr_data = f"data:image/png;base64,{order.minipay_qr_data}"
    
    # Get pending confirmations for this order
    confirmations = PaymentConfirmation.query.filter_by(order_id=order_id).order_by(
        PaymentConfirmation.submitted_at.desc()
    ).all()
    
    return success_response({
        'order_id': order.id,
        'total': order.total,
        'customer_name': order.customer_name,
        'email': order.email,
        'minipay_phone': order.minipay_phone,
        'qr_code': qr_data,
        'payment_status': order.payment_status,
        'payment_deadline': order.payment_deadline.isoformat() if order.payment_deadline else None,
        'is_expired': is_expired,
        'status': order.status,
        'confirmations': [{
            'id': c.id,
            'amount_sent': c.amount_sent,
            'transaction_ref': c.transaction_ref,
            'submitted_at': c.submitted_at.isoformat() if c.submitted_at else None,
            'status': c.status
        } for c in confirmations]
    }), 200


# ============ PAYMENT CONFIRMATION ============

@minipay_bp.route('/confirm', methods=['POST'])
def submit_payment_confirmation():
    """Submit payment confirmation from customer"""
    data = request.get_json()
    
    order_id = data.get('order_id')
    amount_sent = data.get('amount_sent')
    transaction_ref = data.get('transaction_ref')
    payment_time = data.get('payment_time')
    screenshot_base64 = data.get('screenshot')  # Base64 encoded image
    
    if not order_id or not amount_sent or not transaction_ref:
        return error_response('Order ID, amount, and transaction reference are required'), 400
    
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    # Check if already paid
    if order.payment_status == 'verified':
        return error_response('Order already paid'), 400
    
    # Check if expired
    if is_payment_expired(order_id):
        return error_response('Payment deadline expired. Please create a new order.'), 400
    
    # Parse payment time
    submitted_time = None
    if payment_time:
        try:
            submitted_time = datetime.fromisoformat(payment_time.replace('Z', '+00:00'))
        except:
            submitted_time = datetime.utcnow()
    else:
        submitted_time = datetime.utcnow()
    
    # Decode screenshot if provided
    screenshot_data = None
    if screenshot_base64:
        try:
            # Remove data URL prefix if present
            if ',' in screenshot_base64:
                screenshot_base64 = screenshot_base64.split(',')[1]
            screenshot_data = base64.b64decode(screenshot_base64)
        except Exception as e:
            print(f'Warning: Could not decode screenshot: {e}')
    
    # Create payment confirmation record
    confirmation = PaymentConfirmation(
        order_id=order_id,
        amount_sent=float(amount_sent),
        transaction_ref=transaction_ref,
        submitted_at=submitted_time,
        screenshot_data=screenshot_data,
        status='pending'
    )
    
    db.session.add(confirmation)
    
    # Update order status
    order.payment_status = 'pending'
    order.transaction_ref = transaction_ref
    
    # Store screenshot path if needed
    if screenshot_data:
        order.screenshot_path = f'payment_screenshots/{order_id}_{confirmation.id}.png'
    
    db.session.commit()
    
    # Send notification email
    try:
        send_payment_confirmation_email(
            order_id=order_id,
            customer_email=order.email,
            amount=amount_sent,
            transaction_ref=transaction_ref
        )
    except Exception as e:
        print(f'Warning: Could not send payment confirmation email: {e}')
    
    return success_response({
        'message': 'Payment confirmation submitted',
        'confirmation_id': confirmation.id,
        'status': 'pending'
    }), 201


# ============ ADMIN PAYMENT MANAGEMENT ============

@minipay_bp.route('/admin/pending', methods=['GET'])
def get_pending_payments_admin():
    """Get all pending payment confirmations (admin)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get orders with pending payments
        query = Order.query.filter(
            Order.payment_status == 'pending'
        ).order_by(Order.payment_deadline.asc())
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        orders = pagination.items
        
        # Get payment confirmations for these orders
        order_ids = [o.id for o in orders]
        confirmations = {}
        if order_ids:
            confs = PaymentConfirmation.query.filter(
                PaymentConfirmation.order_id.in_(order_ids),
                PaymentConfirmation.status == 'pending'
            ).all()
            for c in confs:
                confirmations[c.order_id] = c
        
        result = []
        for order in orders:
            conf = confirmations.get(order.id)
            result.append({
                'order_id': order.id,
                'customer_name': order.customer_name,
                'email': order.email,
                'order_total': order.total,
                'amount_sent': conf.amount_sent if conf else None,
                'transaction_ref': conf.transaction_ref if conf else order.transaction_ref,
                'submitted_at': conf.submitted_at.isoformat() if conf and conf.submitted_at else None,
                'payment_deadline': order.payment_deadline.isoformat() if order.payment_deadline else None,
                'has_screenshot': bool(conf.screenshot_data) if conf else False,
                'status': order.payment_status
            })
        
        return success_response({
            'payments': result,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(str(e)), 500


@minipay_bp.route('/admin/verify/<order_id>', methods=['POST'])
def verify_payment(order_id):
    """Admin verifies payment and activates order"""
    data = request.get_json()
    action = data.get('action')  # 'verify' or 'reject'
    admin_notes = data.get('notes', '')
    
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    if action == 'verify':
        # Verify the payment
        order.payment_status = 'verified'
        order.status = 'paid'  # Activate the order
        
        # Update any pending confirmations
        PaymentConfirmation.query.filter_by(
            order_id=order_id, 
            status='pending'
        ).update({'status': 'verified'})
        
        db.session.commit()
        
        # Send confirmation email
        try:
            send_payment_verified_email(
                order_id=order_id,
                customer_email=order.email,
                order_total=order.total
            )
        except Exception as e:
            print(f'Warning: Could not send payment verified email: {e}')
        
        return success_response({
            'message': 'Payment verified successfully',
            'order_status': order.status,
            'payment_status': order.payment_status
        }), 200
        
    elif action == 'reject':
        # Reject the payment
        reason = data.get('reason', 'Payment could not be verified')
        
        order.payment_status = 'rejected'
        
        # Update any pending confirmations
        PaymentConfirmation.query.filter_by(
            order_id=order_id,
            status='pending'
        ).update({'status': 'rejected'})
        
        db.session.commit()
        
        # Send rejection email
        try:
            send_payment_rejected_email(
                order_id=order_id,
                customer_email=order.email,
                reason=reason
            )
        except Exception as e:
            print(f'Warning: Could not send payment rejected email: {e}')
        
        return success_response({
            'message': 'Payment rejected',
            'order_status': order.status,
            'payment_status': order.payment_status,
            'reason': reason
        }), 200
    else:
        return error_response('Invalid action. Use "verify" or "reject"'), 400


@minipay_bp.route('/admin/screenshot/<order_id>', methods=['GET'])
def get_payment_screenshot(order_id):
    """Get payment screenshot for admin review"""
    confirmation = PaymentConfirmation.query.filter_by(order_id=order_id).order_by(
        PaymentConfirmation.submitted_at.desc()
    ).first()
    
    if not confirmation or not confirmation.screenshot_data:
        return error_response('No screenshot found'), 404
    
    return send_file(
        io.BytesIO(confirmation.screenshot_data),
        mimetype='image/png',
        as_attachment=False,
        download_name=f'payment_{order_id}.png'
    )


@minipay_bp.route('/admin/history', methods=['GET'])
def get_payment_history_admin():
    """Get payment history for admin"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status')  # verified, rejected, pending
        
        query = Order.query.filter(Order.payment_status.in_(['verified', 'rejected', 'pending']))
        
        if status:
            query = query.filter(Order.payment_status == status)
        
        query = query.order_by(Order.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for order in pagination.items:
            result.append({
                'order_id': order.id,
                'customer_name': order.customer_name,
                'email': order.email,
                'total': order.total,
                'payment_status': order.payment_status,
                'transaction_ref': order.transaction_ref,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'payment_date': order.updated_at.isoformat() if hasattr(order, 'updated_at') and order.updated_at else None
            })
        
        return success_response({
            'history': result,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
    except Exception as e:
        return error_response(str(e)), 500


@minipay_bp.route('/admin/analytics', methods=['GET'])
def get_payment_analytics():
    """Get MiniPay analytics for admin"""
    try:
        # Get date range
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total MiniPay payments
        total_payments = Order.query.filter(
            Order.payment_status == 'verified',
            Order.created_at >= start_date
        ).count()
        
        # Total revenue from MiniPay
        from sqlalchemy import func
        total_revenue = db.session.query(func.sum(Order.total)).filter(
            Order.payment_status == 'verified',
            Order.created_at >= start_date
        ).scalar() or 0
        
        # Average payment value
        avg_payment = float(total_revenue) / total_payments if total_payments > 0 else 0
        
        # Pending payments count
        pending_count = Order.query.filter(Order.payment_status == 'pending').count()
        
        # Rejected payments count
        rejected_count = Order.query.filter(
            Order.payment_status == 'rejected',
            Order.created_at >= start_date
        ).count()
        
        # Success rate
        completed_count = total_payments + rejected_count
        success_rate = (total_payments / completed_count * 100) if completed_count > 0 else 0
        
        # Daily breakdown
        daily_data = db.session.query(
            func.date(Order.created_at).label('date'),
            func.count(Order.id).label('count'),
            func.sum(Order.total).label('revenue')
        ).filter(
            Order.payment_status == 'verified',
            Order.created_at >= start_date
        ).group_by(func.date(Order.created_at)).all()
        
        daily_breakdown = []
        for date, count, revenue in daily_data:
            daily_breakdown.append({
                'date': str(date),
                'count': count,
                'revenue': float(revenue or 0)
            })
        
        return success_response({
            'total_payments': total_payments,
            'total_revenue': float(total_revenue),
            'average_payment': round(avg_payment, 2),
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'success_rate': round(success_rate, 1),
            'daily_breakdown': daily_breakdown,
            'period_days': days
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(str(e)), 500


# ============ CUSTOMER PAYMENT HISTORY ============

@minipay_bp.route('/customer/history', methods=['GET'])
def get_customer_payment_history():
    """Get customer's payment history"""
    email = request.args.get('email')
    
    if not email:
        return error_response('Email required'), 400
    
    try:
        orders = Order.query.filter_by(email=email).order_by(Order.created_at.desc()).all()
        
        result = []
        for order in orders:
            result.append({
                'order_id': order.id,
                'total': order.total,
                'status': order.status,
                'payment_status': order.payment_status,
                'transaction_ref': order.transaction_ref,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'payment_deadline': order.payment_deadline.isoformat() if order.payment_deadline else None
            })
        
        return success_response({
            'payments': result
        }), 200
    except Exception as e:
        return error_response(str(e)), 500


# ============ REFUND HANDLING ============

@minipay_bp.route('/admin/refund/<order_id>', methods=['POST'])
def process_refund(order_id):
    """Process refund for an order"""
    data = request.get_json()
    reason = data.get('reason', 'Refund initiated by admin')
    
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404
    
    if order.payment_status != 'verified':
        return error_response('Can only refund verified payments'), 400
    
    # Mark as refunded
    order.payment_status = 'refunded'
    order.status = 'refunded'
    
    db.session.commit()
    
    # TODO: Actually process refund via MiniPay API if available
    
    return success_response({
        'message': 'Refund processed',
        'order_id': order_id,
        'refund_reason': reason
    }), 200


# ============ CONFIG ============

@minipay_bp.route('/config', methods=['GET'])
def get_minipay_config():
    """Get MiniPay configuration for frontend"""
    return success_response({
        'minipay_phone': MINIPAY_PHONE,
        'payment_deadline_minutes': 30,
        'currency': 'USD'
    }), 200
