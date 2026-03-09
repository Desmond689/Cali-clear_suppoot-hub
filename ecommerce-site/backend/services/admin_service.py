from database.models import User, AdminVerificationToken
from database.db import db
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime, timedelta
import uuid
from services.email_service import send_admin_verification_email

# Admin email whitelist - only these emails can trigger admin login
ADMIN_EMAIL_WHITELIST = [
    'desmondhenry446@gmail.com',  # Admin email
    'dh7799792@gmail.com',       # Second admin
]

# Token expiration in minutes
TOKEN_EXPIRATION_MINUTES = 10


def verify_admin_credentials(email, password):
    """
    Verify admin credentials.
    Returns (user, error) tuple.
    """
    print(f"[DEBUG] verify_admin_credentials: email={email}, whitelist={ADMIN_EMAIL_WHITELIST}")
    
    # Whitelist disabled: allow any email; rely on password + is_admin checks
    # (previously enforced ADMIN_EMAIL_WHITELIST)
    
    # Find admin user by email
    user = User.query.filter_by(email=email).first()
    print(f"[DEBUG] User found: {user}")
    
    if not user:
        print(f"[DEBUG] User not found")
        return None, 'Invalid email or password'
    
    # Verify password
    password_check = user.check_password(password)
    print(f"[DEBUG] Password check result: {password_check}")
    
    if not password_check:
        print(f"[DEBUG] Password invalid")
        return None, 'Invalid email or password'
    
    # Verify user is admin
    print(f"[DEBUG] is_admin: {user.is_admin}")
    
    if not user.is_admin:
        return None, 'Invalid email or password'
    
    print(f"[DEBUG] Credentials valid!")
    return user, None


def generate_verification_token(admin_email, admin_id):
    """
    Generate a one-time verification token for admin login.
    Returns the token string.
    """
    # Invalidate any existing unused tokens for this admin
    existing_tokens = AdminVerificationToken.query.filter_by(
        admin_id=admin_id,
        used=False
    ).all()
    for token in existing_tokens:
        token.used = True
    
    db.session.commit()
    
    # Generate new token
    token_str = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
    
    verification_token = AdminVerificationToken(
        token=token_str,
        admin_email=admin_email,
        admin_id=admin_id,
        expires_at=expires_at,
        used=False
    )
    
    db.session.add(verification_token)
    db.session.commit()
    
    return token_str


def send_verification_email(admin_email):
    """
    Send verification email to admin.
    Returns (token, error) tuple.
    """
    # Whitelist disabled: allow any email; rely on is_admin checks
    # (previously enforced ADMIN_EMAIL_WHITELIST)
    
    # Find admin user by email
    user = User.query.filter_by(email=admin_email).first()
    if not user:
        return None, 'Invalid email or password'
    
    # Verify user is admin
    if not user.is_admin:
        return None, 'Invalid email or password'
    
    # Generate verification token
    token = generate_verification_token(admin_email, user.id)
    
    # Send verification email
    send_admin_verification_email(admin_email, token)
    
    return token, None


def verify_token_and_login(token):
    """
    Verify the admin login token and create session.
    Returns (tokens_dict, error) tuple.
    """
    # Find the token
    verification_token = AdminVerificationToken.query.filter_by(
        token=token,
        used=False
    ).first()
    
    if not verification_token:
        return None, 'Invalid or expired verification link'
    
    # Check if token is expired
    if datetime.utcnow() > verification_token.expires_at:
        return None, 'Verification link has expired'
    
    # Get the admin user
    admin_user = User.query.get(verification_token.admin_id)
    if not admin_user:
        return None, 'Admin user not found'
    
    # Mark token as used
    verification_token.used = True
    db.session.commit()
    
    # Create JWT tokens
    user_identity = str(admin_user.id)
    access_token = create_access_token(
        identity=user_identity,
        expires_delta=timedelta(hours=8)
    )
    refresh_token = create_refresh_token(
        identity=user_identity,
        expires_delta=timedelta(days=7)
    )
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'admin': {
            'id': admin_user.id,
            'email': admin_user.email,
            'is_admin': admin_user.is_admin
        }
    }, None


def is_valid_admin_session(user_id):
    """
    Check if the user has a valid admin session.
    """
    try:
        normalized_id = int(user_id)
    except (TypeError, ValueError):
        return False
    user = User.query.get(normalized_id)
    return user and user.is_admin
