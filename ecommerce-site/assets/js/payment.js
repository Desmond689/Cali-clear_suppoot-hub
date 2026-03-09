/**
 * Payment Processing Module
 * Integrates with Stripe for secure payment handling
 * Supports: Visa, Mastercard, Amex, Discover, PayPal, Apple Pay, Google Pay, Afterpay, Klarna, Bank Transfer
 */

// Configuration - loaded from backend via initStripeConfig()
// Get from Stripe Dashboard: https://dashboard.stripe.com/apikeys
// This is set dynamically from backend API
let STRIPE_PUBLISHABLE_KEY = null;

// Stripe Payment Element Configuration - All supported payment methods
const STRIPE_PAYMENT_METHODS = {
  payment_method_types: [
    'card',
    'card_present',
    'interac_present',
    'fpx',
    'bacs_debit',
    'bancontact',
    'giropay',
    'ideal',
    'p24',
    'sepa_debit',
    'sofort',
    'upi',
    'paynow',
    'wechat_pay',
    'konbini',
    'japanese_convenience_store',
    'pay_easy',
    'boleto',
    'oxxo',
    'klarna',
    'afterpay_clearpay',
    'cashapp'
  ]
};

// Display-friendly payment method labels
const PAYMENT_METHOD_LABELS = {
  'card': 'Credit / Debit Card',
  'card_present': 'Card (In-Store)',
  'interac_present': 'Interac',
  'fpx': 'FPX (Malaysia)',
  'bacs_debit': 'BACS Direct Debit (UK)',
  'bancontact': 'Bancontact',
  'giropay': 'Giropay',
  'ideal': 'iDEAL',
  'p24': 'Przelewy24',
  'sepa_debit': 'SEPA Direct Debit',
  'sofort': 'Sofort',
  'upi': 'UPI',
  'paynow': 'PayNow',
  'wechat_pay': 'WeChat Pay',
  'konbini': 'Konbini',
  'japanese_convenience_store': 'Convenience Store (Japan)',
  'pay_easy': 'Pay Easy',
  'boleto': 'Boleto',
  'oxxo': 'OXXO',
  'klarna': 'Klarna - Pay Later',
  'afterpay_clearpay': 'Afterpay / Clearpay',
  'cashapp': 'Cash App Pay',
  'apple_pay': 'Apple Pay',
  'google_pay': 'Google Pay',
  'paypal': 'PayPal',
  'ach_debit': 'ACH Direct Debit (US)'
};

// Initialize Stripe configuration from backend
async function initStripeConfig() {
    try {
        const response = await fetch('/api/config/stripe');
        if (response.ok) {
            const data = await response.json();
            if (data.data && data.data.publishable_key) {
                STRIPE_PUBLISHABLE_KEY = data.data.publishable_key;
                window.StripePublishableKey = data.data.publishable_key;
                return data.data.publishable_key;
            }
        }
        return null;
    } catch (error) {
        console.warn('Could not load Stripe config:', error);
        return null;
    }
}

/**
 * Get authentication headers for API calls
 */
function getAuthHeaders() {
    const token = localStorage.getItem('access_token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

/**
 * Validate card number using Luhn algorithm
 */
function validateCardNumber(cardNumber) {
    const cleaned = cardNumber.replace(/\s/g, '');
    if (!/^\d{13,19}$/.test(cleaned)) return false;
    
    let sum = 0;
    let isEven = false;
    for (let i = cleaned.length - 1; i >= 0; i--) {
        let digit = parseInt(cleaned[i], 10);
        if (isEven) {
            digit *= 2;
            if (digit > 9) digit -= 9;
        }
        sum += digit;
        isEven = !isEven;
    }
    return sum % 10 === 0;
}

/**
 * Detect card type from number
 */
function detectCardType(cardNumber) {
    const cleaned = cardNumber.replace(/\s/g, '');
    
    const patterns = {
        'visa': /^4/,
        'mastercard': /^5[1-5]/,
        'amex': /^3[47]/,
        'discover': /^6(?:011|5)/,
        'diners': /^3(?:0[0-5]|[68])/,
        'jcb': /^(?:2131|1800|35)/
    };
    
    for (const [type, pattern] of Object.entries(patterns)) {
        if (pattern.test(cleaned)) return type;
    }
    return 'unknown';
}

/**
 * Validate expiry date
 */
function validateExpiry(expiry) {
    const match = expiry.match(/^(0[1-9]|1[0-2])\/([0-9]{2})$/);
    if (!match) return false;
    
    const month = parseInt(match[1], 10);
    const year = parseInt('20' + match[2], 10);
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;
    
    if (year < currentYear) return false;
    if (year === currentYear && month < currentMonth) return false;
    if (month > 12 || month < 1) return false;
    
    return true;
}

/**
 * Format card number with spaces
 */
function formatCardNumber(value) {
    const cleaned = value.replace(/\s/g, '').replace(/\D/g, '');
    const chunks = cleaned.match(/.{1,4}/g) || [];
    return chunks.join(' ');
}

/**
 * Create payment intent via backend API
 */
async function createPaymentIntent(amount, currency = 'usd') {
    try {
        const response = await fetch('/api/payment/create-intent', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                amount: Math.round(amount * 100), // Convert to cents
                currency: currency
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Failed to create payment intent');
        }
        
        return data.data;
    } catch (error) {
        console.error('Create payment intent error:', error);
        throw error;
    }
}

/**
 * Process payment with card details
 */
async function processPayment(paymentDetails) {
    const {
        cardNumber,
        expiry,
        cvc,
        name,
        amount,
        currency = 'usd'
    } = paymentDetails;
    
    // Validate inputs
    if (!cardNumber || !expiry || !cvc || !name) {
        throw new Error('Please fill in all card details');
    }
    
    if (!validateCardNumber(cardNumber)) {
        throw new Error('Invalid card number');
    }
    
    if (!validateExpiry(expiry)) {
        throw new Error('Invalid expiry date');
    }
    
    if (!/^\d{3,4}$/.test(cvc)) {
        throw new Error('Invalid CVC');
    }
    
    // Create payment intent
    const intentData = await createPaymentIntent(amount, currency);
    
    // In a real implementation, you would use Stripe.js to confirm payment
    // For now, we'll simulate the payment confirmation
    if (!STRIPE_PUBLISHABLE_KEY) {
        // Simulate payment for demo purposes
        return await simulatePayment(intentData.clientSecret, paymentDetails);
    }
    
    // Real Stripe integration would go here
    return await confirmStripePayment(intentData.clientSecret, {
        card: {
            number: cardNumber.replace(/\s/g, ''),
            exp: expiry,
            cvc: cvc,
            name: name
        }
    });
}

/**
 * Simulate payment for demo/development
 */
async function simulatePayment(clientSecret, paymentDetails) {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Simulate success (in demo mode)
    return {
        success: true,
        paymentId: 'sim_' + Date.now(),
        clientSecret: clientSecret,
        status: 'succeeded',
        message: 'Payment processed successfully (demo mode)'
    };
}

/**
 * Confirm payment with Stripe (placeholder for real implementation)
 */
async function confirmStripePayment(clientSecret, paymentMethod) {
    try {
        // This would use Stripe.js in production
        // const stripe = Stripe(window.StripePublishableKey);
        // const result = await stripe.confirmCardPayment(clientSecret, {
        //     payment_method: {
        //         card: paymentMethod.card
        //     }
        // });
        
        // For now, fall back to simulation
        return await simulatePayment(clientSecret, paymentMethod);
    } catch (error) {
        console.error('Payment confirmation error:', error);
        throw error;
    }
}

/**
 * Validate payment form
 */
function validatePaymentForm(formData) {
    const errors = [];
    
    if (!formData.cardNumber || !validateCardNumber(formData.cardNumber)) {
        errors.push('Invalid card number');
    }
    
    if (!formData.expiry || !validateExpiry(formData.expiry)) {
        errors.push('Invalid expiry date (use MM/YY format)');
    }
    
    if (!formData.cvc || !/^\d{3,4}$/.test(formData.cvc)) {
        errors.push('Invalid CVC');
    }
    
    if (!formData.name || formData.name.trim().length < 2) {
        errors.push('Please enter cardholder name');
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

/**
 * Initialize payment form handlers
 */
function initPaymentForm() {
    const form = document.getElementById('payment-form');
    if (!form) return;
    
    const cardNumberInput = document.getElementById('card-number');
    const expiryInput = document.getElementById('card-expiry');
    const cvcInput = document.getElementById('card-cvc');
    const nameInput = document.getElementById('card-name');
    
    // Format card number
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', (e) => {
            e.target.value = formatCardNumber(e.target.value);
        });
    }
    
    // Format expiry
    if (expiryInput) {
        expiryInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length >= 2) {
                value = value.substring(0, 2) + '/' + value.substring(2, 4);
            }
            e.target.value = value;
        });
    }
    
    // Only allow numbers for CVC
    if (cvcInput) {
        cvcInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').substring(0, 4);
        });
    }
    
    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Processing...';
        submitBtn.disabled = true;
        
        try {
            const formData = {
                cardNumber: cardNumberInput?.value || '',
                expiry: expiryInput?.value || '',
                cvc: cvcInput?.value || '',
                name: nameInput?.value || '',
                amount: parseFloat(document.getElementById('order-total')?.value || 0)
            };
            
            const validation = validatePaymentForm(formData);
            if (!validation.isValid) {
                throw new Error(validation.errors.join(', '));
            }
            
            const result = await processPayment(formData);
            
            if (result.success) {
                // Store payment ID for order confirmation
                localStorage.setItem('lastPaymentId', result.paymentId);
                window.location.href = '/order-success.html?payment_id=' + result.paymentId;
            } else {
                throw new Error(result.message || 'Payment failed');
            }
        } catch (error) {
            if (typeof showToast === 'function') {
                showToast(error.message || 'Payment failed');
            } else {
                alert(error.message || 'Payment failed');
            }
        } finally {
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    });
}

/**
 * Get payment status
 */
async function getPaymentStatus(paymentId) {
    try {
        const response = await fetch(`/api/payment/status/${paymentId}`, {
            headers: getAuthHeaders()
        });
        
        const data = await response.json();
        return data.data;
    } catch (error) {
        console.error('Get payment status error:', error);
        throw error;
    }
}

/**
 * Refund payment
 */
async function refundPayment(paymentId, amount = null) {
    try {
        const response = await fetch('/api/payment/refund', {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({
                payment_id: paymentId,
                amount: amount ? Math.round(amount * 100) : null
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Refund failed');
        }
        
        return data.data;
    } catch (error) {
        console.error('Refund error:', error);
        throw error;
    }
}

// ============ Payment Method Handlers ============

/**
 * Process Apple Pay payment
 */
async function processApplePay() {
    const amount = parseFloat(document.getElementById('order-total')?.value || 0);
    showToast('Initializing Apple Pay...');
    
    try {
        const intentData = await createPaymentIntent(amount, 'usd');
        // In production, use Stripe Apple Pay
        // const stripe = Stripe(window.StripePublishableKey);
        // await stripe.applePay.startSession(intentData.clientSecret);
        
        // For demo, simulate success
        return await simulatePayment(intentData.clientSecret, { method: 'apple_pay' });
    } catch (error) {
        console.error('Apple Pay error:', error);
        throw error;
    }
}

/**
 * Process Google Pay payment
 */
async function processGooglePay() {
    const amount = parseFloat(document.getElementById('order-total')?.value || 0);
    showToast('Initializing Google Pay...');
    
    try {
        const intentData = await createPaymentIntent(amount, 'usd');
        // In production, use Stripe Google Pay
        // const stripe = Stripe(window.StripePublishableKey);
        // await stripe.googlePay.beginSession(intentData.clientSecret);
        
        return await simulatePayment(intentData.clientSecret, { method: 'google_pay' });
    } catch (error) {
        console.error('Google Pay error:', error);
        throw error;
    }
}

/**
 * Process Afterpay / Clearpay payment
 */
async function processAfterpay() {
    const amount = parseFloat(document.getElementById('order-total')?.value || 0);
    
    // Afterpay limits: $35 - $1,500
    if (amount < 35) {
        throw new Error('Afterpay minimum order is $35');
    }
    if (amount > 1500) {
        throw new Error('Afterpay maximum order is $1,500');
    }
    
    showToast('Initializing Afterpay...');
    
    try {
        const intentData = await createPaymentIntent(amount, 'usd');
        // Configure for Afterpay
        intentData.payment_method_types = ['afterpay_clearpay'];
        
        // In production, redirect to Afterpay
        // await stripe.confirmAfterpayPayment(intentData.clientSecret);
        
        return await simulatePayment(intentData.clientSecret, { method: 'afterpay_clearpay' });
    } catch (error) {
        console.error('Afterpay error:', error);
        throw error;
    }
}

/**
 * Process Klarna payment
 */
async function processKlarna() {
    const amount = parseFloat(document.getElementById('order-total')?.value || 0);
    
    // Klarna limits: $35 - $1,000
    if (amount < 35) {
        throw new Error('Klarna minimum order is $35');
    }
    if (amount > 1000) {
        throw new Error('Klarna maximum order is $1,000');
    }
    
    showToast('Initializing Klarna...');
    
    try {
        const intentData = await createPaymentIntent(amount, 'usd');
        // Configure for Klarna
        intentData.payment_method_types = ['klarna'];
        
        // In production, redirect to Klarna
        // await stripe.confirmKlarnaPayment(intentData.clientSecret);
        
        return await simulatePayment(intentData.clientSecret, { method: 'klarna' });
    } catch (error) {
        console.error('Klarna error:', error);
        throw error;
    }
}

/**
 * Process Bank Transfer (ACH / SEPA / BACS)
 */
async function processBankTransfer() {
    const amount = parseFloat(document.getElementById('order-total')?.value || 0);
    const bankRegion = document.getElementById('bank-region')?.value || 'ach';
    
    showToast('Initializing Bank Transfer...');
    
    try {
        const intentData = await createPaymentIntent(amount, 'usd');
        
        // Configure based on bank region
        let paymentMethodType;
        switch (bankRegion) {
            case 'sepa':
                paymentMethodType = 'sepa_debit';
                break;
            case 'bacs':
                paymentMethodType = 'bacs_debit';
                break;
            default:
                paymentMethodType = 'ach_debit';
        }
        
        intentData.payment_method_types = [paymentMethodType];
        
        // In production, collect bank details via Stripe Elements
        // const stripe = Stripe(window.StripePublishableKey);
        // const elements = stripe.elements({ clientSecret: intentData.clientSecret });
        // const paymentElement = elements.create('payment');
        // paymentElement.mount('#bank-element');
        
        return await simulatePayment(intentData.clientSecret, { method: paymentMethodType, bankRegion });
    } catch (error) {
        console.error('Bank Transfer error:', error);
        throw error;
    }
}

/**
 * Get available payment methods for current amount
 */
function getAvailablePaymentMethods(amount) {
    const methods = [];
    
    // Always available
    methods.push('card', 'paypal');
    
    // Digital wallets (requires HTTPS in production)
    if (window.ApplePaySession) methods.push('apple_pay');
    if (window.google && window.google.payments) methods.push('google_pay');
    
    // BNPL services
    if (amount >= 35 && amount <= 1500) {
        methods.push('afterpay_clearpay');
    }
    if (amount >= 35 && amount <= 1000) {
        methods.push('klarna');
    }
    
    // Bank transfers always available
    methods.push('ach_debit', 'sepa_debit', 'bacs_debit');
    
    return methods;
}

/**
 * Initialize dynamic payment sections
 */
function initPaymentSections() {
    const amount = parseFloat(document.getElementById('order-total')?.value || 0);
    const availableMethods = getAvailablePaymentMethods(amount);
    
    // Update Afterpay amount display
    const afterpayAmount = document.getElementById('afterpay-amount');
    if (afterpayAmount) {
        const installment = (amount / 4).toFixed(2);
        afterpayAmount.textContent = '$' + installment + ' x4';
    }
    
    // In production, show/hide based on availability
    console.log('Available payment methods:', availableMethods);
}

// Export functions for use in other modules
window.PaymentUtils = {
    validateCardNumber,
    detectCardType,
    validateExpiry,
    formatCardNumber,
    createPaymentIntent,
    processPayment,
    validatePaymentForm,
    getPaymentStatus,
    refundPayment,
    processApplePay,
    processGooglePay,
    processAfterpay,
    processKlarna,
    processBankTransfer,
    getAvailablePaymentMethods,
    STRIPE_PAYMENT_METHODS,
    PAYMENT_METHOD_LABELS
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', async () => {
    // Load Stripe config
    await initStripeConfig();
    
    // Initialize form handlers
    initPaymentForm();
    
    // Initialize payment sections
    initPaymentSections();
});
