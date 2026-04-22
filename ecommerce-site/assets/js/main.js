// Main JavaScript - Navbar and common functionality

// Global error handler to avoid entire site JS failure
window.onerror = function(message, source, lineno, colno, error) {
	console.error('Global JS error:', {message, source, lineno, colno, error});
	// If critical code error, show user message at top
	try {
		const warning = document.createElement('div');
		warning.style.position = 'fixed';
		warning.style.top = '0';
		warning.style.left = '0';
		warning.style.right = '0';
		warning.style.background = '#b00020';
		warning.style.color = '#fff';
		warning.style.padding = '8px 12px';
		warning.style.zIndex = '10000';
		warning.style.fontSize = '13px';
		warning.textContent = 'Site JS error occurred, reloading support scripts...';
		document.body.appendChild(warning);
		setTimeout(() => warning.remove(), 4000);
	} catch (_) {}
	return false; // keep browser default behavior
};

function setNavbarOpenState(isOpen) {
	const links = document.getElementById('navbar-links');
	const toggle = document.getElementById('navbar-toggle');
	if (!links || !toggle) return;

	if (isOpen) {
		links.classList.add('active');
		toggle.classList.add('active');
		toggle.setAttribute('aria-expanded', 'true');
		document.body.classList.add('no-scroll');
		const firstLink = links.querySelector('a');
		if (firstLink) firstLink.focus({ preventScroll: true });
	} else {
		links.classList.remove('active');
		toggle.classList.remove('active');
		toggle.setAttribute('aria-expanded', 'false');
		document.body.classList.remove('no-scroll');
	}
}

function injectComponent(id, url) {
	const placeholder = document.getElementById(id);
	if (!placeholder) return Promise.resolve(null);

	return fetch(url)
		.then(response => {
			if (!response.ok) throw new Error(`${url} responded ${response.status}`);
			return response.text();
		})
		.then(html => {
			placeholder.innerHTML = html;
			return html;
		})
		.catch(err => {
			console.warn(`Could not inject ${url}:`, err);
			return null;
		});
}

function loadNavbarAndFooter() {
	const tasks = [];

	if (document.getElementById('navbar-placeholder')) {
		tasks.push(injectComponent('navbar-placeholder', 'components/navbar.html').then(() => setupNavbarToggle()));
	}

	if (document.getElementById('footer-placeholder')) {
		tasks.push(injectComponent('footer-placeholder', 'components/footer.html').then(() => {
			if (!document.getElementById('chatbot-script')) {
				const s = document.createElement('script');
				s.id = 'chatbot-script';
				s.src = 'assets/js/chatbot.js';
				s.onload = () => { if (typeof initChat === 'function') initChat(); };
				document.body.appendChild(s);
			} else if (typeof initChat === 'function') {
				initChat();
			}
		}));
	}

	return Promise.all(tasks);
}

function ensureFooterAtBottom() {
	const footer = document.getElementById('footer-placeholder');
	if (!footer) return;
	if (footer.parentElement !== document.body || document.body.lastElementChild !== footer) {
		footer.remove();
		document.body.appendChild(footer);
	}
}

function createPageFallbackContent() {
	const path = window.location.pathname.split('/').pop();
	const page = path || 'index.html';
	const hasMain = document.querySelector('main, .shop-container, .product-container, .cart-container, .page-container');
	if (hasMain) return;

	let content = '';
	switch (page) {
		case 'shop.html':
			content = '<section class="section"><h2>Shop</h2><div id="products-grid" class="products-grid"></div></section>';
			break;
		case 'product.html':
			content = '<div class="product-container"><div class="product-images"><img id="main-product-img" class="main" src="assets/images/logo.png" alt="Product"></div><div class="card"><h1 id="product-name">Product Name</h1><div class="price" id="product-price">$0.00</div><p class="description" id="product-desc">Product description will appear here.</p><div class="actions"><button id="add-to-cart" class="add-cart">Add to Cart</button><button id="add-to-wishlist" class="add-wishlist">Add to Wishlist</button></div></div></div>';
			break;
		case 'wishlist.html':
			content = '<section class="section"><h2>Wishlist</h2><div id="wishlist-items" class="wishlist-grid"></div><p id="wishlist-empty">Your wishlist is empty.</p></section>';
			break;
		case 'order-history.html':
			content = '<section class="section"><h2>My Orders</h2><div id="orders-list" class="orders-list">No orders yet.</div></section>';
			break;
		case 'about.html':
			content = '<section class="section"><h2>About us</h2><p>Welcome to Cali Clear. We offer premium products with fast delivery.</p></section>';
			break;
		case 'contact.html':
			content = '<section class="section"><h2>Contact</h2><form id="contactForm"><input type="text" id="contact-name" placeholder="Your Name" required><input type="email" id="contact-email" placeholder="Your Email" required><textarea id="contact-message" placeholder="Message" required></textarea><button type="submit">Send Message</button></form></section>';
			break;
		case 'cart.html':
			content = '<section class="section"><h2>Shopping Cart</h2><table id="cart-table" class="cart-table"><thead><tr><th>Product</th><th>Price</th><th>Qty</th><th>Total</th><th>Action</th></tr></thead><tbody></tbody></table><div class="cart-summary"><p>Subtotal: <span id="subtotal">$0.00</span></p><p>Tax: <span id="tax">$0.00</span></p><p>Total: <span id="total">$0.00</span></p></div></section>';
			break;
		default:
			return;
	}

	const main = document.createElement('main');
	main.id = 'page-fallback-content';
	main.innerHTML = content;

	const footer = document.getElementById('footer-placeholder');
	if (footer) {
		footer.insertAdjacentElement('beforebegin', main);
	} else {
		document.body.appendChild(main);
	}
}

// Navbar toggle function - exposed globally for inline handlers
function toggleNavbar() {
	const toggle = document.getElementById('navbar-toggle');
	if (!toggle) {
		console.log('Navbar toggle element not found');
		return;
	}
	const isOpen = toggle.getAttribute('aria-expanded') === 'true';
	setNavbarOpenState(!isOpen);
}

// Function to setup navbar toggle - can be called after navbar is loaded
function setupNavbarToggle() {
	const toggle = document.getElementById('navbar-toggle');
	const links = document.getElementById('navbar-links');
	
	// If elements don't exist yet, return false
	if (!toggle || !links) {
		return false;
	}
	
	// Check if already setup
	if (toggle.dataset.setup === 'true') {
		return true;
	}
	
	toggle.dataset.setup = 'true';

	// Ensure ARIA attributes exist
	if (!toggle.hasAttribute('aria-expanded')) {
		toggle.setAttribute('aria-expanded', 'false');
	}
	if (!toggle.hasAttribute('aria-controls')) {
		toggle.setAttribute('aria-controls', 'navbar-links');
	}

	// Remove inline onclick to avoid double-firing
	toggle.removeAttribute('onclick');
	
	// Add click event listener
	toggle.addEventListener('click', function(e) {
		e.preventDefault();
		toggleNavbar();
	});

	// Close when clicking a nav link (mobile)
	links.querySelectorAll('a').forEach(function(a) {
		a.addEventListener('click', function() {
			if (toggle.getAttribute('aria-expanded') === 'true') {
				links.classList.remove('active');
				toggle.classList.remove('active');
				toggle.setAttribute('aria-expanded', 'false');
				document.body.classList.remove('no-scroll');
			}
		});
	});

	// Close on outside click
	if (!document.body.dataset.navOutsideListener) {
		document.addEventListener('click', function(e) {
			const toggleEl = document.getElementById('navbar-toggle');
			const linksEl = document.getElementById('navbar-links');
			if (!toggleEl || !linksEl) return;
			if (toggleEl.contains(e.target) || linksEl.contains(e.target)) return;
			if (toggleEl.getAttribute('aria-expanded') === 'true') {
				linksEl.classList.remove('active');
				toggleEl.classList.remove('active');
				toggleEl.setAttribute('aria-expanded', 'false');
				document.body.classList.remove('no-scroll');
			}
		});
		document.body.dataset.navOutsideListener = 'true';
	}

	// Close on Escape key
	if (!document.body.dataset.navEscapeListener) {
		document.addEventListener('keydown', function(e) {
			if (e.key === 'Escape') {
				const toggleEl = document.getElementById('navbar-toggle');
				const linksEl = document.getElementById('navbar-links');
				if (!toggleEl || !linksEl) return;
				if (toggleEl.getAttribute('aria-expanded') === 'true') {
					linksEl.classList.remove('active');
					toggleEl.classList.remove('active');
					toggleEl.setAttribute('aria-expanded', 'false');
					document.body.classList.remove('no-scroll');
				}
			}
		});
		document.body.dataset.navEscapeListener = 'true';
	}

	return true;
}

// Setup navbar/footer and content when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
	loadNavbarAndFooter().finally(() => {
		createPageFallbackContent();
		ensureFooterAtBottom();
	});

	// Try immediately and with delays to catch dynamically loaded navbar
	setupNavbarToggle();
	setTimeout(setupNavbarToggle, 100);
	setTimeout(setupNavbarToggle, 300);
	setTimeout(setupNavbarToggle, 500);
	setTimeout(setupNavbarToggle, 1000);

	// Watch for navbar being loaded dynamically via fetch
	const navbarPlaceholder = document.getElementById('navbar-placeholder');
	if (navbarPlaceholder) {
		const observer = new MutationObserver(function(mutations) {
			mutations.forEach(function(mutation) {
				if (mutation.addedNodes.length > 0) {
					// Give time for the HTML to be parsed
					setTimeout(setupNavbarToggle, 50);
					setTimeout(setupNavbarToggle, 200);
				}
			});
		});
		observer.observe(navbarPlaceholder, { childList: true });
	}

	// Also check periodically in case navbar loads after page load
	let attempts = 0;
	const checkInterval = setInterval(function() {
		attempts++;
		if (setupNavbarToggle() || attempts >= 10) {
			clearInterval(checkInterval);
		}
	}, 200);

	// Smooth scroll for anchor links
	document.querySelectorAll('a[href^="#"]').forEach(function(link) {
		link.addEventListener('click', function(e) {
			const target = document.querySelector(this.getAttribute('href'));
			if (target) {
				e.preventDefault();
				target.scrollIntoView({ behavior: 'smooth' });
			}
		});
	});

	// Newsletter form validation (footer and main page)
	function handleNewsletterForm(formId, msgId) {
		const form = document.getElementById(formId);
		const msg = document.getElementById(msgId);
		if (form && msg) {
			form.addEventListener('submit', function(e) {
				e.preventDefault();
				const email = form.querySelector('input[type="email"]').value;
				if (/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
					msg.textContent = 'Thank you for subscribing!';
					msg.style.color = 'green';
					form.reset();
				} else {
					msg.textContent = 'Please enter a valid email.';
					msg.style.color = 'red';
				}
			});
		}
	}
	handleNewsletterForm('newsletter-form', 'newsletter-msg');
	handleNewsletterForm('newsletter-form-main', 'newsletter-main-msg');

	// Update auth UI if function exists
	if (typeof updateAuthUI === 'function') {
		updateAuthUI();
	}
});
