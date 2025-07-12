document.addEventListener('DOMContentLoaded', () => {
    const incomeForm = document.getElementById('incomeForm');
    const confirmationMessage = document.getElementById('confirmationMessage');

    // Function to display messages
    function showMessage(message, type) {
        confirmationMessage.textContent = message;
        // Ensure all previous state classes are removed before adding new ones
        confirmationMessage.classList.remove('hidden', 'success', 'error');
        // Add the base 'message' class and the specific 'type' (success/error)
        confirmationMessage.classList.add('message', type);
        // Remove 'hidden' to make the message visible
        confirmationMessage.classList.remove('hidden');

        // Hide message after 5 seconds by adding the 'hidden' class back
        setTimeout(() => {
            confirmationMessage.classList.add('hidden');
        }, 5000);
    }

    // Set current date as default for date input
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('incomeDate').value = today;

    // Handle Income Form Submission
    incomeForm.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent default form submission

        // Basic client-side validation
        const incomeDate = document.getElementById('incomeDate').value;
        const toursRevenue = parseFloat(document.getElementById('toursRevenue').value);
        const transfersRevenue = parseFloat(document.getElementById('transfersRevenue').value);
        const hoursWorked = parseFloat(document.getElementById('hoursWorked').value);

        if (incomeDate === '' || isNaN(toursRevenue) || isNaN(transfersRevenue) || isNaN(hoursWorked) || toursRevenue < 0 || transfersRevenue < 0 || hoursWorked < 0) {
            showMessage('Please fill in all fields correctly for Income (amounts and hours must be non-negative).', 'error');
            return;
        }

        const formData = {
            income_date: incomeDate,
            tours_revenue_eur: toursRevenue,
            transfers_revenue_eur: transfersRevenue,
            hours_worked: hoursWorked
        };

        try {
            const response = await fetch('/income/', { // Endpoint for income
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                showMessage('Income registered successfully!', 'success');
                incomeForm.reset(); // Clear form fields
                document.getElementById('incomeDate').value = today; // Reset date to today
                document.getElementById('toursRevenue').value = 0; // Reset to 0
                document.getElementById('transfersRevenue').value = 0; // Reset to 0
                document.getElementById('hoursWorked').value = 0; // Reset to 0
            } else {
                const errorData = await response.json();
                showMessage(`Error registering Income: ${errorData.detail || response.statusText}`, 'error');
                console.error('Error adding income:', errorData);
            }
        } catch (error) {
            showMessage(`Network error: ${error.message}`, 'error');
            console.error('Network error during income submission:', error);
        }
    });
});
