document.addEventListener('DOMContentLoaded', () => {
    const authStatusSpan = document.getElementById('authStatus');
    const logoutButton = document.getElementById('logoutButton');
    const loggedInNavItems = document.getElementById('loggedInNavItems');
    const messageArea = document.getElementById('authMessageArea'); // Assuming a message area exists in your HTML for auth

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
            if (loggedInNavItems) {
                loggedInNavItems.classList.remove('hidden');
            }
        } else {
            if (authStatusSpan) {
                if (window.location.pathname !== '/login') {
                    authStatusSpan.textContent = 'Please log in.';
                    authStatusSpan.style.color = 'orange';
                    authStatusSpan.classList.remove('hidden');
                } else {
                    authStatusSpan.classList.add('hidden');
                }
            }
            if (logoutButton) logoutButton.classList.add('hidden');
            if (loggedInNavItems) {
                loggedInNavItems.classList.add('hidden');
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
