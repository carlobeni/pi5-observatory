import { elements } from './dom.js';

export function initNavigation() {
    const { sidebar, btnHamburger, navButtons, views, viewTitle } = elements;

    // Hamburger Menu Logic
    btnHamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar.classList.toggle('open');
        btnHamburger.innerHTML = sidebar.classList.contains('open') ? '<i class="fas fa-times"></i>' : '<i class="fas fa-bars"></i>';
    });

    document.addEventListener('click', (e) => {
        if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== btnHamburger) {
            sidebar.classList.remove('open');
            btnHamburger.innerHTML = '<i class="fas fa-bars"></i>';
        }
    });

    // Navigation
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            navButtons.forEach(b => b.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(target).classList.add('active');
            viewTitle.textContent = btn.innerText.trim();
            if (window.innerWidth <= 1024) {
                sidebar.classList.remove('open');
                btnHamburger.innerHTML = '<i class="fas fa-bars"></i>';
            }
        });
    });
}
