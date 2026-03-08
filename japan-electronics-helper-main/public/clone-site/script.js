document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('a[href]').forEach((link) => {
    const href = link.getAttribute('href') || '';
    if (!href.startsWith('#')) {
      link.addEventListener('click', (e) => e.preventDefault());
    }
  });
});
