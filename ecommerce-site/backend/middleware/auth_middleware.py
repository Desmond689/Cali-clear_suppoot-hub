from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
from flask import jsonify
from services.auth_service import get_user_by_id

def jwt_required_custom(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = get_user_by_id(user_id)
            if not user:
                return jsonify({'message': 'User not found'}), 401
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token is missing or invalid'}), 401
    return wrapper

def admin_required_jwt(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = get_user_by_id(user_id)
            if not user or not user.is_admin:
                return jsonify({'message': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token is missing or invalid'}), 401
    return wrapper
