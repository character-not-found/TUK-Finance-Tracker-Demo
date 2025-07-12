// static/js/auth.js
document.addEventListener('DOMContentLoaded', () => {
    const authStatusSpan = document.getElementById('authStatus');
    const logoutButton = document.getElementById('logoutButton');
    const loggedInNavItems = document.getElementById('loggedInNavItems'); // Get the new div

    // Function to handle showing/hiding UI elements based on authentication status
    function handleAuthUI(isLoggedIn) {
        if (isLoggedIn) {
            // User is logged in
            if (authStatusSpan) {
                authStatusSpan.textContent = 'Logged in as demo_user.'; // Changed text here
                authStatusSpan.style.color = 'green';
                authStatusSpan.classList.remove('hidden'); // Show status
            }
            if (logoutButton) logoutButton.classList.remove('hidden'); // Show logout button
            if (loggedInNavItems) {
                loggedInNavItems.classList.remove('hidden'); // Show nav items
            }
        } else {
            // User is not logged in
            if (authStatusSpan) {
                // Only show "Please log in." if not on the actual login page
                if (window.location.pathname !== '/login') {
                    authStatusSpan.textContent = 'Please log in.';
                    authStatusSpan.style.color = 'orange';
                    authStatusSpan.classList.remove('hidden'); // Show status
                } else {
                    authStatusSpan.classList.add('hidden'); // Hide status on login page
                }
            }
            if (logoutButton) logoutButton.classList.add('hidden'); // Hide logout button
            if (loggedInNavItems) {
                loggedInNavItems.classList.add('hidden'); // Hide nav items
            }
        }
    }

    // Initial check on page load
    const isCurrentlyLoggedIn = (window.location.pathname !== '/login');
    handleAuthUI(isCurrentlyLoggedIn);

    // Handle logout button click
    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    // No body needed for logout
                });

                if (response.ok) {
                    // Update UI immediately
                    handleAuthUI(false);
                    // Redirect to login page after successful logout
                    window.location.href = '/login';
                } else {
                    const errorData = await response.json();
                    console.error('Logout failed:', errorData.detail || 'Unknown error');
                    alert('Logout failed: ' + (errorData.detail || 'Please try again.'));
                }
            } catch (error) {
                console.error('Network or unexpected error during logout:', error);
                alert('An error occurred during logout.');
            }
        });
    }
});
