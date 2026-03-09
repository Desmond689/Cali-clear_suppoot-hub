from database.models import User
from database.db import db
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import timedelta


def _coerce_user_id(user_id):
    """Normalize user id to int when possible."""
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def register_user(email, password):
    """Register a new user with email and password."""
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return None, 'Email already registered'
    
    # Create new user
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return user, None

def authenticate_user(email, password):
    """Authenticate user with email and password."""
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return None, 'Invalid email or password'
    
    return user, None

def get_user_by_id(user_id):
    """Get user by ID."""
    normalized_id = _coerce_user_id(user_id)
    if normalized_id is None:
        return None
    return User.query.get(normalized_id)

def create_tokens(user):
    """Create access and refresh tokens for user."""
    user_identity = str(user.id)
    access_token = create_access_token(identity=user_identity, expires_delta=timedelta(days=1))
    refresh_token = create_refresh_token(identity=user_identity, expires_delta=timedelta(days=7))
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': {
            'id': user.id,
            'email': user.email,
            'is_admin': user.is_admin
        }
    }

def refresh_access_token(refresh_token):
    """Refresh access token using refresh token."""
    from flask_jwt_extended import jwt_required, get_jwt_identity
    user_id = _coerce_user_id(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return None, 'User not found'

    access_token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
    return {'access_token': access_token}, None


# --- Password reset helpers ------------------------------------------------

def generate_password_reset_token(user, expires_hours=1):
    """Create a short‑lived token for resetting a user's password.

    The token contains an additional claim `pw_reset` so we can verify it's a
    reset token when decoding.
    """
    return create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(hours=expires_hours),
        additional_claims={'pw_reset': True}
    )


def verify_password_reset_token(token):
    """Decode a reset token and return the corresponding User or None."""
    from flask_jwt_extended import decode_token
    try:
        data = decode_token(token)
        if data.get('pw_reset'):
            # Flask‑JWT‑Extended stores the identity in ``sub`` by default
            user_id = _coerce_user_id(data.get('sub') or data.get('identity'))
            if user_id is not None:
                return User.query.get(user_id)
    except Exception:
        return None
    return None


def reset_password(user, new_password):
    """Set a new password on the user and save it to the database."""
    user.set_password(new_password)
    db.session.commit()

def is_admin(user_id):
    """Check if user is admin."""
    user = get_user_by_id(user_id)
    return user and user.is_admin
