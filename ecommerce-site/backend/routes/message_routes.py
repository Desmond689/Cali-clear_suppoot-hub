from flask import Blueprint, request
from database.models import Message, db
from utils.responses import success_response, error_response
from middleware.admin_required import admin_required
from services.email_service import send_email
from datetime import datetime

bp = Blueprint('messages', __name__, url_prefix='/api/messages')

@bp.route('', methods=['POST'])
def create_message():
    """Customer sends a chat message"""
    data = request.json or {}
    email = data.get('email', '').strip()
    name = data.get('name', 'Guest').strip()
    message = data.get('message', '').strip()
    
    if not email or not message:
        return error_response('Email and message are required', 400)
    
    msg = Message(
        customer_email=email,
        customer_name=name,
        message=message,
        status='new'
    )
    db.session.add(msg)
    db.session.commit()
    
    # Notify admin of new message
    send_email(
        'support@caliclear.shop',
        f'New message from {name}',
        f'Customer {name} ({email}) sent a message:\n\n{message}'
    )
    
    return success_response(message='Message sent', data={'id': msg.id})

@bp.route('/thread', methods=['GET'])
def get_thread():
    """Get conversation thread for a customer"""
    email = request.args.get('email', '').strip()
    
    if not email:
        return error_response('Email is required', 400)
    
    messages = Message.query.filter_by(customer_email=email).order_by(Message.created_at.asc()).all()
    
    return success_response(data=[{
        'id': m.id,
        'customer_email': m.customer_email,
        'customer_name': m.customer_name,
        'message': m.message,
        'admin_reply': m.admin_reply,
        'status': m.status,
        'created_at': m.created_at.isoformat() if m.created_at else None,
        'replied_at': m.replied_at.isoformat() if m.replied_at else None
    } for m in messages])

@bp.route('', methods=['GET'])
@admin_required
def get_messages():
    """Admin gets all customer messages"""
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return success_response(data=[{
        'id': m.id,
        'customer_email': m.customer_email,
        'customer_name': m.customer_name,
        'message': m.message,
        'status': m.status,
        'admin_reply': m.admin_reply,
        'created_at': m.created_at.isoformat() if m.created_at else None,
        'replied_at': m.replied_at.isoformat() if m.replied_at else None
    } for m in messages])

@bp.route('/<int:msg_id>', methods=['PUT'])
@admin_required
def reply_message(msg_id):
    """Admin replies to a customer message"""
    msg = Message.query.get(msg_id)
    if not msg:
        return error_response('Message not found', 404)
    
    data = request.json or {}
    reply = data.get('reply', '').strip()
    
    if not reply:
        return error_response('Reply text is required', 400)
    
    msg.admin_reply = reply
    msg.status = 'replied'
    msg.replied_at = datetime.utcnow()
    db.session.commit()
    
    # Send reply email to customer
    send_email(
        msg.customer_email,
        'Reply to your message - Cali Clear Support',
        f'Hello {msg.customer_name},\n\nWe received your message: "{msg.message}"\n\n'
        f'Our response:\n{reply}\n\nThank you for contacting us!'
    )
    
    return success_response(message='Reply sent to customer')
