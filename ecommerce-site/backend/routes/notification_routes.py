from flask import Blueprint, request, jsonify
from database.models import AdminNotification, Order, Message, PaymentConfirmation
from database.db import db
from utils.responses import success_response, error_response
from middleware.admin_required import admin_required
from datetime import datetime, timedelta

notif_bp = Blueprint('notifications', __name__, url_prefix='/api/admin/notifications')


@notif_bp.route('/unread-count', methods=['GET'])
@admin_required
def get_unread_count():
    """Return count of unread admin notifications and new messages."""
    notif_count = AdminNotification.query.filter_by(is_read=False).count()
    msg_count = Message.query.filter_by(status='new').count()
    pending_proof = Order.query.filter_by(payment_status='pending').count()

    return success_response({
        'unread_notifications': notif_count,
        'new_messages': msg_count,
        'pending_payments': pending_proof
    }), 200


@notif_bp.route('', methods=['GET'])
@admin_required
def list_notifications():
    """List recent admin notifications with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    only_unread = request.args.get('unread', 'false').lower() == 'true'

    query = AdminNotification.query
    if only_unread:
        query = query.filter_by(is_read=False)

    pagination = query.order_by(AdminNotification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    items = [{
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'body': n.body,
        'order_id': n.order_id,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat() if n.created_at else None
    } for n in pagination.items]

    return success_response({
        'notifications': items,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@notif_bp.route('/mark-read', methods=['POST'])
@admin_required
def mark_read():
    """Mark notifications as read. Accepts {ids: [1,2,3]} or {all: true}."""
    data = request.get_json() or {}

    if data.get('all'):
        AdminNotification.query.filter_by(is_read=False).update({'is_read': True})
        Message.query.filter_by(status='new').update({'status': 'read'})
        db.session.commit()
        return success_response({'message': 'All notifications marked as read'}), 200

    ids = data.get('ids', [])
    if ids:
        AdminNotification.query.filter(AdminNotification.id.in_(ids)).update(
            {'is_read': True}, synchronize_session=False
        )
        db.session.commit()

    return success_response({'message': 'Notifications marked as read'}), 200


@notif_bp.route('/poll', methods=['GET'])
@admin_required
def poll():
    """
    Long-polling endpoint for real-time updates.
    Returns new notifications since a given timestamp.
    Query params:
      - since: ISO timestamp string (e.g. 2025-01-01T00:00:00)
    """
    since_str = request.args.get('since', '')
    if since_str:
        try:
            since = datetime.fromisoformat(since_str.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            since = datetime.utcnow() - timedelta(minutes=5)
    else:
        since = datetime.utcnow() - timedelta(minutes=5)

    new_notifs = AdminNotification.query.filter(
        AdminNotification.created_at > since
    ).order_by(AdminNotification.created_at.desc()).all()

    new_msgs = Message.query.filter(
        Message.created_at > since,
        Message.customer_name != 'Bot'
    ).order_by(Message.created_at.desc()).all()

    pending_count = Order.query.filter_by(payment_status='pending').count()
    unread_notifs = AdminNotification.query.filter_by(is_read=False).count()
    unread_msgs = Message.query.filter_by(status='new').count()

    return success_response({
        'notifications': [{
            'id': n.id,
            'type': n.notification_type,
            'title': n.title,
            'body': n.body,
            'order_id': n.order_id,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat() if n.created_at else None
        } for n in new_notifs],
        'messages': [{
            'id': m.id,
            'customer_email': m.customer_email,
            'customer_name': m.customer_name,
            'message': m.message[:100],
            'message_type': m.message_type,
            'order_id': m.order_id,
            'created_at': m.created_at.isoformat() if m.created_at else None
        } for m in new_msgs],
        'counts': {
            'unread_notifications': unread_notifs,
            'new_messages': unread_msgs,
            'pending_payments': pending_count
        },
        'server_time': datetime.utcnow().isoformat()
    }), 200


@notif_bp.route('/pending-reminders', methods=['GET'])
@admin_required
def pending_reminders():
    """
    Find orders that have payment instructions sent but no proof uploaded
    after X hours (default 2 hours). These need reminders.
    """
    hours = request.args.get('hours', 2, type=int)
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    stale_orders = Order.query.filter(
        Order.status == 'payment_instructions_sent',
        Order.payment_status.in_(['requested', 'pending']),
        Order.created_at < cutoff
    ).order_by(Order.created_at.asc()).all()

    result = []
    for o in stale_orders:
        last_proof = Message.query.filter_by(
            order_id=o.id, message_type='proof'
        ).order_by(Message.created_at.desc()).first()

        if not last_proof:
            result.append({
                'id': o.id,
                'email': o.email,
                'customer_name': o.customer_name,
                'total': o.total,
                'payment_method_name': o.payment_method_name,
                'created_at': o.created_at.isoformat() if o.created_at else None,
                'hours_waiting': round((datetime.utcnow() - o.created_at).total_seconds() / 3600, 1)
            })

    return success_response({
        'reminders': result,
        'total': len(result)
    }), 200


@notif_bp.route('/send-reminder/<order_id>', methods=['POST'])
@admin_required
def send_reminder(order_id):
    """Send a payment reminder to the customer chat for a specific order."""
    order = Order.query.get(order_id)
    if not order:
        return error_response('Order not found'), 404

    reminder_msg = Message(
        customer_email=order.email,
        customer_name='Bot',
        message=(
            f"⏰ Friendly Reminder\n\n"
            f"Hi! We're still waiting for your payment for Order #{order_id}.\n"
            f"Please complete your payment and upload proof when ready.\n\n"
            f"Need help? Tap 'Talk to Agent' below."
        ),
        message_type='bot',
        order_id=order_id,
        status='replied',
        replied_at=datetime.utcnow()
    )
    db.session.add(reminder_msg)
    db.session.commit()

    return success_response({'message': f'Reminder sent for order {order_id}'}), 200
