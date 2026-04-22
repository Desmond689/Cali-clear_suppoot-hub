// Admin Payment Functions - Add to admin.html
// This file provides the missing loadPayments, verifyPayment, and related functions

var currentSelectedPayment = null;
var currentPaymentPage = 1;

async function loadPayments() {
  var tbody = document.getElementById('payments-table-body');
  if (!tbody) return;
  
  tbody.innerHTML = '<tr><td colspan="9" class="loading"><i class="fas fa-spinner"></i> Loading payments...</td></tr>';
  
  try {
    var search = document.getElementById('payment-search')?.value || '';
    var status = document.getElementById('payment-status-filter')?.value || '';
    var page = currentPaymentPage;
    
    var endpoint = '/api/minipay/admin/pending?page=' + page + '&per_page=20';
    if (search) endpoint += '&search=' + encodeURIComponent(search);
    if (status) endpoint += '&status=' + status;
    
    var response = await fetch(endpoint);
    var data = await response.json();
    var payments = data.payments || [];
    
    if (payments.length === 0) {
      tbody.innerHTML = '<tr><td colspan="9" class="loading">No pending payments found</td></tr>';
      return;
    }
    
    var html = '';
    for (var i = 0; i < payments.length; i++) {
      var payment = payments[i];
      var statusClass = 'status-' + (payment.status || 'pending');
      var deadline = payment.payment_deadline ? new Date(payment.payment_deadline).toLocaleString() : 'N/A';
      var submitted = payment.submitted_at ? new Date(payment.submitted_at).toLocaleString() : 'N/A';
      
      html += '<tr>';
      html += '<td>#' + payment.order_id + '</td>';
      html += '<td>' + (payment.customer_name || payment.email || 'N/A') + '</td>';
      html += '<td>$' + parseFloat(payment.order_total || 0).toFixed(2) + '</td>';
      html += '<td>$' + parseFloat(payment.amount_sent || 0).toFixed(2) + '</td>';
      html += '<td><span style="font-size:11px;">' + (payment.transaction_ref || '-') + '</span></td>';
      html += '<td>' + submitted + '</td>';
      html += '<td>' + deadline + '</td>';
      html += '<td><span class="status ' + statusClass + '">' + (payment.status || 'pending') + '</span></td>';
      html += '<td>';
      html += '<button class="btn btn-primary btn-sm" title="View Details" onclick="openPaymentModal(\'' + payment.order_id + '\')"><i class="fas fa-eye"></i></button>';
      if (payment.has_screenshot) {
        html += ' <button class="btn btn-info btn-sm" title="View Screenshot" onclick="viewPaymentScreenshot(\'' + payment.order_id + '\')"><i class="fas fa-image"></i></button>';
      }
      html += '</td>';
      html += '</tr>';
    }
    tbody.innerHTML = html;
    
    // Render pagination
    var totalPages = data.pages || 1;
    var currentPage = data.current_page || 1;
    var paginationHtml = '';
    if (totalPages > 1) {
      paginationHtml += '<button class="btn btn-sm" onclick="currentPaymentPage--; loadPayments();">Prev</button>';
      paginationHtml += '<span style="margin: 0 10px;">Page ' + currentPage + ' of ' + totalPages + '</span>';
      paginationHtml += '<button class="btn btn-sm" onclick="currentPaymentPage++; loadPayments();">Next</button>';
    }
    var paginationEl = document.getElementById('payments-pagination');
    if (paginationEl) paginationEl.innerHTML = paginationHtml;
    
  } catch (error) {
    console.error('Error loading payments:', error);
    tbody.innerHTML = '<tr><td colspan="9" class="loading">Error loading payments</td></tr>';
  }
}

async function loadPaymentStats() {
  try {
    var endpoint = '/api/minipay/admin/analytics?days=30';
    var response = await fetch(endpoint);
    var data = await response.json();
    var stats = data.data || {};
    
    document.getElementById('stat-pending-payments').textContent = stats.pending_count || 0;
    document.getElementById('stat-verified-payments').textContent = stats.total_payments || 0;
    document.getElementById('stat-rejected-payments').textContent = stats.rejected_count || 0;
    document.getElementById('stat-payment-revenue').textContent = '$' + (stats.total_revenue || 0).toFixed(2);
    
  } catch (error) {
    console.error('Error loading payment stats:', error);
  }
}

async function openPaymentModal(orderId) {
  try {
    var endpoint = '/api/minipay/order/' + orderId;
    var response = await fetch(endpoint);
    var data = await response.json();
    var order = data.data;
    
    currentSelectedPayment = orderId;
    
    var content = document.getElementById('payment-details-content');
    content.innerHTML = 
      '<div style="margin-bottom: 15px;">' +
        '<label style="color: #888; font-size: 12px;">Order ID</label>' +
        '<div style="font-size: 18px; font-weight: bold;">' + order.order_id + '</div>' +
      '</div>' +
      '<div style="margin-bottom: 15px;">' +
        '<label style="color: #888; font-size: 12px;">Customer</label>' +
        '<div>' + (order.customer_name || 'N/A') + '</div>' +
        '<div style="color: #888;">' + (order.email || 'N/A') + '</div>' +
      '</div>' +
      '<div style="margin-bottom: 15px;">' +
        '<label style="color: #888; font-size: 12px;">Order Total</label>' +
        '<div style="font-size: 24px; color: #ff6f61; font-weight: bold;">$' + parseFloat(order.total).toFixed(2) + '</div>' +
      '</div>' +
      '<div style="margin-bottom: 15px;">' +
        '<label style="color: #888; font-size: 12px;">Amount Sent</label>' +
        '<div style="font-size: 18px; color: #28a745;">$' + (order.confirmations && order.confirmations[0] ? parseFloat(order.confirmations[0].amount_sent).toFixed(2) : '0.00') + '</div>' +
      '</div>' +
      '<div style="margin-bottom: 15px;">' +
        '<label style="color: #888; font-size: 12px;">Transaction Reference</label>' +
        '<div style="font-family: monospace;">' + (order.confirmations && order.confirmations[0] ? order.confirmations[0].transaction_ref : 'N/A') + '</div>' +
      '</div>' +
      '<div style="margin-bottom: 15px;">' +
        '<label style="color: #888; font-size: 12px;">Payment Status</label>' +
        '<div><span class="status status-' + order.payment_status + '">' + (order.payment_status || 'none') + '</span></div>' +
      '</div>' +
      '<div style="margin-bottom: 15px;">' +
        '<label style="color: #888; font-size: 12px;">Payment Deadline</label>' +
        '<div>' + (order.payment_deadline ? new Date(order.payment_deadline).toLocaleString() : 'N/A') + '</div>' +
      '</div>';
    
    document.getElementById('payment-modal').style.display = 'flex';
    
  } catch (error) {
    console.error('Error loading payment details:', error);
    showNotification('Error loading payment details', 'error');
  }
}

function closePaymentModal() {
  document.getElementById('payment-modal').style.display = 'none';
  currentSelectedPayment = null;
}

async function verifyPayment() {
  if (!currentSelectedPayment) return;
  
  try {
    var endpoint = '/api/minipay/admin/verify/' + currentSelectedPayment;
    var response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'verify' })
    });
    
    var data = await response.json();
    
    if (response.ok) {
      showNotification('Payment verified successfully!', 'success');
      closePaymentModal();
      loadPayments();
      loadPaymentStats();
    } else {
      throw new Error(data.message || 'Failed to verify payment');
    }
  } catch (error) {
    console.error('Error verifying payment:', error);
    showNotification('Error: ' + (error.message || 'Failed to verify payment'), 'error');
  }
}

async function rejectPayment() {
  if (!currentSelectedPayment) return;
  
  var reason = prompt('Please enter reason for rejection:');
  if (reason === null) return;
  
  try {
    var endpoint = '/api/minipay/admin/verify/' + currentSelectedPayment;
    var response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'reject', reason: reason || 'Payment could not be verified' })
    });
    
    var data = await response.json();
    
    if (response.ok) {
      showNotification('Payment rejected', 'success');
      closePaymentModal();
      loadPayments();
      loadPaymentStats();
    } else {
      throw new Error(data.message || 'Failed to reject payment');
    }
  } catch (error) {
    console.error('Error rejecting payment:', error);
    showNotification('Error: ' + (error.message || 'Failed to reject payment'), 'error');
  }
}

async function viewPaymentScreenshot(orderId) {
  try {
    var endpoint = '/api/minipay/admin/screenshot/' + orderId;
    window.open(endpoint, '_blank');
  } catch (error) {
    console.error('Error viewing screenshot:', error);
    showNotification('Error loading screenshot', 'error');
  }
}

// Auto-load payments when section is shown
window.addEventListener('DOMContentLoaded', function() {
  // Override the section change handler to load payments
  var originalShowSection = window.showSection;
  if (typeof originalShowSection === 'function') {
    window.showSection = function(sectionId) {
      originalShowSection(sectionId);
      if (sectionId === 'payments') {
        loadPayments();
        loadPaymentStats();
      }
    };
  }
});
