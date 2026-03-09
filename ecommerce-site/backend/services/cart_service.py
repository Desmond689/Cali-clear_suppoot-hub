from database.models import Cart, Product

def get_cart_items(cart_id):
    return Cart.query.filter_by(id=cart_id).all()

def add_to_cart(cart_id, product_id, quantity):
    cart_item = Cart.query.filter_by(id=cart_id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(id=cart_id, product_id=product_id, quantity=quantity)
    return cart_item

def clear_cart(cart_id):
    Cart.query.filter_by(id=cart_id).delete()

def calculate_cart_total(cart_id):
    cart_items = get_cart_items(cart_id)
    total = 0.0
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            total += product.price * item.quantity
    return total
