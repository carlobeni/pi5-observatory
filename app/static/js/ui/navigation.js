import { elements } from './dom.js';

export function initNavigation() {
    const { sidebar, btnHamburger, navButtons, views, viewTitle } = elements;
    const overlay = document.getElementById('sidebar-overlay');

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        btnHamburger.innerHTML = '<i class="fas fa-bars"></i>';
    }

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('active');
        btnHamburger.innerHTML = '<i class="fas fa-times"></i>';
    }

    // Hamburger Menu Logic
    btnHamburger.addEventListener('click', (e) => {
        e.stopPropagation();
        if (sidebar.classList.contains('open')) {
            closeSidebar();
        } else {
            openSidebar();
        }
    });

    // Overlay click closes sidebar
    if (overlay) {
        overlay.addEventListener('click', closeSidebar);
    }

    // Click outside closes sidebar
    document.addEventListener('click', (e) => {
        if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== btnHamburger) {
            closeSidebar();
        }
    });

    // Navigation
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            
            // UI Update
            navButtons.forEach(b => b.classList.remove('active'));
            views.forEach(v => v.classList.remove('active'));
            
            btn.classList.add('active');
            const targetView = document.getElementById(target);
            if (targetView) targetView.classList.add('active');
            
            viewTitle.textContent = btn.innerText.trim();

            // Mobile Auto-close
            if (window.innerWidth <= 1024) {
                closeSidebar();
            }
        });
    });
}
