# Simple script to exercise authentication endpoints using Flask test client
from app import app
from database.db import db
from database.models import User


def test_auth_flow():
    with app.app_context():
        # clean up any existing test user
        User.query.filter_by(email='flow@test.com').delete()
        db.session.commit()

        client = app.test_client()
        print('--- Registering user ---')
        resp = client.post('/api/register', json={'email': 'flow@test.com', 'password': 'Secret123'})
        print('Status', resp.status_code)
        print(resp.get_json())

        print('\n--- Logging in user ---')
        resp = client.post('/api/login', json={'email': 'flow@test.com', 'password': 'Secret123'})
        print('Status', resp.status_code)
        data = resp.get_json()
        print(data)

        print('\n--- Trigger forgot password (existing email) ---')
        resp = client.post('/api/forgot-password', json={'email': 'flow@test.com'})
        print('Status', resp.status_code)
        data = resp.get_json()
        print(data)
        token = None
        if resp.ok and data.get('data'):
            token = data['data'].get('reset_token')
            print('Token returned:', token)

        if token:
            print('\n--- Resetting password using token ---')
            resp = client.post('/api/reset-password', json={'token': token, 'password': 'Newpass456'})
            print('Status', resp.status_code)
            print(resp.get_json())

            print('\n--- Logging in with new password ---')
            resp = client.post('/api/login', json={'email': 'flow@test.com', 'password': 'Newpass456'})
            print('Status', resp.status_code)
            print(resp.get_json())

        # clean up
        user = User.query.filter_by(email='flow@test.com').first()
        if user:
            db.session.delete(user)
            db.session.commit()


if __name__ == '__main__':
    test_auth_flow()
