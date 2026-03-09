// Main JavaScript - Navbar and common functionality

// Navbar toggle function - exposed globally for inline handlers
function toggleNavbar() {
	const links = document.getElementById('navbar-links');
	const toggle = document.getElementById('navbar-toggle');
	if (!links || !toggle) return;

	// Ensure accessibility attributes
	if (!toggle.hasAttribute('aria-controls')) {
		toggle.setAttribute('aria-controls', 'navbar-links');
	}

	const isOpen = toggle.getAttribute('aria-expanded') === 'true';
	if (isOpen) {
		links.classList.remove('active');
		toggle.classList.remove('active');
		toggle.setAttribute('aria-expanded', 'false');
		document.body.classList.remove('no-scroll');
	} else {
		links.classList.add('active');
		toggle.classList.add('active');
		toggle.setAttribute('aria-expanded', 'true');
		document.body.classList.add('no-scroll');
		// Focus first focusable item for better keyboard navigation
		const firstLink = links.querySelector('a, button');
		if (firstLink) firstLink.focus({ preventScroll: true });
	}
}

// Function to setup navbar toggle - can be called after navbar is loaded
function setupNavbarToggle() {
	const toggle = document.getElementById('navbar-toggle');
	const links = document.getElementById('navbar-links');
	if (toggle && links) {
		// Check if already setup
		if (toggle.dataset.setup === 'true') return true;
		toggle.dataset.setup = 'true';

		// Ensure ARIA attribute exists
		if (!toggle.hasAttribute('aria-expanded')) toggle.setAttribute('aria-expanded', 'false');

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
				}
			});
		});

		// Close on outside click (only add once)
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
					}
				}
			});
			document.body.dataset.navEscapeListener = 'true';
		}

		return true;
	}
	return false;
}

// Setup navbar when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
	// Try immediately and with delays
	setupNavbarToggle();
	setTimeout(setupNavbarToggle, 100);
	setTimeout(setupNavbarToggle, 500);
	setTimeout(setupNavbarToggle, 1000);

	// Watch for navbar being loaded dynamically
	const navbarPlaceholder = document.getElementById('navbar-placeholder');
	if (navbarPlaceholder) {
		const observer = new MutationObserver(function(mutations) {
			mutations.forEach(function(mutation) {
				if (mutation.addedNodes.length > 0) {
					setTimeout(setupNavbarToggle, 50);
				}
			});
		});
		observer.observe(navbarPlaceholder, { childList: true });
	}

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
