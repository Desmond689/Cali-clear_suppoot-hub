// Login & registration UI logic with backend API
// Use existing API_URL or define it (check to avoid redeclaration)
var API_URL = typeof API_URL !== 'undefined' ? API_URL : '/api';

document.addEventListener('DOMContentLoaded', function() {
	// Show/hide password
	function togglePassword(inputId, btnId) {
		const input = document.getElementById(inputId);
		const btn = document.getElementById(btnId);
		if (input && btn) {
			btn.onclick = function() {
				input.type = input.type === 'password' ? 'text' : 'password';
			};
		}
	}
	togglePassword('login-password', 'toggle-login-password');
	togglePassword('register-password', 'toggle-register-password');

	// Helper function to store auth data
	function storeAuthData(data) {
		if (data.data && data.data.access_token) {
			const access = data.data.access_token;
			const refresh = data.data.refresh_token || '';
			const userObj = data.data.user || data.data;
			localStorage.setItem('access_token', access);
			localStorage.setItem('refresh_token', refresh);
			localStorage.setItem('user', JSON.stringify(userObj));
			// Mirror admin keys if user is admin to support admin.html
			if (userObj && userObj.is_admin) {
				localStorage.setItem('admin_token', access);
				localStorage.setItem('admin_user', JSON.stringify(userObj));
			}
		}
	}

	// Helper function to get auth headers
	function getAuthHeaders() {
		const token = localStorage.getItem('access_token');
		return {
			'Content-Type': 'application/json',
			'Authorization': token ? `Bearer ${token}` : ''
		};
	}

	// Check if already logged in - redirect to home
	function checkAuth() {
		const token = localStorage.getItem('access_token');
		const userStr = localStorage.getItem('user');
		if (token && userStr) {
			let user;
			try { user = JSON.parse(userStr); } catch (_) { user = null; }
			if (user && user.is_admin) {
				window.location.href = 'admin.html';
				return;
			}
			window.location.href = 'index.html';
		}
	}

	// Registration form
	const registerForm = document.getElementById('register-form');
	if (registerForm) {
		registerForm.onsubmit = async function(e) {
			e.preventDefault();
			const email = document.getElementById('register-email').value.trim();
			const password = document.getElementById('register-password').value;
			const msgEl = document.getElementById('register-msg');
			const submitBtn = document.getElementById('register-submit');
			
			if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
				msgEl.textContent = '✗ Invalid email format.';
				msgEl.className = 'message error';
				return;
			}
			if (password.length < 6) {
				msgEl.textContent = '✗ Password must be at least 6 characters.';
				msgEl.className = 'message error';
				return;
			}
			
			try {
				submitBtn.disabled = true;
				submitBtn.textContent = 'Creating Account...';
				msgEl.className = '';
				
				const response = await fetch(`${API_URL}/register`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ email, password })
				});
				
				const data = await response.json();
				
				if (response.ok && data.data && data.data.access_token) {
					storeAuthData(data);
					msgEl.textContent = '✓ Account created successfully! Redirecting...';
					msgEl.className = 'message success';
					setTimeout(() => window.location.href = 'index.html', 1200);
				} else {
					msgEl.textContent = '✗ ' + (data.message || 'Registration failed. Try a different email.');
					msgEl.className = 'message error';
					submitBtn.disabled = false;
					submitBtn.textContent = 'Create Account';
				}
			} catch (error) {
				msgEl.textContent = '✗ Network error. Please check your connection and try again.';
				msgEl.className = 'message error';
				submitBtn.disabled = false;
				submitBtn.textContent = 'Create Account';
			}
		};
	}

	// Login form
	const loginForm = document.getElementById('login-form');
	if (loginForm) {
		loginForm.onsubmit = async function(e) {
			e.preventDefault();
			const email = document.getElementById('login-email').value.trim();
			const password = document.getElementById('login-password').value;
			const msgEl = document.getElementById('login-msg');
			const submitBtn = document.getElementById('login-submit');
			
			try {
				submitBtn.disabled = true;
				submitBtn.textContent = 'Signing in...';
				msgEl.className = '';
				
				const response = await fetch(`${API_URL}/login`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ email, password })
				});
				
				const data = await response.json();
				
				if (response.ok && data.data && data.data.access_token) {
					storeAuthData(data);
					msgEl.textContent = '✓ Login successful! Redirecting...';
					msgEl.className = 'message success';
					const user = (data.data && data.data.user) ? data.data.user : null;
					setTimeout(() => {
						if (user && user.is_admin) {
							window.location.href = 'admin.html';
						} else {
							window.location.href = 'index.html';
						}
					}, 1000);
				} else {
					msgEl.textContent = '✗ ' + (data.message || data.error || 'Invalid credentials. Please try again.');
					msgEl.className = 'message error';
					submitBtn.disabled = false;
					submitBtn.textContent = 'Sign In';
				}
			} catch (error) {
				console.error('Login error:', error);
				msgEl.textContent = '✗ Network error. Please check your connection and try again.';
				msgEl.className = 'message error';
				submitBtn.disabled = false;
				submitBtn.textContent = 'Sign In';
			}
		};
	}

	// Logout function (exposed globally)
	window.logout = function() {
		const token = localStorage.getItem('access_token');
		if (token) {
			fetch(`${API_URL}/logout`, {
				method: 'POST',
				headers: getAuthHeaders()
			}).finally(() => {
				localStorage.removeItem('access_token');
				localStorage.removeItem('refresh_token');
				localStorage.removeItem('user');
				window.location.href = 'index.html';
			});
		} else {
			localStorage.removeItem('user');
			window.location.href = 'index.html';
		}
	};

	// Update UI based on auth state
	window.updateAuthUI = function() {
		const user = JSON.parse(localStorage.getItem('user') || 'null');
		const authLinks = document.getElementById('auth-links');
		const userLinks = document.getElementById('user-links');
		const userName = document.getElementById('user-name');
		
		if (authLinks && userLinks) {
			if (user) {
				authLinks.style.display = 'none';
				userLinks.style.display = 'flex';
				if (userName) {
					userName.textContent = user.email ? user.email.split('@')[0] : 'User';
				}
			} else {
				authLinks.style.display = 'flex';
				userLinks.style.display = 'none';
			}
		}
	};

	// Initialize auth UI
	updateAuthUI();

	// Check if on login/register page and already logged in
	if (window.location.pathname.includes('login.html') || 
		window.location.pathname.includes('register.html')) {
		checkAuth();
	}
});
