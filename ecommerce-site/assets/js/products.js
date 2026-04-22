// Products JS - Full Integration with Backend API
// Use existing API_URL or define it (check to avoid redeclaration)
var API_URL = typeof API_URL !== 'undefined' ? API_URL : '/api';

document.addEventListener("DOMContentLoaded", async () => {
  const productId = new URLSearchParams(window.location.search).get("id");
  const isProductPage = !!document.getElementById("main-product-img");
  const isShopPage = window.location.pathname.endsWith("shop.html") || window.location.pathname.endsWith("/shop") || window.location.pathname.endsWith("shop");
  const isHomePage = window.location.pathname.endsWith("index.html") || window.location.pathname === "/" || window.location.pathname === "";

  let allProducts = [];

  // ===== FETCH PRODUCTS FROM BACKEND API OR FALLBACK =====
  try {
    const response = await fetch(`${API_URL}/products`);
    if (response.ok) {
      const data = await response.json();
      allProducts = data.data?.products || [];
      console.log('Loaded products from API:', allProducts.length);
    } else {
      throw new Error('API not available');
    }
  } catch (err) {
    console.log('API not available, using fallback products.json');
    try {
      // Try multiple possible paths for products.json
      let res = await fetch("data/products.json");
      if (!res.ok) {
        res = await fetch("../data/products.json");
      }
      if (!res.ok) {
        res = await fetch("assets/data/products.json");
      }
      if (res.ok) {
        const data = await res.json();
        allProducts = data || [];
        console.log('Loaded products from JSON:', allProducts.length);
      } else {
        throw new Error('Could not load products.json');
      }
    } catch (e) {
      console.error('Failed to load products:', e);
      // Show message to user
      const grid = document.getElementById("products-grid");
      if (grid) {
        grid.innerHTML = '<p style="text-align:center;padding:2rem;">Unable to load products. Please try again later.</p>';
      }
      return;
    }
  }

  // Clean product names
  allProducts.forEach(p => {
    p.cleanName = (p.name || '').replace("Cali Clear Vape - ", "");
    // Map image_url to image for compatibility
    if (!p.image && p.image_url) p.image = p.image_url;
  });

  // ===== PRODUCT PAGE =====
  if (isProductPage) {
    const product = allProducts.find(p => String(p.id) === String(productId)) || allProducts[0];
    if (!product) {
      document.body.innerHTML = "<h2 style='text-align:center'>Product not found</h2>";
      return;
    }
    renderProduct(product);
    renderRelated(allProducts, product);
  }

  // ===== SHOP PAGE =====
  if (isShopPage) {
    console.log('Shop page detected, rendering all products');
    renderProductGrid(allProducts);
  }

  // ===== HOMEPAGE =====
  if (!isShopPage && isHomePage) {
    console.log('Homepage detected, rendering featured products');
    renderProductGrid(allProducts.slice(0, 4));
  }

  updateCartCountUI();
});

  // ===============================
  // RENDER SINGLE PRODUCT
  // ===============================
  function renderProduct(product) {
    setText("product-name", product.name);
    setText("product-desc", product.description || "");
    setText("product-specs", product.specs || "");

    const img = document.getElementById("main-product-img");
    if (img) {
      img.src = product.image_url || product.image || "";
      img.alt = product.name || "";
    }

    const priceEl = document.getElementById("product-price");
    if (priceEl) priceEl.textContent = `$${Number(product.price).toFixed(2)}`;

    const ratingEl = document.getElementById("product-rating");
    const rating = Math.max(0, Math.min(5, product.rating || 4));
    if (ratingEl) ratingEl.innerHTML = "★".repeat(rating) + "☆".repeat(5 - rating);

    const stockEl = document.getElementById("product-stock");
    const inStock = (product.stock ?? 1) > 0;
    if (stockEl) {
      stockEl.textContent = inStock ? "In Stock" : "Out of Stock";
      stockEl.style.color = inStock ? "#43a047" : "#e53935";
    }

    const qtyInput = document.getElementById("qty");
    if (qtyInput) {
      qtyInput.max = product.stock || 99;
      qtyInput.value = 1;
    }

    const addBtn = document.getElementById("add-to-cart");
    if (addBtn) {
      addBtn.disabled = !inStock;
      addBtn.onclick = () => {
        addToCart(product);
      };
    }

    const wishBtn = document.getElementById("add-to-wishlist");
    if (wishBtn) wishBtn.onclick = () => addToWishlist(product);
  }

  // ===============================
  // RENDER RELATED PRODUCTS
  // ===============================
  function renderRelated(products, product) {
    const grid = document.getElementById("related-products-grid");
    if (!grid) return;

    let related = products
      .filter(p => p.id !== product.id && p.category_id === product.category_id)
      .slice(0, 4);

    if (related.length < 4) {
      related = products.filter(p => p.id !== product.id).slice(0, 4);
    }

    grid.innerHTML = related.map(p => `
      <div class="product-card">
        <img src="${p.image_url || p.image}" alt="${p.name}">
        <h4>${p.name}</h4>
        <div class="product-rating">${"★".repeat(p.rating || 4)}${"☆".repeat(5 - (p.rating || 4))}</div>
        <p>$${Number(p.price).toFixed(2)}</p>
        <button class="btn add-to-cart" data-id="${p.id}" data-name="${p.name}" data-price="${Number(p.price).toFixed(2)}">Add to Cart</button>
      </div>
    `).join("");

    // Add to cart event binding for related products
    grid.querySelectorAll('.product-card .add-to-cart').forEach(btn => {
      btn.addEventListener('click', function() {
        const productId = this.dataset.id;
        const product = allProducts.find(prod => String(prod.id) === String(productId));
        if (product) addToCart(product);
      });
    });
  }

  // ===============================
  // RENDER PRODUCT GRID (Homepage)
  // ===============================
  function renderProductGrid(products) {
    const grid = document.getElementById("products-grid");
    if (!grid) {
      console.log('products-grid element not found');
      return;
    }
    
    if (!products || products.length === 0) {
      grid.innerHTML = '<p style="text-align:center;padding:2rem;">No products available.</p>';
      return;
    }

    console.log('Rendering', products.length, 'products');
    grid.innerHTML = products.map(p => {
      // Handle both image and image_url fields
      const imgSrc = p.image_url || p.image || 'assets/images/logo.png';
      const rating = p.rating || 4;
      const name = p.cleanName || p.name || 'Product';
      return `
        <div class="product-card">
          <img src="${imgSrc}" alt="${name}" onerror="this.src='assets/images/logo.png'">
          <h4>${name}</h4>
          <div class="product-rating">${"★".repeat(rating)}${"☆".repeat(5 - rating)}</div>
          <p>${Number(p.price || 0).toFixed(2)}</p>
          <button class="btn add-to-cart" data-id="${p.id}" data-name="${name}" data-price="${Number(p.price || 0).toFixed(2)}">Add to Cart</button>
        </div>
      `;
    }).join("");

    // Add to cart event binding for shop grid
    grid.querySelectorAll('.product-card .add-to-cart').forEach(btn => {
      btn.addEventListener('click', function() {
        const productId = this.dataset.id;
        const product = products.find(prod => String(prod.id) === String(productId));
        if (product) addToCart(product);
      });
    });
  }

  // ===============================
  // CART LOGIC
  // ===============================
  async function addToCart(product) {
    const qty = Math.max(1, Math.min(Number(document.getElementById("qty")?.value || 1), product.stock || 99));

    try {
      const response = await fetch('/api/cart/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: product.id, quantity: qty }),
        credentials: 'include'
      });
      
      if (response.ok) {
        showToast(`Added ${product.name} to cart 🛒`, true);
        // Also sync to localStorage for fallback
        syncToLocalStorage(product.id, product.name, product.price, product.image_url, qty);
        updateCartCountUI();
      } else {
        const data = await response.json();
        showToast(data.message || 'Error adding to cart');
      }
    } catch (error) {
      // Fallback to localStorage when backend is not available
      let cart = JSON.parse(localStorage.getItem("cart") || "[]");
      const existing = cart.find(item => item.id === product.id);
      if (existing) {
        existing.qty += qty;
      } else {
        cart.push({ 
          id: product.id, 
          qty: qty, 
          name: product.name, 
          price: product.price, 
          image_url: product.image_url,
          product_id: product.id,
          quantity: qty,
          image: product.image_url
        });
      }
      localStorage.setItem("cart", JSON.stringify(cart));
      showToast(`Added ${product.name} to cart 🛒`, true);
      updateCartCountUI();
    }
  }

  // Sync item to localStorage
  function syncToLocalStorage(productId, name, price, imageUrl, qty) {
    try {
      let cart = JSON.parse(localStorage.getItem("cart") || "[]");
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
      localStorage.setItem("cart", JSON.stringify(cart));
      console.log('[CART] Synced to localStorage');
    } catch (error) {
      console.error('[CART] Error syncing to localStorage:', error);
    }
  }

  function updateCartCount(cart) {
    const el = document.getElementById("cart-count");
    if (!el) return;
    el.textContent = cart.reduce((sum, i) => sum + i.qty, 0);
  }

  function updateCartCountFromStorage() {
    updateCartCountUI();
  }

  async function updateCartCountUI() {
    try {
      const response = await fetch('/api/cart', { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        const count = data.data?.reduce((sum, item) => sum + item.quantity, 0) || 0;
        const el = document.getElementById("cart-count");
        if (el) el.textContent = count;
      }
    } catch (error) {
      const cart = JSON.parse(localStorage.getItem("cart") || "[]");
      updateCartCount(cart);
    }
  }

  // ===============================
  // WISHLIST LOGIC
  // ===============================
  async function addToWishlist(product) {
    try {
      const response = await fetch('/api/wishlist/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: product.id })
      });
      
      if (response.ok) {
        showToast(`${product.name} added to wishlist ❤️`);
      } else {
        const data = await response.json();
        showToast(data.message || 'Error adding to wishlist');
      }
    } catch (error) {
      // Fallback to localStorage
      let wishlist = JSON.parse(localStorage.getItem("wishlist") || "[]");
      if (!wishlist.find(item => item.id === product.id)) {
        wishlist.push({ id: product.id, name: product.name, price: product.price, image: product.image_url });
        localStorage.setItem("wishlist", JSON.stringify(wishlist));
        showToast(`${product.name} added to wishlist ❤️`);
      } else {
        showToast(`${product.name} is already in wishlist`);
      }
    }
  }

  // ==============================
  // HELPER
  // ==============================
  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }
