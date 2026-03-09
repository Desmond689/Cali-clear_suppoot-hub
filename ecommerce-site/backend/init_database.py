#!/usr/bin/env python3
import sqlite3
import os
from werkzeug.security import generate_password_hash

# Use the .env DATABASE_URL: sqlite:///ecommerce.db
db_path = os.path.join(os.path.dirname(__file__), 'ecommerce.db')

# Create the database and tables
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create user table
c.execute('''
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Create other required tables
c.execute('''
CREATE TABLE IF NOT EXISTS category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS product (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_id INTEGER,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price FLOAT NOT NULL,
    category_id INTEGER,
    image_url VARCHAR(200),
    stock INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT 1,
    featured BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES category(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS "order" (
    id VARCHAR(20) PRIMARY KEY,
    email VARCHAR(120) NOT NULL,
    total FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'created',
    shipping_address TEXT,
    tracking_number VARCHAR(100),
    carrier VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS order_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id VARCHAR(20) NOT NULL,
    product_id INTEGER,
    quantity INTEGER NOT NULL,
    price FLOAT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES "order"(id),
    FOREIGN KEY (product_id) REFERENCES product(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS cart (
    id VARCHAR(36) PRIMARY KEY,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES product(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS wishlist (
    id VARCHAR(36) PRIMARY KEY,
    product_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES product(id)
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS admin_verification_token (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR(36) UNIQUE NOT NULL,
    admin_email VARCHAR(120) NOT NULL,
    admin_id INTEGER NOT NULL,
    expires_at DATETIME NOT NULL,
    used BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES user(id)
)
''')

conn.commit()

# Check if admin exists
c.execute('SELECT email FROM user WHERE is_admin=1')
admin = c.fetchone()

if not admin:
    # Create admin user
    email = 'desmondhenry446@gmail.com'
    password = 'desmond12345$'
    password_hash = generate_password_hash(password)
    
    c.execute(
        'INSERT INTO user (email, password_hash, is_admin, is_active) VALUES (?, ?, 1, 1)',
        (email, password_hash)
    )
    conn.commit()
    print(f'Admin created: {email}')
else:
    print(f'Admin already exists: {admin[0]}')

conn.close()
print(f'Database initialized at {db_path}')
