# Test script for order tracking functionality
from app import app
from database.db import db
from database.models import Order

def test_tracking():
    with app.app_context():
        # Create a sample order for testing
        order = Order(
            id='TEST123',
            email='test@example.com',
            total=100.0,
            shipping_address='123 Test St',
            status='created'
        )
        db.session.add(order)
        db.session.commit()

        # Test client
        client = app.test_client()

        # Test 1: Update order status to 'shipped' with tracking info
        print("Testing update order status with tracking...")
        response = client.put('/api/orders/TEST123/status', json={
            'status': 'shipped',
            'email': 'test@example.com',
            'tracking_number': 'TRACK123',
            'carrier': 'UPS'
        })
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")

        # Test 2: Retrieve tracking details
        print("\nTesting get tracking details...")
        response = client.get('/api/orders/TEST123/tracking?email=test@example.com')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")

        # Test 3: Update status without tracking (should not set tracking)
        print("\nTesting update status without tracking...")
        response = client.put('/api/orders/TEST123/status', json={
            'status': 'delivered',
            'email': 'test@example.com'
        })
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")

        # Test 4: Get tracking after status change
        print("\nTesting get tracking after status change...")
        response = client.get('/api/orders/TEST123/tracking?email=test@example.com')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")

        # Test 5: Invalid order ID
        print("\nTesting invalid order ID...")
        response = client.get('/api/orders/INVALID/tracking?email=test@example.com')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")

        # Test 6: Wrong email
        print("\nTesting wrong email...")
        response = client.get('/api/orders/TEST123/tracking?email=wrong@example.com')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")

        # Clean up
        db.session.delete(order)
        db.session.commit()

if __name__ == "__main__":
    test_tracking()
