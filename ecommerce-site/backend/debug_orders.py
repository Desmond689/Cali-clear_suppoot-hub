print('debug_orders.py starting')
try:
    from app import app
    from database.models import Order
    print('imports successful')
except Exception as e:
    print('import error', e)
    raise

with app.app_context():
    print('app context entered')
    total = Order.query.count()
    print('total orders in db =', total)
    orders = Order.query.limit(10).all()
    for o in orders:
        print(o.id, o.email, o.status)
