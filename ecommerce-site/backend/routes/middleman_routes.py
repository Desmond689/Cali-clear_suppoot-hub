from flask import Blueprint, request, jsonify
from database.models import Middleman, PaymentMethod
from database.db import db
from utils.responses import success_response, error_response
from middleware.admin_required import admin_required
import json

mm_bp = Blueprint('middlemen', __name__, url_prefix='/api/admin/middlemen')


@mm_bp.route('', methods=['GET'])
@admin_required
def list_middlemen():
    """List all middlemen, optionally filtered by payment method."""
    pm_id = request.args.get('payment_method_id', type=int)

    query = Middleman.query
    if pm_id:
        query = query.filter_by(payment_method_id=pm_id)

    middlemen = query.order_by(Middleman.created_at.desc()).all()

    result = []
    for m in middlemen:
        account_info = {}
        try:
            account_info = json.loads(m.account_info) if m.account_info else {}
        except (json.JSONDecodeError, TypeError):
            account_info = {}

        pm_name = m.payment_method.name if m.payment_method else 'Unknown'

        result.append({
            'id': m.id,
            'name': m.name,
            'payment_method_id': m.payment_method_id,
            'payment_method_name': pm_name,
            'account_info': account_info,
            'active': m.active,
            'created_at': m.created_at.isoformat() if m.created_at else None,
            'updated_at': m.updated_at.isoformat() if m.updated_at else None
        })

    return success_response({'middlemen': result}), 200


@mm_bp.route('', methods=['POST'])
@admin_required
def create_middleman():
    """Create a new middleman entry."""
    data = request.get_json()
    if not data:
        return error_response('Invalid request body'), 400

    name = data.get('name', '').strip()
    pm_id = data.get('payment_method_id')
    account_info = data.get('account_info', {})

    if not name or not pm_id:
        return error_response('name and payment_method_id are required'), 400

    pm = PaymentMethod.query.get(pm_id)
    if not pm:
        return error_response('Payment method not found'), 404

    mm = Middleman(
        name=name,
        payment_method_id=pm_id,
        account_info=json.dumps(account_info),
        active=data.get('active', True)
    )
    db.session.add(mm)
    db.session.commit()

    return success_response({'id': mm.id, 'message': 'Middleman created'}), 201


@mm_bp.route('/<int:mm_id>', methods=['PUT'])
@admin_required
def update_middleman(mm_id):
    """Update a middleman entry."""
    mm = Middleman.query.get(mm_id)
    if not mm:
        return error_response('Middleman not found'), 404

    data = request.get_json()
    if not data:
        return error_response('Invalid request body'), 400

    if 'name' in data:
        mm.name = data['name']
    if 'payment_method_id' in data:
        pm = PaymentMethod.query.get(data['payment_method_id'])
        if not pm:
            return error_response('Payment method not found'), 404
        mm.payment_method_id = data['payment_method_id']
    if 'account_info' in data:
        mm.account_info = json.dumps(data['account_info'])
    if 'active' in data:
        mm.active = bool(data['active'])

    db.session.commit()
    return success_response({'message': 'Middleman updated'}), 200


@mm_bp.route('/<int:mm_id>', methods=['DELETE'])
@admin_required
def delete_middleman(mm_id):
    """Delete a middleman entry."""
    mm = Middleman.query.get(mm_id)
    if not mm:
        return error_response('Middleman not found'), 404

    db.session.delete(mm)
    db.session.commit()
    return success_response({'message': 'Middleman deleted'}), 200


@mm_bp.route('/<int:mm_id>/toggle', methods=['PATCH'])
@admin_required
def toggle_middleman(mm_id):
    """Toggle active status of a middleman."""
    mm = Middleman.query.get(mm_id)
    if not mm:
        return error_response('Middleman not found'), 404

    mm.active = not mm.active
    db.session.commit()
    return success_response({'message': f'Middleman {"activated" if mm.active else "deactivated"}'}), 200


@mm_bp.route('/for-method/<slug>', methods=['GET'])
@admin_required
def get_middlemen_for_method(slug):
    """Get active middlemen for a specific payment method (by slug)."""
    pm = PaymentMethod.query.filter_by(slug=slug, active=True).first()
    if not pm:
        return error_response('Payment method not found'), 404

    middlemen = Middleman.query.filter_by(payment_method_id=pm.id, active=True).all()

    result = []
    for m in middlemen:
        account_info = {}
        try:
            account_info = json.loads(m.account_info) if m.account_info else {}
        except (json.JSONDecodeError, TypeError):
            account_info = {}

        result.append({
            'id': m.id,
            'name': m.name,
            'account_info': account_info,
            'payment_method': pm.name
        })

    return success_response({
        'payment_method': pm.name,
        'payment_method_slug': pm.slug,
        'middlemen': result
    }), 200
