#!/usr/bin/env python
"""Create admin user"""
from app import app
from database.db import db
from database.models import User

with app.app_context():
    email = 'desmondhenry446@gmail.com'
    password = 'desmond12345$'
    
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_admin = True
        user.set_password(password)
        print(f'Updated {email} to admin with new password')
    else:
        user = User(email=email, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        print(f'Created new admin: {email}')
    
    db.session.commit()
    print('Done!')
