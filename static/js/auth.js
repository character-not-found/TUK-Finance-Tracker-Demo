// static/js/auth.js
document.addEventListener('DOMContentLoaded', () => {
    console.log('auth.js loaded.');

    const authStatusSpan = document.getElementById('authStatus');
    const logoutButton = document.getElementById('logoutButton');

    // Function to check if a specific cookie exists (simple check for HttpOnly cookie presence)
    // Note: JS cannot read HttpOnly cookies, so this is a simplified check.
    // The true authentication check happens on the server for each protected route.
    function checkAuthStatus() {
        // If we are on the login page, or if the server redirected us to login,
        // it means we are not authenticated or the token expired.
        // For actual status, an API call to a protected endpoint would be better.
        // For this demo, if the user is on a protected page, we assume they are authenticated
        // if they haven't been redirected to /login.
        if (window.location.pathname === '/login') {
            if (authStatusSpan) {
                authStatusSpan.textContent = 'Please log in.';
                authStatusSpan.style.color = 'orange';
            }
            if (logoutButton) logoutButton.style.display = 'none';
        } else {
            // Assume logged in if not on login page and not redirected
            if (authStatusSpan) {
                authStatusSpan.textContent = 'Logged in as demo_user.';
                authStatusSpan.style.color = 'green';
            }
            if (logoutButton) logoutButton.style.display = 'inline-block';
        }
    }

    // Initial check on page load
    checkAuthStatus();

    // Handle logout button click
    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json', // Or no content-type if body is empty
                    },
                    // No body needed for logout
                });

                if (response.ok) {
                    console.log('Logged out successfully.');
                    // Redirect to login page after successful logout
                    window.location.href = '/login';
                } else {
                    const errorData = await response.json();
                    console.error('Logout failed:', errorData.detail || 'Unknown error');
                    alert('Logout failed: ' + (errorData.detail || 'Please try again.')); // Using alert for simplicity here
                }
            } catch (error) {
                console.error('Network or unexpected error during logout:', error);
                alert('An error occurred during logout.'); // Using alert for simplicity here
            }
        });
    }
});
