from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from services.auth_service import (
    register_user,
    authenticate_user,
    create_tokens,
    get_user_by_id,
    generate_password_reset_token,
    verify_password_reset_token
)
from utils.responses import success_response, error_response
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Custom decorator for auth endpoints
def rate_limit_auth(f):
    @wraps(f)
    @limiter.limit("5 per minute")
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
@rate_limit_auth
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return error_response('Email and password required'), 400
    
    user, error = register_user(email, password)
    if error:
        return error_response(error), 400
    
    tokens = create_tokens(user)
    return success_response(tokens, 'Registration successful'), 201

@auth_bp.route('/login', methods=['POST'])
@rate_limit_auth
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return error_response('Email and password required'), 400
    
    user, error = authenticate_user(email, password)
    if error:
        return error_response(error), 401
    
    tokens = create_tokens(user)
    return success_response(tokens, 'Login successful'), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    
    if not user:
        return error_response('User not found'), 404
    
    return success_response({
        'id': user.id,
        'email': user.email,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat()
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_token():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    
    if not user:
        return error_response('User not found'), 404
    
    access_token = create_access_token(identity=str(user.id))
    return success_response({'access_token': access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # In a production app, you would blacklist the token here
    return success_response(message='Logged out successfully'), 200


# ----- password reset flow --------------------------------------------------

@auth_bp.route('/forgot-password', methods=['POST'])
@rate_limit_auth
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email')
    if not email:
        return error_response('Email required'), 400

    # lookup user by email (not by id):
    from database.models import User
    user = User.query.filter_by(email=email).first()
    if user:
        token = generate_password_reset_token(user)
        # TODO: send email with link containing token
        # For now we return token in response for development/testing
        return success_response({'reset_token': token}, 'Password reset token generated'), 200
    # return generic success to avoid leaking existence
    return success_response(message='If that email is registered, you will receive a reset link'), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = data.get('token')
    new_password = data.get('password')
    if not token or not new_password:
        return error_response('Token and new password required'), 400

    user = verify_password_reset_token(token)
    if not user:
        return error_response('Invalid or expired token'), 400

    user.set_password(new_password)
    from database.db import db
    db.session.commit()
    # automatically log in the user after resetting
    tokens = create_tokens(user)
    return success_response(tokens, 'Password updated successfully'), 200
