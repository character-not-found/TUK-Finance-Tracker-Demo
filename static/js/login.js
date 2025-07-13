document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const messageDisplay = document.getElementById('message');

    if (loginForm) {
        loginForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const username = usernameInput.value;
            const password = passwordInput.value;

            messageDisplay.textContent = '';
            messageDisplay.style.color = 'red';

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
                    messageDisplay.textContent = 'Login successful! Redirecting...';
                    messageDisplay.style.color = 'green';
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
