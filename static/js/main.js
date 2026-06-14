// ── LibraVerse Main JS ──

// Toast notification
function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.style.background = type === 'error' ? '#e63946' : type === 'warning' ? '#f77f00' : '#2dc653';
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
}

// Borrow a book
async function borrowBook(bookId, event) {
  if (event) { event.stopPropagation(); event.preventDefault(); }
  try {
    const res = await fetch(`/api/borrow/${bookId}`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast(data.message || 'Book borrowed successfully!', 'success');
      setTimeout(() => location.reload(), 1500);
    } else {
      showToast(data.error || 'Could not borrow book', 'error');
    }
  } catch (e) {
    showToast('Something went wrong', 'error');
  }
}

// Global search
const searchInput = document.getElementById('globalSearch');
const searchDropdown = document.getElementById('searchDropdown');
let searchTimeout;

if (searchInput) {
  searchInput.addEventListener('input', function () {
    clearTimeout(searchTimeout);
    const q = this.value.trim();
    if (!q) { searchDropdown.classList.remove('show'); return; }
    searchTimeout = setTimeout(async () => {
      const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
      const results = await res.json();
      if (results.length === 0) {
        searchDropdown.innerHTML = '<div class="search-item"><div class="search-item-info"><h4>No results found</h4></div></div>';
      } else {
        searchDropdown.innerHTML = results.map(b => `
          <a href="/book/${b.id}" class="search-item">
            <div class="search-item-icon"><i class="fas fa-book"></i></div>
            <div class="search-item-info">
              <h4>${b.title}</h4>
              <span>${b.author} · ${b.category}</span>
            </div>
          </a>
        `).join('');
      }
      searchDropdown.classList.add('show');
    }, 250);
  });

  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
      searchDropdown.classList.remove('show');
    }
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && searchInput.value) {
      window.location = `/books?search=${encodeURIComponent(searchInput.value)}`;
    }
  });
}

// Wishlist toggle (book list pages)
document.querySelectorAll('.wishlist-btn').forEach(btn => {
  btn.addEventListener('click', async function (e) {
    e.stopPropagation(); e.preventDefault();
    const id = this.dataset.id;
    const res = await fetch(`/api/wishlist/toggle/${id}`, { method: 'POST' });
    const data = await res.json();
    const icon = this.querySelector('i');
    if (data.added) {
      icon.style.color = '#e63946';
      showToast('Added to wishlist!');
    } else {
      icon.style.color = '';
      showToast('Removed from wishlist');
    }
  });
});

// Navbar scroll effect
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (navbar) {
    if (window.scrollY > 20) navbar.style.boxShadow = '0 4px 30px rgba(0,0,0,0.12)';
    else navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.08)';
  }
});

// Mobile menu (basic toggle)
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
if (mobileMenuBtn) {
  mobileMenuBtn.addEventListener('click', () => {
    const links = document.querySelector('.nav-links');
    if (links) {
      links.style.display = links.style.display === 'flex' ? 'none' : 'flex';
      links.style.flexDirection = 'column';
      links.style.position = 'absolute';
      links.style.top = '64px';
      links.style.right = '24px';
      links.style.background = 'white';
      links.style.padding = '16px';
      links.style.borderRadius = '12px';
      links.style.boxShadow = '0 8px 30px rgba(0,0,0,0.15)';
      links.style.zIndex = '999';
    }
  });
}

// Scroll reveal animations
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.book-card, .category-card, .book-row-card').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
  observer.observe(el);
});


// Profile dropdown click fix
document.addEventListener('DOMContentLoaded', function () {
  const profile = document.querySelector('.nav-profile');
  const avatar = document.querySelector('.profile-avatar');
  const dropdown = document.querySelector('.profile-dropdown');

  if (profile && avatar && dropdown) {
    avatar.addEventListener('click', function (e) {
      e.stopPropagation();
      dropdown.style.display =
        dropdown.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', function (e) {
      if (!profile.contains(e.target)) {
        dropdown.style.display = 'none';
      }
    });
  }
});
