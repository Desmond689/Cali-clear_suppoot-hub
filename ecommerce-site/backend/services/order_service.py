from database.models import Order, Cart
from database.db import db

def create_order(user_id, total):
    order = Order(user_id=user_id, total=total)
    db.session.add(order)
    db.session.commit()
    return order

def get_orders_by_user(user_id):
    return Order.query.filter_by(user_id=user_id).all()

def get_order_by_id(order_id):
    return Order.query.get(order_id)

def update_order_status(order_id, status):
    order = Order.query.get(order_id)
    if order:
        order.status = status
        db.session.commit()
        return order
    return None
