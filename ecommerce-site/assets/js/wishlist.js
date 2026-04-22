// Wishlist logic (localStorage)
document.addEventListener('DOMContentLoaded', function() {
	const itemsDiv = document.getElementById('wishlist-items');
	const emptyDiv = document.getElementById('wishlist-empty');
	if (!itemsDiv || !emptyDiv) return;
	
	let products = [], wishlist = [];
	
	function loadWishlistData() {
		fetch('data/products.json')
			.then(r => r.json())
			.then(data => {
				products = data;
				wishlist = JSON.parse(localStorage.getItem('wishlist')||'[]');
				renderWishlist();
			})
			.catch(err => {
				console.error('Error loading wishlist:', err);
				emptyDiv.style.display = 'block';
			});
	}
	
	function renderWishlist() {
		if (!wishlist.length) {
			itemsDiv.innerHTML = '';
			emptyDiv.style.display = 'block';
			return;
		}
		emptyDiv.style.display = 'none';
		itemsDiv.innerHTML = wishlist.map(item => {
			let p;
			const id = item.id || item;
			p = products.find(pr => String(pr.id) == String(id));
			if (!p) return '';
			return `
				<div class="product-card">
					<button class="remove-btn" data-id="${p.id}" style="float:right;width:auto;padding:5px 10px;">×</button>
					<img src="${p.image || p.image_url}" alt="${p.name}" onerror="this.src='assets/images/logo.png'">
					<h3>${p.name}</h3>
					<p class="price">$${Number(p.price).toFixed(2)}</p>
					<button onclick="window.location='product.html?id=${p.id}'">View</button>
				</div>
			`;
		}).join('');
	}
	
	loadWishlistData();
	
	itemsDiv.addEventListener('click', function(e) {
		if (e.target.classList.contains('remove-btn')) {
			const id = e.target.dataset.id;
			wishlist = wishlist.filter(i => String(i.id || i) !== String(id));
			localStorage.setItem('wishlist', JSON.stringify(wishlist));
			renderWishlist();
			showToast('Removed from wishlist!');
		}
	});
});
