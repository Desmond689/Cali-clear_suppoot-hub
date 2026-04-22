// Cart logic with backend API
const API_URL = '/api';

let cart = [];
let coupon = null;

async function fetchCart() {
    console.log('[CART] Fetching cart...');
    try {
        const response = await fetch(`${API_URL}/cart`, { 
            credentials: 'include',
            headers: { 'Cache-Control': 'no-cache' }
        });
        
        if (response.ok) {
            const data = await response.json();
            const items = data.data || [];
            console.log('[CART] API returned:', items.length, 'items');
            
            if (items.length > 0) {
                return items.map(item => ({
                    id: item.product_id,
                    product_id: item.product_id,
                    original_id: item.original_id || item.product_id,  // Include original ID for matching
                    name: item.name,
                    price: item.price,
                    quantity: item.quantity,
                    qty: item.quantity,
                    image_url: item.image_url
                }));
            }
        }
    } catch (error) {
        console.log('[CART] Backend error, using localStorage:', error);
    }
    
    // Fallback to localStorage
    const localCart = localStorage.getItem('cart');
    console.log('[CART] LocalStorage cart:', localCart);
    if (localCart) {
        try {
            const items = JSON.parse(localCart);
            return items.map(item => ({
                id: item.id || item.product_id,
                product_id: item.id || item.product_id,
                name: item.name,
                price: item.price,
                quantity: item.qty || item.quantity || 1,
                qty: item.qty || item.quantity || 1,
                image_url: item.image_url || item.image
            }));
        } catch (e) {
            console.error('[CART] Error parsing localStorage:', e);
        }
    }
    return [];
}

async function syncCartToLocalStorage() {
    const localCart = cart.map(item => ({
        id: item.id || item.product_id,
        product_id: item.id || item.product_id,
        name: item.name,
        price: item.price,
        qty: item.quantity,
        quantity: item.quantity,
        image_url: item.image_url
    }));
    localStorage.setItem('cart', JSON.stringify(localCart));
    console.log('[CART] Synced to localStorage:', localCart.length, 'items');
}

async function updateCartItem(productId, quantity) {
    console.log('[CART] Updating item:', productId, 'qty:', quantity);
    try {
        const response = await fetch(`${API_URL}/cart/update`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId, quantity }),
            credentials: 'include'
        });
        if (response.ok) {
            await loadCart();
            await syncCartToLocalStorage();
        }
    } catch (error) {
        console.error('[CART] Error updating cart:', error);
    }
}

async function removeFromCart(productId) {
    console.log('[CART] Removing item:', productId);
    try {
        const response = await fetch(`${API_URL}/cart/remove`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_id: productId }),
            credentials: 'include'
        });
        if (response.ok) {
            showToast('Removed from cart');
            await loadCart();
            await syncCartToLocalStorage();
        } else {
            // If API fails, try removing from local state
            cart = cart.filter(item => item.product_id !== productId);
            showToast('Removed from cart');
            renderCart();
            syncCartToLocalStorage();
        }
    } catch (error) {
        console.error('[CART] Error removing from cart:', error);
        // Fallback: remove from local state
        cart = cart.filter(item => item.product_id !== productId);
        showToast('Removed from cart');
        renderCart();
        syncCartToLocalStorage();
    }
}

async function loadCart() {
    console.log('[CART] Loading cart...');
    cart = await fetchCart();
    console.log('[CART] Final cart data:', cart.length, 'items');
    renderCart();
}

function renderCart() {
    const tbody = document.querySelector('#cart-table tbody');
    console.log('[CART] Rendering cart, tbody found:', !!tbody);
    
    if (!cart || cart.length === 0) {
        console.log('[CART] Cart is empty');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="5">Your cart is empty. <a href="shop.html">Continue shopping</a></td></tr>';
        }
        updateCartCount(0);
        updateSummary(0);
        return;
    }
    
    console.log('[CART] Rendering', cart.length, 'items');
    
    if (tbody) {
        tbody.innerHTML = '';
        
        cart.forEach(item => {
            const tr = document.createElement('tr');
            tr.setAttribute('data-product-id', item.product_id);
            tr.innerHTML = `
                <td class="cart-product">
                    <img src="${item.image_url}" alt="${item.name}" onerror="this.src='assets/images/products/default.png'">
                    <span>${item.name}</span>
                </td>
                <td>$${Number(item.price).toFixed(2)}</td>
                <td>
                    <input type="number" min="1" max="${item.stock || 99}" value="${item.quantity}" data-id="${item.product_id}" class="quantity-input cart-qty-input">
                </td>
                <td>$${(Number(item.price) * item.quantity).toFixed(2)}</td>
                <td>
                    <button class="remove-btn cart-item-remove" data-id="${item.product_id}">Remove</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        // Attach event listeners directly to each remove button
        document.querySelectorAll('.cart-item-remove').forEach(btn => {
            btn.onclick = function() {
                const id = +this.getAttribute('data-id');
                console.log('[CART] Remove button clicked for product:', id);
                removeFromCart(id);
            };
        });
        
        // Attach event listeners to quantity inputs
        document.querySelectorAll('.cart-qty-input').forEach(input => {
            input.onchange = async function() {
                const id = +this.getAttribute('data-id');
                let qty = Math.max(1, Math.min(+this.value, 99));
                console.log('[CART] Quantity changed:', id, '->', qty);
                await updateCartItem(id, qty);
            };
        });
        
        console.log('[CART] Event listeners attached to', cart.length, 'items');
    }
    
    const subtotal = cart.reduce((sum, item) => sum + (Number(item.price) * item.quantity), 0);
    updateSummary(subtotal);
}

function updateSummary(subtotal) {
    let discount = 0;
    if (coupon === 'SALE10') discount = subtotal * 0.10;
    let shipping = subtotal > 50 ? 0 : 5;
    let total = subtotal - discount + shipping;
    let tax = subtotal * 0.10;
    
    const subtotalEl = document.getElementById('subtotal');
    const taxEl = document.getElementById('tax');
    const totalEl = document.getElementById('total');
    const shippingEl = document.getElementById('shipping');
    
    if (subtotalEl) subtotalEl.textContent = '$' + subtotal.toFixed(2);
    if (taxEl) taxEl.textContent = '$' + tax.toFixed(2);
    if (totalEl) totalEl.textContent = '$' + total.toFixed(2);
    if (shippingEl) shippingEl.textContent = '$' + shipping.toFixed(2);
    
    updateCartCount(cart.reduce((sum, item) => sum + item.quantity, 0));
}

function updateCartCount(count) {
    const cartCount = document.getElementById('cart-count');
    if (cartCount) cartCount.textContent = count;
    // Also update navbar cart count
    const navbarCartCount = document.getElementById('cart-count');
    if (navbarCartCount) navbarCartCount.textContent = count;
}

// Coupon
function applyCoupon() {
    const couponInput = document.getElementById('coupon-code');
    const applyCouponBtn = document.getElementById('apply-coupon');
    const couponMsg = document.getElementById('coupon-msg');
    
    if (!couponInput || !couponMsg) return;
    
    const code = (couponInput.value || '').trim().toUpperCase();
    if (code === 'SALE10') {
        coupon = code;
        couponMsg.textContent = '10% discount applied!';
        couponMsg.style.color = 'green';
    } else {
        couponMsg.textContent = 'Invalid coupon code';
        couponMsg.style.color = 'red';
    }
    const subtotal = cart.reduce((sum, item) => sum + (Number(item.price) * item.quantity), 0);
    updateSummary(subtotal);
}

// Initialize on DOM load - but only if we're on the cart page
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('cart-table')) {
        console.log('[CART] Cart page detected, initializing...');
        loadCart();
    }
});
