// Universal Toast Notification
// Supports: showToast(message) or showToast(message, showCartLink)
function showToast(message, showCartLinkOrDuration = false, duration = 2000) {
	// Handle case where second arg is duration (backwards compatibility)
	if (typeof showCartLinkOrDuration === 'number') {
		duration = showCartLinkOrDuration;
		showCartLinkOrDuration = false;
	}
	
	const container = document.getElementById('toast-container');
	if (!container) {
		// Create container if not exists
		const toastContainer = document.createElement('div');
		toastContainer.id = 'toast-container';
		toastContainer.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;';
		document.body.appendChild(toastContainer);
		return showToast(message, showCartLinkOrDuration, duration);
	}
	
	const toast = document.createElement('div');
	// Support HTML content for cart link
	if (showCartLinkOrDuration && typeof showCartLinkOrDuration === 'boolean') {
		toast.innerHTML = message + '<br><a href="cart.html" style="color:#ff6f61;text-decoration:underline;cursor:pointer;margin-top:5px;display:inline-block;">View Cart</a>';
	} else {
		toast.textContent = message;
	}
	toast.style.background = '#222';
	toast.style.color = '#fff';
	toast.style.padding = '10px 20px';
	toast.style.borderRadius = '8px';
	toast.style.marginTop = '10px';
	toast.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
	toast.style.opacity = '0';
	toast.style.transition = 'opacity 0.3s ease';
	toast.style.fontWeight = '600';
	toast.style.letterSpacing = '0.5px';
	container.appendChild(toast);
	setTimeout(() => toast.style.opacity = '1', 50);
	setTimeout(() => {
		toast.style.opacity = '0';
		setTimeout(() => container.removeChild(toast), 300);
	}, duration);
}
