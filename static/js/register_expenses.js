document.addEventListener('DOMContentLoaded', () => {
    const expenseTypeSelect = document.getElementById('expenseType');
    const dailyExpenseFormSection = document.getElementById('dailyExpenseFormSection');
    const fixedCostFormSection = document.getElementById('fixedCostFormSection');
    const dailyExpenseForm = document.getElementById('dailyExpenseForm');
    const fixedCostForm = document.getElementById('fixedCostForm');
    const confirmationMessage = document.getElementById('confirmationMessage');

    const today = new Date().toISOString().split('T')[0];
    document.getElementById('dailyCostDate').value = today;
    document.getElementById('fixedCostDate').value = today;

    function showMessage(message, type) {
        confirmationMessage.textContent = message;
        confirmationMessage.className = `message ${type}`;
        confirmationMessage.classList.remove('hidden');
        setTimeout(() => {
            confirmationMessage.classList.add('hidden');
        }, 5000);
    }

    expenseTypeSelect.addEventListener('change', (event) => {
        if (event.target.value === 'daily') {
            dailyExpenseFormSection.classList.remove('hidden');
            fixedCostFormSection.classList.add('hidden');
        } else {
            dailyExpenseFormSection.classList.add('hidden');
            fixedCostFormSection.classList.remove('hidden');
        }
    });

    dailyExpenseForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const amount = parseFloat(document.getElementById('dailyAmount').value);
        const description = document.getElementById('dailyDescription').value;
        const category = document.getElementById('dailyCategory').value;
        const costDate = document.getElementById('dailyCostDate').value;
        const paymentMethod = document.getElementById('dailyPaymentMethod').value;

        const formData = {
            amount: amount,
            description: description,
            category: category,
            cost_date: costDate,
            payment_method: paymentMethod
        };

        try {
            const response = await fetch('/daily-expenses/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                showMessage('Daily Expense registered successfully!', 'success');
                dailyExpenseForm.reset();
                document.getElementById('dailyCostDate').value = today;
            } else {
                const errorData = await response.json();
                showMessage(`Error registering Daily Expense: ${errorData.detail || response.statusText}`, 'error');
                console.error('Error adding daily expense:', errorData);
            }
        } catch (error) {
            showMessage(`Network error: ${error.message}`, 'error');
            console.error('Network error during daily expense submission:', error);
        }
    });

    fixedCostForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const amountEur = parseFloat(document.getElementById('fixedAmountEur').value);
        const description = document.getElementById('fixedDescription').value;
        const costFrequency = document.getElementById('fixedCostFrequency').value;
        const category = document.getElementById('fixedCategory').value;
        const recipient = document.getElementById('fixedRecipient').value;
        const costDate = document.getElementById('fixedCostDate').value;
        const paymentMethod = document.getElementById('fixedPaymentMethod').value;

        const formData = {
            amount_eur: amountEur,
            description: description,
            cost_frequency: costFrequency,
            category: category,
            recipient: recipient,
            cost_date: costDate,
            payment_method: paymentMethod
        };

        try {
            const response = await fetch('/fixed-costs/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                showMessage('Fixed Cost registered successfully!', 'success');
                fixedCostForm.reset();
                document.getElementById('fixedCostDate').value = today;
            } else {
                const errorData = await response.json();
                showMessage(`Error registering Fixed Cost: ${errorData.detail || response.statusText}`, 'error');
                console.error('Error adding fixed cost:', errorData);
            }
        } catch (error) {
            showMessage(`Network error: ${error.message}`, 'error');
            console.error('Network error during fixed cost submission:', error);
        }
    });
});
