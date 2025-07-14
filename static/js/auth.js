// static/js/auth.js

document.addEventListener('DOMContentLoaded', () => {
    const authStatusSpan = document.getElementById('authStatus');
    const logoutButton = document.getElementById('logoutButton');
    const loggedInNavItems = document.getElementById('loggedInNavItems');
    const mobileMenu = document.getElementById('mobile-menu');
    const mobileMenuButton = document.getElementById('mobileMenuButton');

    const messageArea = document.getElementById('authMessageArea');

    // Function to display messages
    function showMessage(message, type) {
        if (messageArea) {
            messageArea.textContent = message;
            messageArea.classList.remove('hidden', 'success', 'error');
            messageArea.classList.add('message', type);
            messageArea.classList.remove('hidden');
            setTimeout(() => {
                messageArea.classList.add('hidden');
            }, 5000);
        } else {
            console.warn("Message area not found for auth.js. Message:", message);
        }
    }

    function handleAuthUI(isLoggedIn) {
        if (isLoggedIn) {
            if (authStatusSpan) {
                authStatusSpan.textContent = 'Logged in as demo_user.';
                authStatusSpan.style.color = 'green';
                authStatusSpan.classList.remove('hidden');
            }
            if (logoutButton) logoutButton.classList.remove('hidden');

            // When logged in:
            // Remove the force-hide class to make them visible
            if (loggedInNavItems) {
                loggedInNavItems.classList.remove('force-hide');
                // IMPORTANT: DO NOT remove 'hidden' here. Let home.js and Tailwind's md:flex manage it.
                // loggedInNavItems.classList.remove('hidden'); // REMOVED THIS LINE
            }
            if (mobileMenu) {
                mobileMenu.classList.remove('hidden');
            }
            if (mobileMenuButton) {
                mobileMenuButton.classList.remove('force-hide');
                mobileMenuButton.classList.remove('hidden'); // Also remove 'hidden' for Tailwind's md:hidden to work
            }

        } else { // Not logged in
            if (authStatusSpan) {
                authStatusSpan.textContent = '';
                authStatusSpan.classList.add('hidden');
            }
            if (logoutButton) logoutButton.classList.add('hidden');

            // If not logged in, ensure navigation elements are hidden using force-hide
            if (loggedInNavItems) {
                loggedInNavItems.classList.add('force-hide');
                loggedInNavItems.classList.add('hidden'); // Keep 'hidden' for consistency
                loggedInNavItems.classList.remove('md:flex'); // Ensure md:flex is removed to prevent layout issues
            }
            if (mobileMenu) {
                mobileMenu.classList.add('hidden');
            }
            if (mobileMenuButton) {
                mobileMenuButton.classList.add('force-hide');
                mobileMenuButton.classList.add('hidden'); // Keep 'hidden' for consistency
            }
        }
    }

    const isCurrentlyLoggedIn = (window.location.pathname !== '/login');
    handleAuthUI(isCurrentlyLoggedIn);

    if (logoutButton) {
        logoutButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    handleAuthUI(false);
                    window.location.href = '/login';
                } else {
                    const errorData = await response.json();
                    console.error('Logout failed:', errorData.detail || 'Unknown error');
                    showMessage('Logout failed: ' + (errorData.detail || 'Please try again.'), 'error');
                }
            } catch (error) {
                console.error('Network or unexpected error during logout:', error);
                showMessage('An error occurred during logout.', 'error');
            }
        });
    }
});
