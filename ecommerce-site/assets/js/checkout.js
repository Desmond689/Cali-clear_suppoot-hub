// Checkout form & payment UI logic
document.addEventListener('DOMContentLoaded', function() {
	const form = document.getElementById('checkout-form');
	const steps = document.querySelectorAll('.step');
	const stepContents = [
		document.getElementById('step-1'),
		document.getElementById('step-2'),
		document.getElementById('step-3'),
		document.getElementById('step-4')
	];
	let currentStep = 0;
	let cartItems = [];
	
	function showStep(idx) {
		stepContents.forEach((c,i)=>c.style.display=i===idx?'flex':'none');
		steps.forEach((s,i)=>s.classList.toggle('active',i===idx));
		currentStep = idx;
	}
	
	form?.addEventListener('click', function(e) {
		if (e.target.classList.contains('next-step')) {
			if (!validateStep(currentStep)) return;
			showStep(currentStep+1);
		}
		if (e.target.classList.contains('prev-step')) {
			showStep(currentStep-1);
		}
	});
	
	function validateStep(idx) {
		const inputs = stepContents[idx].querySelectorAll('input,select');
		for (let inp of inputs) {
			if (!inp.checkValidity()) { inp.reportValidity(); return false; }
			if (inp.type==='email' && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(inp.value)) { inp.setCustomValidity('Invalid email'); inp.reportValidity(); return false; }
			if (inp.type==='tel' && !/^\+?\d{7,15}$/.test(inp.value.replace(/\D/g,''))) { inp.setCustomValidity('Invalid phone'); inp.reportValidity(); return false; }
			inp.setCustomValidity('');
		}
		return true;
	}
	
	// Only show step-based checkout if steps exist
	if (steps.length > 0) {
		showStep(0);
	}

	// Payment method UI
	const paymentMethod = document.getElementById('payment-method');
	const paymentDetails = document.getElementById('payment-details');
	paymentMethod?.addEventListener('change', renderPaymentDetails);
	
	function renderPaymentDetails() {
		let val = paymentMethod.value;
		if (val==='card') paymentDetails.innerHTML = `
			<input type="text" placeholder="Card Number" required pattern="[0-9]{13,19}">
			<input type="text" placeholder="Name on Card" required>
			<input type="text" placeholder="MM/YY" required pattern="(0[1-9]|1[0-2])\/\d{2}">
			<input type="text" placeholder="CVV" required pattern="\d{3,4}">
		`;
		else if (val==='paypal') paymentDetails.innerHTML = `<button type="button" class="btn">Pay with PayPal</button>`;
		else if (val==='applepay') paymentDetails.innerHTML = `<button type="button" class="btn">Apple Pay</button>`;
		else if (val==='googlepay') paymentDetails.innerHTML = `<button type="button" class="btn">Google Pay</button>`;
		else if (val==='bank') paymentDetails.innerHTML = `<div>Bank transfer instructions will be sent to your email.</div>`;
		else if (val==='giftcard') paymentDetails.innerHTML = `<input type="text" placeholder="Gift Card Code" required>`;
		else paymentDetails.innerHTML = '';
	}
	
	// Only render payment details if payment method exists
	if (paymentMethod) {
		renderPaymentDetails();
	}

	// Fetch cart from API
	async function fetchCartFromAPI() {
		try {
			const response = await fetch('/api/cart', { 
				credentials: 'include',
				headers: { 'Cache-Control': 'no-cache' }
			});
			
			if (response.ok) {
				const data = await response.json();
				return data.data || [];
			}
		} catch (error) {
			console.error('[CHECKOUT] Error fetching cart from API:', error);
		}
		
		// Fallback to localStorage
		const localCart = localStorage.getItem('cart');
		if (localCart) {
			try {
				return JSON.parse(localCart);
			} catch (e) {
				console.error('[CHECKOUT] Error parsing localStorage:', e);
			}
		}
		return [];
	}

	// Order summary - fetch from API
	async function renderOrderSummary() {
		console.log('[CHECKOUT] Rendering order summary...');
		cartItems = await fetchCartFromAPI();
		console.log('[CHECKOUT] Cart items:', cartItems.length);
		
		if (cartItems.length === 0) {
			console.log('[CHECKOUT] Cart is empty');
			const summaryEl = document.getElementById('order-summary');
			if (summaryEl) {
				summaryEl.innerHTML = `
					<div style="text-align:center;color:#888;">Your cart is empty</div>
				`;
			}
			return;
		}
		
		// Fetch products to get prices
		try {
			const productsRes = await fetch('data/products.json');
			const products = await productsRes.json();
			
			let subtotal = 0;
			let itemsHtml = '';
			
			for (const item of cartItems) {
				// Try to find product in API data first, then local JSON
				// Use original_id for matching with products.json
				const matchId = item.original_id || item.product_id;
				let product = products.find(p => String(p.id) == String(matchId));
				
				if (product) {
					const itemTotal = product.price * item.quantity;
					subtotal += itemTotal;
					itemsHtml += `
						<div class="order-item">
							<span>${product.name} x ${item.quantity}</span>
							<span>$${itemTotal.toFixed(2)}</span>
						</div>
					`;
				} else {
					console.log('[CHECKOUT] Product not found for item:', item.product_id);
				}
			}
			
			let shipping = subtotal > 50 ? 0 : 5;
			let total = subtotal + shipping;
			
			// Store order total globally
			window.orderTotal = total;
			
			const summaryEl = document.getElementById('order-summary');
			if (summaryEl) {
				summaryEl.innerHTML = `
					${itemsHtml}
					<hr style="margin:10px 0;border-color:#444;">
					<div class="order-item">
						<span>Subtotal:</span>
						<span>$${subtotal.toFixed(2)}</span>
					</div>
					<div class="order-item">
						<span>Shipping:</span>
						<span>$${shipping.toFixed(2)}</span>
					</div>
					<hr style="margin:10px 0;border-color:#444;">
					<div class="order-item" style="font-weight:bold;font-size:1.1em;">
						<span>Total:</span>
						<span>$${total.toFixed(2)}</span>
					</div>
				`;
			}
		} catch (error) {
			console.error('[CHECKOUT] Error rendering order summary:', error);
		}
	}
	
	// Add event listeners for steps
	if (steps[3]) {
		steps[3]?.addEventListener('click', renderOrderSummary);
	}
	
	// Also render on page load
	renderOrderSummary();

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
	 * Create order via API
	 */
	async function createOrderAPI(orderData) {
		try {
			const response = await fetch('/api/orders', {
				method: 'POST',
				headers: getAuthHeaders(),
				body: JSON.stringify(orderData)
			});
			
			// Check if response is JSON
			const contentType = response.headers.get('content-type');
			if (!contentType || !contentType.includes('application/json')) {
				const text = await response.text();
				throw new Error('Server error: ' + (text.substring(0, 100) || 'Unknown error'));
			}
			
			const data = await response.json();
			
			if (!response.ok) {
				throw new Error(data.message || 'Failed to create order');
			}
			
			return data.data;
		} catch (error) {
			console.error('Create order error:', error);
			throw error;
		}
	}

	/**
	 * Setup MiniPay for order
	 */
	async function setupMiniPay(orderId) {
		try {
			const response = await fetch(`/api/minipay/setup/${orderId}`, {
				method: 'POST',
				headers: getAuthHeaders()
			});
			
			const data = await response.json();
			
			if (!response.ok) {
				console.error('MiniPay setup error:', data);
				return null;
			}
			
			return data.data;
		} catch (error) {
			console.error('MiniPay setup error:', error);
			return null;
		}
	}

	/**
	 * Place order - main order creation function
	 */
	async function placeOrder(formData) {
		const { email, shipping_address, items, total, paymentMethod } = formData;
		
		try {
			// Create order
			const orderData = await createOrderAPI({
				email: email,
				shipping_address: shipping_address,
				items: items,
				total: total,
				payment_method: paymentMethod
			});
			
			// For MiniPay, setup the payment details
			if (paymentMethod === 'minipay') {
				const minipaySetup = await setupMiniPay(orderData.order_id);
				console.log('[CHECKOUT] MiniPay setup result:', minipaySetup);
			}
			
			return {
				success: true,
				order_id: orderData.order_id,
				email: email,
				message: orderData.message,
				payment_method: paymentMethod
			};
		} catch (error) {
			return {
				success: false,
				message: error.message || 'Failed to create order'
			};
		}
	}

	/**
	 * Get cart items from API
	 */
	async function getCartItems() {
		// First try to get from localStorage cart
		const localCart = localStorage.getItem('cart');
		if (localCart) {
			try {
				const cart = JSON.parse(localCart);
				console.log('[CHECKOUT] Local cart:', cart);
				return cart.map(item => ({
					product_id: item.product_id || item.id,
					id: item.product_id || item.id,
					quantity: item.quantity || item.qty || 1,
					price: item.price
				}));
			} catch (e) {
				console.error('[CHECKOUT] Error parsing local cart:', e);
			}
		}
		
		// Fallback to API
		cartItems = await fetchCartFromAPI();
		return cartItems.map(item => ({
			product_id: item.product_id,
			id: item.product_id,
			quantity: item.quantity || item.qty || 1,
			price: item.price
		}));
	}

	/**
	 * Get shipping address from form
	 */
	function getShippingAddress() {
		const address = document.getElementById('address')?.value || '';
		const city = document.getElementById('city')?.value || '';
		const zip = document.getElementById('zip')?.value || '';
		return `${address}, ${city} ${zip}`.trim().replace(/^, |, $/g, '');
	}

	/**
	 * Get email from form
	 */
	function getEmail() {
		return document.getElementById('email')?.value || '';
	}

	/**
	 * Get customer name from form
	 */
	function getName() {
		const name = document.getElementById('fullName')?.value || document.getElementById('name')?.value || '';
		return name.trim();
	}

	/**
	 * Get order total - from renderOrderSummary in checkout.html
	 */
	function getOrderTotal() {
		const totalEl = document.getElementById('total');
		if (totalEl) {
			const text = totalEl.textContent.replace(/[^0-9.]/g, '');
			const value = parseFloat(text);
			if (!isNaN(value)) return value;
		}
		return window.orderTotal || 0;
	}

	/**
	 * Get selected payment method from form
	 */
	function getSelectedPaymentMethod() {
		// Check for radio button selection
		const selected = document.querySelector('input[name="payment_method"]:checked');
		if (selected) return selected.value;
		// Check for global selectedPM (used by inline checkout)
		if (window.selectedPM && window.selectedPM.slug) return window.selectedPM.slug;
		// Fallback
		return 'pending';
	}

	// Place order - main form submission handler
	form?.addEventListener('submit', async function(e) {
		e.preventDefault();
		
		const submitBtn = document.getElementById('placeOrder') || form.querySelector('button[type="submit"]');
		if (submitBtn) {
			submitBtn.disabled = true;
			submitBtn.textContent = 'Processing...';
		}
		
		try {
			const email = getEmail();
			const shipping_address = getShippingAddress();
			const items = await getCartItems();
			const total = getOrderTotal();
			
			console.log('[CHECKOUT] Placing order with', items.length, 'items, total:', total);
			
			if (!email || !shipping_address) {
				throw new Error('Please fill in all required fields');
			}
			
			if (!items || items.length === 0) {
				throw new Error('Your cart is empty');
			}
			
			// Create the order
			const result = await placeOrder({
				email: email,
				shipping_address: shipping_address,
				items: items,
				total: total,
				paymentMethod: getSelectedPaymentMethod()
			});
			
			if (result.success) {
				// Clear cart from API and localStorage
				try {
					await fetch('/api/cart/clear', {
						method: 'DELETE',
						credentials: 'include'
					});
				} catch (err) {
					console.error('[CHECKOUT] Error clearing API cart:', err);
				}
				localStorage.removeItem('cart');
				
				// Update cart count
				const cartCount = document.getElementById('cart-count');
				if (cartCount) cartCount.textContent = '0';
				
				// Store order ID and customer email for order tracking
				localStorage.setItem('lastOrderId', result.order_id);
				if (result.email) {
					localStorage.setItem('user', JSON.stringify({ email: result.email }));
				}
				
				// Check if this is a MiniPay order
				if (result.payment_method === 'minipay') {
					// Show success message
					if (typeof showToast === 'function') {
						showToast('Order created! Redirecting to payment...');
					} else {
						alert('Order created! Redirecting to payment...');
					}
				} else {
					// Show success message and redirect to order success
					if (typeof showToast === 'function') {
						showToast('Order created successfully!');
					} else {
						alert('Order created successfully!');
					}
				}

				const customerName = getName() || 'Guest';
				setTimeout(() => {
					if (typeof openChatForOrder === 'function') {
						openChatForOrder(result.order_id, result.email || email, customerName, getSelectedPaymentMethod(), items.map(item => item.name || item.product_id).join(', '), total);
					}
				}, 500);
			} else {
				throw new Error(result.message);
			}
		} catch (error) {
			if (typeof showToast === 'function') {
				showToast(error.message || 'An error occurred');
			} else {
				alert(error.message || 'An error occurred');
			}
		} finally {
			if (submitBtn) {
				submitBtn.disabled = false;
				submitBtn.textContent = 'Place Order & Pay';
			}
		}
	});

	// Export for use in other modules
	window.CheckoutUtils = {
		placeOrder,
		createOrderAPI,
		getCartItems,
		getShippingAddress,
		getEmail,
		getOrderTotal,
		getSelectedPaymentMethod
	};
});

});
