// Render featured products on home page using backend API
document.addEventListener('DOMContentLoaded', function() {
	const grid = document.getElementById('featured-products-grid');
	if (!grid) return;

	const API_URL = '/api';

	// Fetch products from API
	async function fetchProducts() {
		try {
			const response = await fetch(`${API_URL}/featured`);
			if (!response.ok) throw new Error('API not available');
			const data = await response.json();
			return data.data || [];
		} catch (error) {
			console.warn('API not available, using fallback');
			try {
				const res = await fetch('../data/products.json');
				const data = await res.json();
				return data.filter(p => p.bestSeller).slice(0, 4);
			} catch (e) {
				console.error('Failed to load products');
				return [];
			}
		}
	}

	// Sync item to localStorage
	function syncToLocalStorage(productId, name, price, imageUrl, qty) {
		try {
			let cart = JSON.parse(localStorage.getItem('cart') || '[]');
			const existing = cart.find(item => item.id === productId);
			if (existing) {
				existing.qty = (existing.qty || 1) + qty;
			} else {
				cart.push({
					id: productId,
					qty: qty,
					name: name,
					price: price,
					image_url: imageUrl,
					product_id: productId,
					quantity: qty,
					image: imageUrl
				});
			}
			localStorage.setItem('cart', JSON.stringify(cart));
			console.log('[CART] Synced to localStorage');
		} catch (error) {
			console.error('[CART] Error syncing to localStorage:', error);
		}
	}

	// Add to cart via API
	async function addToCart(productId) {
		try {
			const response = await fetch(`${API_URL}/cart/add`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ product_id: productId, quantity: 1 }),
				credentials: 'include'
			});
			
			if (response.ok) {
				// Find product info for localStorage sync
				const products = await fetchProducts();
				const product = products.find(p => p.id === productId);
				if (product) {
					syncToLocalStorage(productId, product.name, product.price, product.image_url || product.image, 1);
				}
				showToast('Added to cart 🛒', true);
				updateCartCount();
			} else {
				const data = await response.json();
				showToast(data.message || 'Error adding to cart');
			}
		} catch (error) {
			// Fallback to localStorage
			let cart = JSON.parse(localStorage.getItem('cart') || '[]');
			const existing = cart.find(item => item.id === productId);
			if (existing) {
				existing.qty += 1;
			} else {
				cart.push({ id: productId, qty: 1 });
			}
			localStorage.setItem('cart', JSON.stringify(cart));
			showToast('Added to cart 🛒', true);
			updateCartCount();
		}
	}

	// Update cart count
	async function updateCartCount() {
		try {
			const response = await fetch(`${API_URL}/cart`, { credentials: 'include' });
			if (response.ok) {
				const data = await response.json();
				const count = data.data?.reduce((sum, item) => sum + item.quantity, 0) || 0;
				const el = document.getElementById('cart-count');
				if (el) el.textContent = count;
			}
		} catch (error) {
			const cart = JSON.parse(localStorage.getItem('cart') || '[]');
			const count = cart.reduce((sum, item) => sum + (item.qty || 1), 0);
			const el = document.getElementById('cart-count');
			if (el) el.textContent = count;
		}
	}

	// Render products
	async function render() {
		const products = await fetchProducts();
		
		if (products.length === 0) {
			grid.innerHTML = '<p style="text-align:center;color:#888;">No products available</p>';
			return;
		}

		grid.innerHTML = products.map(product => `
			<div class="product-card">
				<div class="product-img-wrap">
					<img src="${product.image_url || product.image}" alt="${product.name}">
				</div>
				<div class="product-info">
					<h3>${product.name}</h3>
					<div class="product-rating">${'★'.repeat(4)}${'☆'.repeat(1)}</div>
					<div class="product-price">$${Number(product.price).toFixed(2)}</div>
					<p class="product-desc">${product.description || ''}</p>
					<button class="btn add-to-cart" data-id="${product.id}" data-name="${product.name}" data-price="${Number(product.price).toFixed(2)}">Add to Cart</button>
				</div>
			</div>
		`).join('');

		// Add click handlers for add to cart buttons
		grid.querySelectorAll('.add-to-cart').forEach(btn => {
			btn.addEventListener('click', function() {
				const productId = parseInt(this.dataset.id);
				addToCart(productId);
			});
		});
	}

	// Initialize
	render();
});
