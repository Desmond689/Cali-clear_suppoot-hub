from flask import Blueprint, request, jsonify
from database.models import PaymentMethod
from database.db import db
from utils.responses import success_response, error_response
from middleware.admin_required import admin_required
import json

pm_bp = Blueprint('payment_methods', __name__)

# ============ PUBLIC: List active payment methods ============

@pm_bp.route('/payment-methods', methods=['GET'])
def get_active_payment_methods():
    """Return active payment methods for the checkout page"""
    methods = PaymentMethod.query.filter_by(active=True).order_by(PaymentMethod.sort_order).all()
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
            'instructions': m.instructions
        })
    return success_response(result), 200


# ============ ADMIN: Full CRUD ============

@pm_bp.route('/admin/payment-methods', methods=['GET'])
@admin_required
def admin_list_payment_methods():
    """List all payment methods (including inactive)"""
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


@pm_bp.route('/admin/payment-methods', methods=['POST'])
@admin_required
def admin_create_payment_method():
    """Create a new payment method"""
    data = request.get_json()
    if not data:
        return error_response('Invalid request body'), 400

    name = data.get('name', '').strip()
    slug = data.get('slug', '').strip().lower()
    if not name or not slug:
        return error_response('Name and slug are required'), 400

    # Check uniqueness
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


@pm_bp.route('/admin/payment-methods/<int:pm_id>', methods=['PUT'])
@admin_required
def admin_update_payment_method(pm_id):
    """Update a payment method"""
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


@pm_bp.route('/admin/payment-methods/<int:pm_id>', methods=['DELETE'])
@admin_required
def admin_delete_payment_method(pm_id):
    """Delete a payment method"""
    pm = PaymentMethod.query.get(pm_id)
    if not pm:
        return error_response('Payment method not found'), 404

    db.session.delete(pm)
    db.session.commit()
    return success_response({'message': 'Payment method deleted'}), 200


@pm_bp.route('/admin/payment-methods/<int:pm_id>/toggle', methods=['PATCH'])
@admin_required
def admin_toggle_payment_method(pm_id):
    """Toggle active status"""
    pm = PaymentMethod.query.get(pm_id)
    if not pm:
        return error_response('Payment method not found'), 404

    pm.active = not pm.active
    db.session.commit()
    return success_response({'message': f'Payment method {"activated" if pm.active else "deactivated"}'}), 200
