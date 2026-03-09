# Stripe Webhook Setup for Local Testing

## Step 1: Install Stripe CLI

**Windows:**
```powershell
winget install Stripe.CLI
```

**Or download from:** https://docs.stripe.com/stripe-cli#install

## Step 2: Login to Stripe

```bash
stripe login
```

## Step 3: Configure .env File

Create or update your `.env` file in the backend folder:

```env
# Stripe Keys (get these from https://dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**To get your webhook secret:**
```bash
stripe listen --print-secret
```

This will output something like: `whsec_1234567890abcdef`

## Step 4: Start Your Flask Server

```bash
cd backend
python app.py
```

## Step 5: Start Stripe Listener

Open a new terminal and run:

```bash
stripe listen --forward-to localhost:5000/api/payment/webhook
```

## Step 6: Test the Webhook

You should see output like:
```
2024-01-01 12:00:00  --> checkout.session.completed [evt_1234567890]
```

## Step 7: Test Checkout Flow

1. Go to your website at http://localhost:5000
2. Add items to cart
3. Proceed to checkout
4. Complete a test payment using Stripe test card:
   - Card number: `4242 4242 4242 4242`
   - Exp: Any future date (e.g., `12/25`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any valid ZIP (e.g., `12345`)

## Troubleshooting

**Webhook not working?**
- Make sure Stripe CLI is forwarding to the correct port
- Check that your `.env` file has the correct `STRIPE_WEBHOOK_SECRET`
- Restart both Flask server and Stripe listener

**"Signature verification failed" error?**
- The webhook secret has changed - run `stripe listen --print-secret` again
- Update your `.env` file with the new secret

## For Production

When deploying to production:
1. Get live Stripe keys from your Stripe dashboard
2. Configure your hosting provider's environment variables
3. Register your production webhook URL in Stripe Dashboard:
   - Go to Developers → Webhooks
   - Add endpoint: `https://yourdomain.com/api/payment/webhook`
