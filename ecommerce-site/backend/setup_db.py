#!/usr/bin/env python
"""Direct database initialization without app context."""
import sys
import os
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'ecommerce_new.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"✓ Connected to database: {db_path}")
    
    # Create user table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(200) NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ User table created/exists")
    
    # Check if admin exists
    cursor.execute("SELECT * FROM user WHERE is_admin=1 LIMIT 1")
    admin = cursor.fetchone()
    
    if admin:
        print(f"✓ Admin user exists: {admin[1]}")
    else:
        print("Creating admin user...")
        from werkzeug.security import generate_password_hash
        email = 'desmondhenry446@gmail.com'
        password = 'desmond12345$'
        password_hash = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO user (email, password_hash, is_admin, is_active)
            VALUES (?, ?, 1, 1)
        ''', (email, password_hash))
        conn.commit()
        print(f"✓ Admin user created: {email}")
    
    conn.close()
    print("\n✓ Database ready for login!")
    
except Exception as e:
    import traceback
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
