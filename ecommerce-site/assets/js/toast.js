// Universal Toast Notification
function showToast(message, duration = 2000) {
	const container = document.getElementById('toast-container');
	if (!container) return;
	const toast = document.createElement('div');
	toast.textContent = message;
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
