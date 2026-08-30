import htmx from 'htmx.org';
import Alpine from 'alpinejs';
import focus from '@alpinejs/focus';
import { createIcons, icons } from 'lucide';

window.htmx = htmx;
window.Alpine = Alpine;

Alpine.plugin(focus);
Alpine.start();

const LUCIDE_CONFIG = {
  icons,
  attrs: { width: '1.2em', height: '1.2em', 'stroke-width': 2 }
};

const renderIcons = (root = document) => {
  createIcons({
    ...LUCIDE_CONFIG,
    root,
  });
};

// Lucide: initial render on page load
document.addEventListener('DOMContentLoaded', () => {
  renderIcons();
});

// Lucide: Standard HTMX swaps & settle events
document.addEventListener('htmx:afterSettle', (event) => {
  const root = event?.detail?.target || document;
  renderIcons(root);
});

// Alpine and Lucide: HTMX Out-Of-Band (OOB) swaps
document.addEventListener('htmx:oobAfterSwap', (event) => {
  const target = event.detail?.target;
  if (target) {
    Alpine.initTree(target);
    renderIcons(target);
  }
});


// Read Django's CSRF cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Automatically attach Django's CSRF token to all outgoing HTMX requests
document.body.addEventListener('htmx:configRequest', (evt) => {
  const csrfToken = getCookie('csrftoken');
  if (csrfToken) {
    evt.detail.headers['X-CSRFToken'] = csrfToken;
  }
});
