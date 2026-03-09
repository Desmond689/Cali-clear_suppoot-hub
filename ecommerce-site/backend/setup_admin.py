#!/usr/bin/env python
"""
Setup admin user for the e-commerce platform.
This script ensures the database is initialized and creates an admin account.
"""
import os
import sys

# Add backend directory to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
parent_dir = os.path.dirname(backend_dir)
sys.path.insert(0, parent_dir)

def main():
    try:
        # Import Flask app
        from app import app, db
        from database.models import User
        
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Check if admin exists
            admin = User.query.filter_by(is_admin=True).first()
            
            if not admin:
                # Create admin user
                admin_email = 'desmondhenry446@gmail.com'
                admin_password = 'desmond12345$'
                
                admin = User(
                    email=admin_email,
                    is_admin=True,
                    is_active=True
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()
                
                return {
                    'success': True,
                    'message': f'Admin user created: {admin_email}',
                    'email': admin_email,
                    'password': admin_password
                }
            else:
                return {
                    'success': True,
                    'message': f'Admin user already exists: {admin.email}',
                    'email': admin.email
                }
                
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Error setting up database: {e}'
        }

if __name__ == '__main__':
    result = main()
    import json
    # Write result to a file for retrieval
    with open('setup_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    # Also print for any terminal that might capture it
    print(json.dumps(result, indent=2))
