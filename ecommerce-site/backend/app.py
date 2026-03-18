from flask import Flask, send_from_directory, send_file, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token
from datetime import timedelta
from dotenv import load_dotenv
from config import Config
from database.db import db
from database.models import User
import os

load_dotenv()

# Get the base directory (ecommerce-site folder)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, 'assets'))
app.config.from_object(Config)
# enable debug mode for development error visibility
app.debug = True

# Enable detailed error logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Configure Flask-Mail
app.config['MAIL_FROM_NAME'] = Config.MAIL_FROM_NAME
app.config['MAIL_FROM_ADDR'] = Config.MAIL_FROM_ADDRESS

CORS(app, supports_credentials=True)
db.init_app(app)
mail = Mail(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)
jwt = JWTManager(app)

# Custom error handler for 500 errors to see actual errors
@app.errorhandler(500)
def handle_500(e):
    import traceback
    traceback.print_exc()
    return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

# Create tables FIRST before any migration/initialization code
with app.app_context():
    db.create_all()
    print("[INIT] Database tables created")


# Register blueprints
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from routes.wishlist_routes import wishlist_bp
from routes.order_routes import order_bp
from routes.payment_routes import payment_bp
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from routes.message_routes import bp as message_bp

app.register_blueprint(product_bp, url_prefix='/api')
app.register_blueprint(cart_bp, url_prefix='/api')
app.register_blueprint(wishlist_bp, url_prefix='/api')
app.register_blueprint(order_bp, url_prefix='/api')
app.register_blueprint(payment_bp, url_prefix='/api/payment')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(message_bp)
app.register_blueprint(minipay_bp, url_prefix='/api/minipay')

# Serve HTML pages
HTML_PAGES = [
    'index', 'shop', 'product', 'cart', 'checkout', 'order-success',
    'login', 'register', 'wishlist', 'about', 'contact', 'faq',
    'privacy', 'terms', 'admin', 'tracking', 'order-history', 'forgot', 'reset', 'intro'
]

for page in HTML_PAGES:
    @app.route(f'/{page}.html', endpoint=f'page_{page}')
    def serve_page(page_name=page):
        return send_file(os.path.join(BASE_DIR, f'{page_name}.html'))

@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'index.html'))

# Serve static files
@app.route('/assets/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'assets'), filename)

# Serve data files
@app.route('/data/<path:filename>')
def serve_data(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'data'), filename)

# Serve components
@app.route('/components/<path:filename>')
def serve_component(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'components'), filename)

# Serve favicon.ico
@app.route('/favicon.ico')
def serve_favicon():
    return send_from_directory(BASE_DIR, 'favicon.ico')

# Run migrations and seed data after tables are created
with app.app_context():
    # Ensure `is_active` column exists in user table (for older databases)
    try:
        conn = db.engine.connect()
        conn.execute(db.text("SELECT is_active FROM user LIMIT 1"))
        conn.close()
    except Exception:
        # Column or table missing; add it
        try:
            conn = db.engine.connect()
            conn.execute(db.text("ALTER TABLE user ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            conn.commit()
            conn.close()
            print("[MIGRATION] Added 'is_active' column to user table")
        except Exception as exc:
            print("[MIGRATION] Failed to add 'is_active' column:", exc)
            try:
                conn.close()
            except Exception:
                pass
    
    # Add missing columns to existing tables
    try:
        # Check if tracking_number column exists, add if not
        db.session.execute(db.text("""
            ALTER TABLE "order" ADD COLUMN tracking_number VARCHAR(100)
        """))
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    try:
        # Check if carrier column exists, add if not
        db.session.execute(db.text("""
            ALTER TABLE "order" ADD COLUMN carrier VARCHAR(50)
        """))
        db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        # Ensure customer_name column exists, add if not (older DBs may miss this)
        db.session.execute(db.text("""
            ALTER TABLE "order" ADD COLUMN customer_name VARCHAR(100)
        """))
        db.session.commit()
    except Exception:
        db.session.rollback()
    
    # Check if we have products, if not seed from JSON
    from database.models import Product, User
    if Product.query.count() == 0:
        try:
            from database.seed import seed_data
            seed_data()
            print("Database seeded with products from products.json")
        except Exception as e:
            print(f"Warning: Could not seed database: {e}")

    # Ensure at least one admin exists for local development/testing
    try:
        has_admin = User.query.filter_by(is_admin=True).count() > 0
        if not has_admin:
            default_email = os.environ.get('ADMIN_DEFAULT_EMAIL', 'admin@caliclear.local')
            default_password = os.environ.get('ADMIN_DEFAULT_PASSWORD', 'Admin@1234')
            admin = User(email=default_email, is_admin=True)
            admin.set_password(default_password)
            db.session.add(admin)
            db.session.commit()
            print(f"[BOOTSTRAP] Created default admin: {default_email} / {default_password}")
    except Exception as e:
        db.session.rollback()
        print(f"[BOOTSTRAP] Failed to create default admin: {e}")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
