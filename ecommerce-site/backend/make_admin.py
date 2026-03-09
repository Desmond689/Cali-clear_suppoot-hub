#!/usr/bin/env python
"""Script to make a user an admin"""
from app import app
from database.db import db
from database.models import User

with app.app_context():
    user = User.query.filter_by(email='desmondhenry446@gmail.com').first()
    if user:
        user.is_admin = True
        db.session.commit()
        print(f'✅ {user.email} is now an admin!')
    else:
        print('❌ User not found')
