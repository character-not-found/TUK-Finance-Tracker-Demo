document.addEventListener('DOMContentLoaded', () => {
    const incomeForm = document.getElementById('incomeForm');
    const confirmationMessage = document.getElementById('confirmationMessage');

    function showMessage(message, type) {
        confirmationMessage.textContent = message;
        confirmationMessage.classList.remove('hidden', 'success', 'error');
        confirmationMessage.classList.add('message', type);
        confirmationMessage.classList.remove('hidden');

        setTimeout(() => {
            confirmationMessage.classList.add('hidden');
        }, 5000);
    }

    const today = new Date().toISOString().split('T')[0];
    document.getElementById('incomeDate').value = today;

    incomeForm.addEventListener('submit', async (event) => {
        event.preventDefault();

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
            const response = await fetch('/income/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                showMessage('Income registered successfully!', 'success');
                incomeForm.reset();
                document.getElementById('incomeDate').value = today;
                document.getElementById('toursRevenue').value = 0;
                document.getElementById('transfersRevenue').value = 0;
                document.getElementById('hoursWorked').value = 0;
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
