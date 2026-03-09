import stripe
from config import Config

stripe.api_key = Config.STRIPE_SECRET_KEY

def create_payment_intent(amount, currency='usd'):
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
    )
    return intent

def confirm_payment_intent(payment_intent_id):
    intent = stripe.PaymentIntent.confirm(payment_intent_id)
    return intent

def refund_payment(payment_intent_id, amount=None):
    refund = stripe.Refund.create(
        payment_intent=payment_intent_id,
        amount=amount
    )
    return refund
