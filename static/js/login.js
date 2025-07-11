// static/js/login.js
document.addEventListener('DOMContentLoaded', () => {
    console.log('login.js loaded.');

    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const messageDisplay = document.getElementById('message');

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault(); // Prevent default form submission

            const username = usernameInput.value;
            const password = passwordInput.value;

            // Clear previous messages
            messageDisplay.textContent = '';
            messageDisplay.style.color = 'red'; // Default to red for errors

            try {
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);

                const response = await fetch('/login/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: formData.toString(),
                });

                if (response.ok) {
                    // No need to read data or store token in sessionStorage
                    // The server has already set the HttpOnly cookie.
                    messageDisplay.textContent = 'Login successful! Redirecting...';
                    messageDisplay.style.color = 'green';
                    // Redirect to the dashboard or main page
                    window.location.href = '/';
                } else {
                    const errorData = await response.json();
                    messageDisplay.textContent = errorData.detail || 'Login failed.';
                    console.error('Login failed:', errorData);
                }
            } catch (error) {
                messageDisplay.textContent = 'An error occurred during login.';
                console.error('Network or unexpected error:', error);
            }
        });
    }
});
