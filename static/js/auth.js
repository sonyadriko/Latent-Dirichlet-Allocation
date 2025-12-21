// Authentication utilities

// Check if user is logged in
function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    return token && user;
}

// Get token for API calls
function getToken() {
    return localStorage.getItem('token');
}

// Get current user
function getUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Logout
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}

// Setup logout button
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    }

    // Display user name if available
    const userNameEl = document.getElementById('user-name');
    if (userNameEl) {
        const user = getUser();
        if (user) {
            userNameEl.textContent = user.name;
        }
    }
});

// Make authenticated API request
async function apiRequest(url, options = {}) {
    const token = getToken();

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
        ...options,
        headers
    });

    // Handle unauthorized
    if (response.status === 401) {
        logout();
        throw new Error('Session expired. Please login again.');
    }

    // Check if response is valid JSON
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
        throw new Error('Invalid response format. Expected JSON.');
    }

    const responseText = await response.text();
    
    // Check if response is empty
    if (!responseText.trim()) {
        throw new Error('Empty response from server.');
    }

    try {
        return JSON.parse(responseText);
    } catch (error) {
        console.error('JSON Parse Error:', error);
        console.error('Response Text:', responseText);
        throw new Error(`JSON.parse: ${error.message}. Response: ${responseText.substring(0, 100)}`);
    }
}
