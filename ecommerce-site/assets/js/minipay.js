// MiniPay Page Logic
const API_URL = '/api';

let orderId = new URLSearchParams(window.location.search).get('order_id');
let orderData = null;
let deadlineTimer = null;

document.addEventListener('DOMContentLoaded', initMiniPay);

async function initMiniPay() {
  if (!orderId) {
    showStatus('Invalid order ID. <a href="checkout.html">Back to Checkout</a>', 'error');
    return;
  }
  
  try {
    showLoading('Loading payment details...');
    
    // Use correct API endpoint
    const response = await fetch(`${API_URL}/minipay/order/${orderId}`);
    const data = await response.json();
    
    if (!response.ok) throw new Error(data.message || 'Failed to load order');
    
    orderData = data.data;
    
    // Check if already paid
    if (orderData.payment_status === 'verified') {
      showStatus('Order already paid! <a href="order-history.html">View Orders</a>', 'success');
      document.getElementById('confirmation-section').style.display = 'none';
      return;
    }
    
    // Check if expired
    if (orderData.is_expired) {
      showStatus('Payment deadline expired. Please place a new order.', 'error');
      document.getElementById('confirmation-section').style.display = 'none';
      return;
    }
    
    renderPaymentPage(orderData);
    
    if (orderData.payment_deadline) {
      startDeadlineTimer(orderData.payment_deadline);
    }
    
  } catch (error) {
    console.error('MiniPay init error:', error);
    showStatus(error.message || 'Error loading payment details', 'error');
  }
}

function renderPaymentPage(data) {
  document.getElementById('order-id').textContent = data.order_id;
  document.getElementById('order-amount').textContent = parseFloat(data.total).toFixed(2);
  document.getElementById('minipay-phone').textContent = data.minipay_phone || '+1234567890';
  
  // Update instruction fields
  document.getElementById('instr-amount').textContent = parseFloat(data.total).toFixed(2);
  document.getElementById('instr-order').textContent = data.order_id;
  
  if (data.payment_deadline) {
    const deadline = new Date(data.payment_deadline);
    document.getElementById('deadline').textContent = deadline.toLocaleString();
  }
  
  document.getElementById('conf-order-id').value = data.order_id;
  document.getElementById('order-details').style.display = 'block';
  
  if (data.qr_code) {
    document.getElementById('qr-code').src = data.qr_code;
  }
  
  document.getElementById('timer').style.display = 'block';
  
  hideLoading();
  showConfirmationForm();
}

function startDeadlineTimer(deadline) {
  if (deadlineTimer) clearInterval(deadlineTimer);
  
  const end = new Date(deadline).getTime();
  
  deadlineTimer = setInterval(() => {
    const now = Date.now();
    const remaining = Math.max(0, end - now);
    const mins = Math.floor(remaining / 60000);
    const secs = Math.floor((remaining % 60000) / 1000);
    
    const timerEl = document.getElementById('timer');
    if (timerEl) {
      timerEl.textContent = `${mins}m ${secs}s remaining`;
    }
    
    if (remaining <= 0) {
      clearInterval(deadlineTimer);
      if (timerEl) {
        timerEl.style.background = '#dc3545';
        timerEl.textContent = 'EXPIRED';
      }
      showStatus('Payment deadline expired. Please place a new order.', 'error');
      document.getElementById('confirmation-section').style.display = 'none';
    }
  }, 1000);
}

function showConfirmationForm() {
  const section = document.getElementById('confirmation-section');
  if (section) section.style.display = 'block';
  
  // Set default payment time to now
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  const timeInput = document.getElementById('conf-time');
  if (timeInput) {
    timeInput.value = now.toISOString().slice(0, 16);
  }
  
  // Pre-fill amount if available
  if (orderData) {
    const amountInput = document.getElementById('conf-amount');
    if (amountInput) amountInput.value = parseFloat(orderData.total).toFixed(2);
  }
}

function hideLoading() {
  const loading = document.querySelector('.loading');
  if (loading) loading.remove();
}

function showStatus(message, type = 'info') {
  const statusEl = document.getElementById('status-message');
  if (!statusEl) return;
  
  statusEl.innerHTML = message;
  statusEl.className = `status-${type}`;
  statusEl.style.display = 'block';
  statusEl.style.padding = '20px';
  statusEl.style.borderRadius = '12px';
  statusEl.style.marginTop = '20px';
  
  if (type === 'success') {
    statusEl.style.background = 'rgba(40, 167, 69, 0.2)';
    statusEl.style.color = '#28a745';
    statusEl.style.border = '1px solid #28a745';
  } else if (type === 'error') {
    statusEl.style.background = 'rgba(220, 53, 69, 0.2)';
    statusEl.style.color = '#dc3545';
    statusEl.style.border = '1px solid #dc3545';
  } else {
    statusEl.style.background = 'rgba(102, 126, 234, 0.2)';
    statusEl.style.color = '#667eea';
    statusEl.style.border = '1px solid #667eea';
  }
  
  hideLoading();
}

// Confirmation form handler
const confirmationForm = document.getElementById('confirmation-form');
if (confirmationForm) {
  confirmationForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const submitBtn = confirmationForm.querySelector('button[type="submit"]');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';
    }
    
    const amountSent = parseFloat(document.getElementById('conf-amount').value);
    const transactionRef = document.getElementById('conf-ref').value;
    const paymentTime = document.getElementById('conf-time').value;
    
    // Handle screenshot
    let screenshotBase64 = null;
    const screenshotInput = document.getElementById('conf-screenshot');
    if (screenshotInput && screenshotInput.files[0]) {
      screenshotBase64 = await toBase64(screenshotInput.files[0]);
    }
    
    const formData = {
      order_id: document.getElementById('conf-order-id').value,
      amount_sent: amountSent,
      transaction_ref: transactionRef,
      payment_time: paymentTime,
      screenshot: screenshotBase64
    };
    
    try {
      const response = await fetch(`${API_URL}/minipay/confirm`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        showStatus('Confirmation submitted! Admin will verify your payment shortly.<br><br><a href="order-history.html" style="color:#667eea;">View Order Status</a>', 'success');
        confirmationForm.style.display = 'none';
        
        // Optionally poll for payment status
        startStatusPolling(formData.order_id);
      } else {
        throw new Error(result.message || 'Failed to submit confirmation');
      }
    } catch (error) {
      console.error('Confirmation error:', error);
      showStatus('Error: ' + (error.message || 'Failed to submit confirmation'), 'error');
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Submit Confirmation';
      }
    }
  });
}

// Poll for payment status updates
function startStatusPolling(oid) {
  const pollInterval = setInterval(async () => {
    try {
      const response = await fetch(`${API_URL}/minipay/order/${oid}`);
      const data = await response.json();
      
      if (data.data.payment_status === 'verified') {
        clearInterval(pollInterval);
        showStatus('Payment verified! Order is now being processed.<br><a href="order-history.html">View Orders</a>', 'success');
      } else if (data.data.payment_status === 'rejected') {
        clearInterval(pollInterval);
        showStatus('Payment was rejected. Please contact support.', 'error');
      }
    } catch (error) {
      console.error('Status poll error:', error);
    }
  }, 10000); // Check every 10 seconds
  
  // Stop polling after 5 minutes
  setTimeout(() => clearInterval(pollInterval), 300000);
}

// Helper: Convert file to base64
function toBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });
}

function showLoading(msg) {
  const container = document.querySelector('div[style*="max-width:600px"]');
  if (container) {
    container.innerHTML = `
      <div style="text-align:center;padding:50px;">
        <div style="width:50px;height:50px;border:4px solid #333;border-top:4px solid #667eea;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 20px;"></div>
        <p>${msg || 'Loading...'}</p>
      </div>
      <style>@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>
    `;
  }
}
