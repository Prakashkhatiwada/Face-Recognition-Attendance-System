/**
 * Theme Toggle System — Dark / Light Mode
 * Persists choice to localStorage, applies on every page load.
 */
(function () {
    const STORAGE_KEY = 'faceattend-theme';

    function getPreferred() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) return saved;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
        // Update all toggle button icons
        document.querySelectorAll('.theme-toggle-btn .material-icons').forEach(function (icon) {
            icon.textContent = theme === 'dark' ? 'light_mode' : 'dark_mode';
        });
    }

    // Apply immediately (before paint) to avoid flash
    applyTheme(getPreferred());

    // After DOM ready, attach click handlers
    document.addEventListener('DOMContentLoaded', function () {
        applyTheme(getPreferred()); // re-apply to update icons
        document.querySelectorAll('.theme-toggle-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var current = document.documentElement.getAttribute('data-theme') || 'light';
                applyTheme(current === 'dark' ? 'light' : 'dark');
            });
        });
    });
})();
