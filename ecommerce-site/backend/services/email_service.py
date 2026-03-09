from flask_mail import Mail, Message
from config import Config

mail = Mail()

# Admin email for all order notifications
ADMIN_EMAIL = "dh7799792@gmail.com"


def _get_sender():
    """Get the proper sender address with name."""
    if hasattr(Config, 'MAIL_FROM_NAME') and hasattr(Config, 'MAIL_FROM_ADDRESS'):
        return f"{Config.MAIL_FROM_NAME} <{Config.MAIL_FROM_ADDRESS}>"
    return Config.MAIL_USERNAME


def send_email(recipient, subject, body):
    """Send a simple text email."""
    try:
        msg = Message(subject, sender=_get_sender(), recipients=[recipient])
        msg.body = body
        mail.send(msg)
        print(f"Email sent to {recipient}: {subject}")
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")


def send_order_confirmation_email(order_id, customer_email, order_details, items, shipping_address, payment_method):
    """
    Send order confirmation email to both customer and admin.
    
    Args:
        order_id: The order ID
        customer_email: Customer's email address
        order_details: Dictionary containing order information
        items: List of order items
        shipping_address: Shipping address dictionary
        payment_method: Payment method used
    """
    # Build detailed email content
    subject = f'Order Confirmation - #{order_id}'
    
    # Build items list
    items_html = ""
    for item in items:
        items_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #eee;">{item.get('name', 'Product')}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{item.get('quantity', 1)}</td>
            <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: right;">${item.get('price', 0):.2f}</td>
        </tr>
        """
    
    # Shipping address formatting
    if isinstance(shipping_address, dict):
        address_str = f"{shipping_address.get('street', '')}, {shipping_address.get('city', '')}, {shipping_address.get('state', '')} {shipping_address.get('zip', '')}"
    else:
        address_str = str(shipping_address)
    
    # HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .order-details {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .total {{ font-size: 18px; font-weight: bold; color: #667eea; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th {{ background: #667eea; color: white; padding: 10px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Order Confirmation</h1>
                <p>Thank you for your order!</p>
            </div>
            <div class="content">
                <p>Hi,</p>
                <p>Your order <strong>#{order_id}</strong> has been successfully placed!</p>
                
                <div class="order-details">
                    <h3>Order Details</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th style="text-align: center;">Qty</th>
                                <th style="text-align: right;">Price</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    <p class="total">Total: ${order_details.get('total', 0):.2f}</p>
                </div>
                
                <div class="order-details">
                    <h3>Shipping Address</h3>
                    <p>{address_str}</p>
                </div>
                
                <div class="order-details">
                    <h3>Payment Method</h3>
                    <p>{payment_method}</p>
                </div>
                
                <p>We'll send you another email once your order ships.</p>
            </div>
            <div class="footer">
                <p>Thank you for shopping with us!</p>
                <p>Questions? Contact us at support@example.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    Order Confirmation - #{order_id}
    
    Thank you for your order!
    
    Order ID: {order_id}
    Total: ${order_details.get('total', 0):.2f}
    
    Items:
    """
    for item in items:
        text_body += f"  - {item.get('name', 'Product')} x {item.get('quantity', 1)}: ${item.get('price', 0):.2f}\n"
    
    text_body += f"""
    Shipping Address:
    {address_str}
    
    Payment Method: {payment_method}
    
    We'll send you another email once your order ships.
    
    Thank you for shopping with us!
    """
    
    sender = _get_sender()
    
    # Send to customer
    try:
        msg_customer = Message(subject, sender=sender, recipients=[customer_email])
        msg_customer.html = html_body
        msg_customer.body = text_body
        mail.send(msg_customer)
        print(f"Order confirmation email sent to customer: {customer_email}")
    except Exception as e:
        print(f"Failed to send email to customer: {e}")
    
    # Send to admin
    try:
        msg_admin = Message(f"New Order - #{order_id}", sender=sender, recipients=[ADMIN_EMAIL])
        msg_admin.html = html_body
        msg_admin.body = text_body
        mail.send(msg_admin)
        print(f"Order notification email sent to admin: {ADMIN_EMAIL}")
    except Exception as e:
        print(f"Failed to send email to admin: {e}")


def send_shipping_update(order_id, email, status, tracking_number=None, carrier=None):
    """Send shipping update email to customer."""
    subject = f'Order Update - #{order_id}'
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .tracking {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Order Update</h1>
            </div>
            <div class="content">
                <p>Your order <strong>#{order_id}</strong> has been updated.</p>
                <p>New Status: <strong>{status}</strong></p>
                {'<div class="tracking"><h3>Tracking Information</h3><p>Tracking Number: ' + tracking_number + '</p><p>Carrier: ' + carrier + '</p></div>' if tracking_number and carrier else ''}
            </div>
            <div class="footer">
                <p>Thank you for shopping with us!</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Order Update - #{order_id}
    
    Status: {status}
    """
    if tracking_number and carrier:
        text_body += f"""
    Tracking Number: {tracking_number}
    Carrier: {carrier}
    """
    
    try:
        msg = Message(subject, sender=_get_sender(), recipients=[email])
        msg.html = html_body
        msg.body = text_body
        mail.send(msg)
        print(f"Shipping update email sent to: {email}")
    except Exception as e:
        print(f"Failed to send shipping update email: {e}")


def send_refund_notification(order_id, email, amount):
    """Send refund notification email to customer."""
    subject = f'Refund Processed - Order #{order_id}'
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .refund {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Refund Processed</h1>
            </div>
            <div class="content">
                <p>A refund has been processed for your order <strong>#{order_id}</strong>.</p>
                <div class="refund">
                    <p>Refund Amount: <strong>${amount:.2f}</strong></p>
                    <p>Please allow 5-10 business days for the refund to appear on your statement.</p>
                </div>
            </div>
            <div class="footer">
                <p>Thank you for shopping with us!</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Refund Processed - Order #{order_id}
    
    Refund Amount: ${amount:.2f}
    
    Please allow 5-10 business days for the refund to appear on your statement.
    
    Thank you for shopping with us!
    """
    
    try:
        msg = Message(subject, sender=_get_sender(), recipients=[email])
        msg.html = html_body
        msg.body = text_body
        mail.send(msg)
        print(f"Refund notification email sent to: {email}")
    except Exception as e:
        print(f"Failed to send refund notification email: {e}")


def send_admin_verification_email(email, token):
    """Send admin login verification email."""
    from config import Config
    
    subject = 'Admin Login Verification - Cali Clear'
    
    # Build verification link
    base_url = Config.FRONTEND_URL if hasattr(Config, 'FRONTEND_URL') else 'http://localhost:3000'
    verification_link = f"{base_url}/admin/verify?token={token}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9f9f9; }}
            .button {{ display: inline-block; padding: 15px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; border-radius: 8px; margin: 20px 0; }}
            .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Admin Login Verification</h1>
            </div>
            <div class="content">
                <p>Someone (hopefully you) is trying to access the admin panel.</p>
                <p>To confirm this login attempt, please click the button below:</p>
                
                <div style="text-align: center;">
                    <a href="{verification_link}" class="button">Yes, It's Me - Verify Login</a>
                </div>
                
                <div class="warning">
                    <strong>Security Note:</strong><br>
                    This verification link will expire in 10 minutes for your security.<br>
                    If you didn't attempt to log in, please ignore this email.
                </div>
                
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #667eea;">{verification_link}</p>
            </div>
            <div class="footer">
                <p>Cali Clear - Admin Panel</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
    Admin Login Verification - Cali Clear
    
    Someone (hopefully you) is trying to access the admin panel.
    
    To confirm this login attempt, please visit:
    {verification_link}
    
    This verification link will expire in 10 minutes for your security.
    If you didn't attempt to log in, please ignore this email.
    
    Cali Clear - Admin Panel
    """
    
    try:
        msg = Message(subject, sender=_get_sender(), recipients=[email])
        msg.html = html_body
        msg.body = text_body
        mail.send(msg)
        print(f"Admin verification email sent to: {email}")
    except Exception as e:
        print(f"Failed to send admin verification email: {e}")
