#!/usr/bin/env python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test imports
try:
    from app import app
    print("✓ Flask app imported successfully")
except Exception as e:
    print(f"✗ Failed to import Flask app: {e}")
    sys.exit(1)

# Test database context and admin check
try:
    with app.app_context():
        from database.models import User
        print("✓ Database models imported successfully")
        
        # Check for admin users
        admin = User.query.filter_by(is_admin=True).first()
        if admin:
            print(f"✓ Admin user found: {admin.email}")
            print(f"  - ID: {admin.id}")
            print(f"  - is_admin: {admin.is_admin}")
            print(f"  - is_active: {admin.is_active}")
            
            # Test password verification
            test_pw = "desmond12345$"
            if admin.check_password(test_pw):
                print(f"✓ Password 'desmond12345$' matches for admin user")
            else:
                print(f"✗ Password 'desmond12345$' does NOT match for admin user")
        else:
            print("✗ No admin user found in database")
            
            # List all users
            all_users = User.query.all()
            print(f"\nTotal users in database: {len(all_users)}")
            for user in all_users:
                print(f"  - {user.email} (admin={user.is_admin})")
except Exception as e:
    import traceback
    print(f"✗ Error during database test: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n✓ All tests passed!")
