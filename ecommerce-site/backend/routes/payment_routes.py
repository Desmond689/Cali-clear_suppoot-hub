from flask import Blueprint, request, jsonify
import stripe
from config import Config
from database.models import Order
from database.db import db
from utils.responses import success_response, error_response
from services.email_service import send_refund_notification

stripe.api_key = Config.STRIPE_SECRET_KEY

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/config/stripe', methods=['GET'])
def get_stripe_config():
    """Return Stripe publishable key for frontend"""
    publishable_key = Config.STRIPE_PUBLISHABLE_KEY if hasattr(Config, 'STRIPE_PUBLISHABLE_KEY') else None
    return success_response({
        'publishable_key': publishable_key,
        'is_configured': bool(publishable_key)
    }), 200

@payment_bp.route('/create-intent', methods=['POST'])
def create_payment_intent():
    """Create a payment intent for direct card payments"""
    data = request.get_json()
    amount = data.get('amount')  # in cents
    currency = data.get('currency', 'usd')
    
    if not amount:
        return error_response('Amount required'), 400
    
    try:
        # If Stripe is configured, create real payment intent
        if Config.STRIPE_SECRET_KEY:
            intent = stripe.PaymentIntent.create(
                amount=int(amount),
                currency=currency,
                automatic_payment_methods={'enabled': True}
            )
            return success_response({
                'clientSecret': intent.client_secret,
                'paymentId': intent.id
            }), 200
        else:
            # Demo mode - return simulated intent
            import uuid
            demo_id = f'demo_{uuid.uuid4().hex[:16]}'
            return success_response({
                'clientSecret': f'{demo_id}_secret_demo',
                'paymentId': demo_id,
                'demo_mode': True
            }), 200
    except Exception as e:
        return error_response(str(e)), 500

@payment_bp.route('/status/<payment_id>', methods=['GET'])
def get_payment_status(payment_id):
    """Get payment status"""
    try:
        if Config.STRIPE_SECRET_KEY and not payment_id.startswith('demo_'):
            intent = stripe.PaymentIntent.retrieve(payment_id)
            return success_response({
                'id': intent.id,
                'status': intent.status,
                'amount': intent.amount / 100
            }), 200
        else:
            # Demo mode
            return success_response({
                'id': payment_id,
                'status': 'succeeded',
                'amount': 0,
                'demo_mode': True
            }), 200
    except Exception as e:
        return error_response(str(e)), 500

@payment_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    data = request.get_json()
    order_id = data.get('order_id')
    amount = data.get('amount')  # in cents

    if not order_id or not amount:
        return error_response('Order ID and amount required'), 400

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card', 'apple_pay', 'google_pay', 'paypal', 'klarna', 'afterpay_clearpay', 'sepa_debit', 'ach_debit'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': f'Order {order_id}'},
                    'unit_amount': int(amount * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{request.host_url}order-success.html?order_id={order_id}',
            cancel_url=f'{request.host_url}checkout.html',
            metadata={'order_id': order_id}
        )
        return success_response({'session_id': session.id, 'url': session.url}), 200
    except Exception as e:
        return error_response(str(e)), 500

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, Config.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session['metadata']['order_id']
        # Update order status to paid
        order = Order.query.get(order_id)
        if order:
            order.status = 'paid'
            db.session.commit()

    return jsonify({'status': 'success'}), 200

@payment_bp.route('/refund', methods=['POST'])
def refund_payment():
    data = request.get_json()
    order_id = data.get('order_id')
    amount = data.get('amount')  # in dollars

    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404

    try:
        refund = stripe.Refund.create(
            amount=int(amount * 100),
            currency='usd',
            metadata={'order_id': order_id}
        )
        order.status = 'refunded'
        db.session.commit()
        send_refund_notification(order_id, order.email, amount)
        return success_response({'refund_id': refund.id}), 200
    except Exception as e:
        return error_response(str(e)), 500
