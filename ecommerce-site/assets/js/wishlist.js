// Wishlist logic (localStorage)
document.addEventListener('DOMContentLoaded', function() {
	const itemsDiv = document.getElementById('wishlist-items');
	const emptyDiv = document.getElementById('wishlist-empty');
	let products = [], wishlist = [];
	fetch('data/products.json')
		.then(r => r.json())
		.then(data => {
			products = data;
			wishlist = JSON.parse(localStorage.getItem('wishlist')||'[]');
			renderWishlist();
		});
	function renderWishlist() {
		if (!wishlist.length) {
			itemsDiv.innerHTML = '';
			emptyDiv.style.display = 'block';
			return;
		}
		emptyDiv.style.display = 'none';
		itemsDiv.innerHTML = wishlist.map(id => {
			const p = products.find(pr=>pr.id==id);
			if (!p) return '';
			return `
				<div class="wishlist-card">
					<button class="remove-wishlist" data-id="${p.id}">×</button>
					<img src="${p.image}" alt="${p.name}">
					<h3>${p.name}</h3>
					<div class="product-price">$${p.price.toFixed(2)}</div>
					<button class="btn" onclick="window.location='product.html?id=${p.id}'">View</button>
				</div>
			`;
		}).join('');
	}
	itemsDiv.addEventListener('click', function(e) {
		if (e.target.classList.contains('remove-wishlist')) {
			const id = +e.target.dataset.id;
			wishlist = wishlist.filter(i=>i!=id);
			localStorage.setItem('wishlist', JSON.stringify(wishlist));
			renderWishlist();
			showToast('Removed from wishlist!');
		}
	});
});
