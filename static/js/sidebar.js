// Sidebar Functions

// Mobile Sidebar Functions
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    sidebar?.classList.toggle('active');
    overlay?.classList.toggle('active');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    sidebar?.classList.remove('active');
    overlay?.classList.remove('active');
}

// Desktop Sidebar Toggle Function
function toggleDesktopSidebar() {
    const sidebar = document.getElementById('sidebar');
    const dashboard = document.querySelector('.dashboard');
    const toggleBtn = document.getElementById('desktop-sidebar-toggle');

    sidebar?.classList.toggle('collapsed');
    dashboard?.classList.toggle('sidebar-collapsed');

    // Update toggle button icon
    if (sidebar?.classList.contains('collapsed')) {
        toggleBtn.innerHTML = '→';
        toggleBtn.title = 'Show Sidebar';
    } else {
        toggleBtn.innerHTML = '☰';
        toggleBtn.title = 'Hide Sidebar';
    }
}

// Close sidebar when clicking on menu links (mobile)
document.addEventListener('DOMContentLoaded', () => {
    const menuLinks = document.querySelectorAll('.sidebar-menu a');
    menuLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 1024) {
                closeSidebar();
            }
        });
    });
});
