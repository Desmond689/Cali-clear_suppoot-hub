// Shop page: product rendering, filters, sort, search, pagination, quick view modal
const API_URL = '/api';
document.addEventListener('DOMContentLoaded', function() {
	const grid = document.getElementById('shop-products-grid');
	const pagination = document.getElementById('pagination');
	const searchBar = document.getElementById('search-bar');
	const sortSelect = document.getElementById('sort-select');
	const filterCategory = document.getElementById('filter-category');
	const filterPrice = document.getElementById('filter-price');
	const priceValue = document.getElementById('price-value');
	const filterRating = document.getElementById('filter-rating');
	const filterPopularity = document.getElementById('filter-popularity');
	const clearFilters = document.getElementById('clear-filters');
	const quickViewModal = document.getElementById('quick-view-modal');
	let allProducts = [], filtered = [], page = 1, perPage = 8;

	// Fetch products - try API first, fallback to JSON
	fetch(`${API_URL}/products`)
		.then(r => r.ok ? r.json() : Promise.reject('API not available'))
		.then(data => {
			allProducts = data.data?.products || [];
			filterAndRender();
		})
		.catch(() => {
			fetch('data/products.json')
				.then(r => r.json())
				.then(products => {
					allProducts = products;
					filterAndRender();
				});
		});

	// Filtering, sorting, searching
	function filterAndRender() {
		let q = (searchBar?.value || '').toLowerCase();
		let cat = filterCategory?.value || 'all';
		let price = filterPrice ? +filterPrice.value : 200;
		let rating = filterRating?.value || 'all';
		let pop = filterPopularity?.value || 'all';
		let sort = sortSelect?.value || 'popularity';
		filtered = allProducts.filter(p => {
			let match = true;
			if (q && !(p.name.toLowerCase().includes(q) || (p.shortDesc||'').toLowerCase().includes(q))) match = false;
			if (cat !== 'all' && p.category !== cat) match = false;
			if (price && p.price > price) match = false;
			if (rating !== 'all' && (p.rating||4) < +rating) match = false;
			if (pop !== 'all') {
				if (pop === 'bestseller' && !p.bestSeller) match = false;
				if (pop === 'new' && p.badge !== 'New') match = false;
				if (pop === 'hot' && p.badge !== 'Hot') match = false;
				if (pop === 'sale' && p.badge !== 'Sale') match = false;
			}
			return match;
		});
		// Sort
		if (sort === 'price-asc') filtered.sort((a,b)=>a.price-b.price);
		else if (sort === 'price-desc') filtered.sort((a,b)=>b.price-a.price);
		else if (sort === 'name-asc') filtered.sort((a,b)=>a.name.localeCompare(b.name));
		else if (sort === 'name-desc') filtered.sort((a,b)=>b.name.localeCompare(a.name));
		else filtered.sort((a,b)=>((b.bestSeller?1:0)-(a.bestSeller?1:0)));
		renderProducts();
		renderPagination();
	}

	function renderProducts() {
		if (!grid) return;
		let start = (page-1)*perPage, end = start+perPage;
		let show = filtered.slice(start, end);
		grid.innerHTML = show.map(product => `
			<div class="product-card">
				<div class="product-img-wrap">
					<img src="${product.image}" alt="${product.name}">
					${product.badge ? `<span class="badge badge-${product.badge.toLowerCase()}">${product.badge}</span>` : ''}
				</div>
				<div class="product-info">
					<h3>${product.name}</h3>
					<div class="product-rating">${'★'.repeat(product.rating||4)}${'☆'.repeat(5-(product.rating||4))}</div>
					<div class="product-price">$${product.price.toFixed(2)}</div>
					<p class="product-desc">${product.shortDesc||''}</p>
					<button class="btn add-to-cart" data-id="${product.id}">Add to Cart</button>
					<button class="btn quick-view" data-id="${product.id}">Quick View</button>
				</div>
			</div>
		`).join('');
	}

	function renderPagination() {
		if (!pagination) return;
		let total = Math.ceil(filtered.length/perPage);
		if (total <= 1) { pagination.innerHTML = ''; return; }
		pagination.innerHTML = Array.from({length: total}, (_,i) =>
			`<button class="${i+1===page?'active':''}" data-page="${i+1}">${i+1}</button>`
		).join('');
	}

	// Event listeners
	if (searchBar) searchBar.addEventListener('input', ()=>{page=1;filterAndRender();});
	if (sortSelect) sortSelect.addEventListener('change', ()=>{page=1;filterAndRender();});
	if (filterCategory) filterCategory.addEventListener('change', ()=>{page=1;filterAndRender();});
	if (filterPrice) filterPrice.addEventListener('input', ()=>{
		priceValue.textContent = `$0 - $${filterPrice.value}`;
		page=1;filterAndRender();
	});
	if (filterRating) filterRating.addEventListener('change', ()=>{page=1;filterAndRender();});
	if (filterPopularity) filterPopularity.addEventListener('change', ()=>{page=1;filterAndRender();});
	if (clearFilters) clearFilters.addEventListener('click', ()=>{
		if (filterCategory) filterCategory.value = 'all';
		if (filterPrice) filterPrice.value = 200;
		if (priceValue) priceValue.textContent = '$0 - $200';
		if (filterRating) filterRating.value = 'all';
		if (filterPopularity) filterPopularity.value = 'all';
		if (searchBar) searchBar.value = '';
		if (sortSelect) sortSelect.value = 'popularity';
		page=1;filterAndRender();
	});
	if (pagination) pagination.addEventListener('click', e => {
		if (e.target.tagName === 'BUTTON') {
			page = +e.target.dataset.page;
			renderProducts();
			renderPagination();
			window.scrollTo({top: grid.offsetTop-80, behavior:'smooth'});
		}
	});

	// Quick View Modal (UI only)
	if (grid) grid.addEventListener('click', e => {
		if (e.target.classList.contains('quick-view')) {
			const id = e.target.dataset.id;
			const product = allProducts.find(p=>p.id==id);
			if (product && quickViewModal) {
				quickViewModal.innerHTML = `
					<div>
						<h2>${product.name}</h2>
						<img src="${product.image}" alt="${product.name}" style="max-width:200px;">
						<div class="product-rating">${'★'.repeat(product.rating||4)}${'☆'.repeat(5-(product.rating||4))}</div>
						<div class="product-price">$${product.price.toFixed(2)}</div>
						<p>${product.description||''}</p>
						<button onclick="document.getElementById('quick-view-modal').style.display='none'">Close</button>
					</div>
				`;
				quickViewModal.style.display = 'flex';
			}
		}
	});
	if (quickViewModal) quickViewModal.addEventListener('click', e => {
		if (e.target === quickViewModal) quickViewModal.style.display = 'none';
	});
});
