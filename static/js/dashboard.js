// Function to load user preferences
async function loadUserPreferences() {
  try {
    const response = await fetch('/update_preferences', {
      method: 'GET'
    });
    const data = await response.json();
    if (data.success) {
      document.getElementById('favColor').value = data.preferences.favorite_color || '';
      document.getElementById('favStyle').value = data.preferences.preferred_style || '';
      document.getElementById('budget').value = data.preferences.budget || '';
    }
  } catch (err) {
    console.error('Error loading preferences:', err);
  }
}

// Function to update recently viewed products
async function loadRecentlyViewed() {
  try {
    const response = await fetch('/get_recently_viewed');
    const data = await response.json();
    if (data.success) {
      const container = document.querySelector('.recently-viewed-carousel');
      container.innerHTML = data.products.map(product => `
        <div class="product-card" data-product-id="${product.id}">
          <img src="/static/${product.image}" alt="${product.title}">
          <div class="title">${product.title}</div>
          <div class="desc">${product.description}</div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading recently viewed:', err);
  }
}

// Function to load personalized recommendations
async function loadRecommendations() {
  try {
    const response = await fetch('/get_recommendations');
    const data = await response.json();
    if (data.success) {
      const container = document.querySelector('.recommend-grid');
      container.innerHTML = data.products.map(product => `
        <div class="product-card" data-product-id="${product.id}">
          <img src="/static/${product.image}" alt="${product.title}">
          <div class="title">${product.title}</div>
          <div class="desc">${product.description}</div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading recommendations:', err);
  }
}

// Function to load active offers
async function loadOffers() {
  try {
    const response = await fetch('/get_offers');
    const data = await response.json();
    if (data.success) {
      const container = document.querySelector('.offers-list');
      container.innerHTML = data.offers.map(offer => `
        <div class="offer-card">
          <svg width="28" height="28" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="12" fill="#fff"/>
            <path d="M7 13l3 3 7-7" stroke="#b23a48" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <div class="offer-content">
            <div class="offer-title">${offer.title}</div>
            <div class="offer-desc">${offer.description}</div>
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading offers:', err);
  }
}

// Function to load user reviews
async function loadUserReviews() {
  try {
    const response = await fetch('/get_user_reviews');
    const data = await response.json();
    if (data.success) {
      const container = document.querySelector('.reviews-list');
      container.innerHTML = data.reviews.map(review => `
        <div class="review-card">
          <div class="review-title">${review.product_title}</div>
          <div class="review-rating">${'★'.repeat(review.rating)}${'☆'.repeat(5-review.rating)}</div>
          <div class="review-text">${review.review_text}</div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Error loading reviews:', err);
  }
}

// Initialize all dynamic content
document.addEventListener('DOMContentLoaded', () => {
  loadUserPreferences();
  loadRecentlyViewed();
  loadRecommendations();
  loadOffers();
  loadUserReviews();
});

// Update active section in sidebar
document.querySelectorAll('.sidebar-nav button').forEach(button => {
  button.addEventListener('click', () => {
    // Update active state
    document.querySelectorAll('.sidebar-nav button').forEach(b => b.classList.remove('active'));
    button.classList.add('active');
    
    // Show selected section
    const sectionId = 'section-' + button.getAttribute('data-section');
    document.querySelectorAll('.dashboard-section').forEach(section => {
      section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
    
    // Load section-specific data
    const section = button.getAttribute('data-section');
    switch(section) {
      case 'recently':
        loadRecentlyViewed();
        break;
      case 'recommend':
        loadRecommendations();
        break;
      case 'offers':
        loadOffers();
        break;
      case 'reviews':
        loadUserReviews();
        break;
    }
  });
});
