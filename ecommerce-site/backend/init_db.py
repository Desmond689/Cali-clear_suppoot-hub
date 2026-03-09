#!/usr/bin/env python
"""Initialize the database and create an admin user."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Starting database initialization...")

try:
    from app import app, db
    from database.models import User
    
    print("✓ App and models imported")
    
    with app.app_context():
        print("✓ App context activated")
        
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Tables created")
        
        # Check for existing admin
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            print(f"✓ Admin user already exists: {admin.email}")
        else:
            print("Creating admin user...")
            admin = User(email='desmondhenry446@gmail.com', is_admin=True, is_active=True)
            admin.set_password('desmond12345$')
            db.session.add(admin)
            db.session.commit()
            print(f"✓ Admin user created: desmondhenry446@gmail.com")
        
        print("\n✓ Database initialization complete!")
        
except Exception as e:
    import traceback
    print(f"\n✗ Error: {e}")
    traceback.print_exc()
    sys.exit(1)
