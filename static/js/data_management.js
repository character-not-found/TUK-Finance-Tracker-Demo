document.addEventListener('DOMContentLoaded', () => {
    const tableSelect = document.getElementById('tableSelect');
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    const loadDataBtn = document.getElementById('loadDataBtn');
    const dataTable = document.getElementById('dataTable');
    const noDataMessage = document.getElementById('noDataMessage');
    const messageArea = document.getElementById('messageArea');
    const tableDataHeading = document.getElementById('tableDataHeading'); // New: for dynamic heading

    const globalSearchInput = document.getElementById('globalSearchInput'); // New
    const globalSearchBtn = document.getElementById('globalSearchBtn');     // New

    const entryModal = document.getElementById('entryModal');
    const closeButton = document.querySelector('.close-button');
    const modalTitle = document.getElementById('modalTitle');
    const modalDocId = document.getElementById('modalDocId');
    const modalTableType = document.getElementById('modalTableType');
    const dynamicFormFields = document.getElementById('dynamicFormFields');
    const editForm = document.getElementById('editForm');
    const deleteBtn = document.getElementById('deleteBtn');
    const saveBtn = document.getElementById('saveBtn');

    let currentTableData = []; // To store the fetched data for editing

    // Populate Year Select
    const currentYear = new Date().getFullYear();
    for (let i = currentYear; i >= 2020; i--) { // Adjust range as needed
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        yearSelect.appendChild(option);
    }
    yearSelect.value = currentYear; // Set current year as default

    // Function to show message
    function showMessage(message, type) {
        messageArea.textContent = message;
        messageArea.className = `message ${type}`; // Reset classes and add new type
        messageArea.style.display = 'block';
        setTimeout(() => {
            messageArea.style.display = 'none';
        }, 5000); // Hide after 5 seconds
    }

    // Function to format currency in European style (e.g., 1 234,56 €)
    function formatCurrency(value) {
        if (typeof value !== 'number' || isNaN(value)) return '0.00 €';
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            currencyDisplay: 'symbol'
        }).format(value);
    }

    // Function to format date from YYYY-MM-DD to DD Month YYYY
    function formatDateToDDMonthYYYY(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString + 'T00:00:00'); // Add T00:00:00 to ensure UTC interpretation
        const options = { day: '2-digit', month: 'long', year: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // Centralized function to perform the delete operation
    async function performDelete(docId, tableType) {
        try {
            const response = await fetch(`/${tableType}/${docId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                showMessage('Entry deleted successfully!', 'success');
                // After delete, if we were in search mode, re-search, otherwise reload filtered data
                if (globalSearchInput.value.trim()) {
                    performGlobalSearch();
                } else {
                    loadTableData();
                }
                return true; // Indicate success
            } else {
                const errorData = await response.json();
                showMessage(`Error deleting entry: ${errorData.detail || response.statusText}`, 'error');
                console.error('Error deleting entry:', errorData);
                return false; // Indicate failure
            }
        } catch (error) {
            showMessage(`Network error: ${error.message}`, 'error');
            console.error('Network error during delete:', error);
            return false; // Indicate failure
        }
    }

    // Handler for delete buttons in table rows
    function handleDeleteRow(event) {
        const docId = event.target.dataset.docId;
        const tableType = event.target.dataset.tableType;
        if (confirm('Are you sure you want to delete this entry?')) {
            performDelete(docId, tableType);
        }
    }

    // Function to render table data
    function renderTable(data, tableType, isSearchMode = false) {
        const thead = dataTable.querySelector('thead tr');
        const tbody = dataTable.querySelector('tbody');
        thead.innerHTML = ''; // Clear existing headers
        tbody.innerHTML = ''; // Clear existing data

        if (data.length === 0) {
            noDataMessage.classList.remove('hidden');
            tableDataHeading.textContent = isSearchMode ? 'Search Results (No Data)' : 'Table Data (No Data)';
            return;
        } else {
            noDataMessage.classList.add('hidden');
            tableDataHeading.textContent = isSearchMode ? 'Search Results' : 'Table Data';
        }

        let headers = [];
        let dataKeys = [];

        if (isSearchMode) {
            headers = ['ID', 'Source', 'Date', 'Description', 'Amount (€)', 'Payment Method', 'Actions']; // Added Payment Method
            // We'll dynamically get data based on the item's type
        } else if (tableType === 'daily-expenses') {
            headers = ['ID', 'Date', 'Description', 'Category', 'Amount (€)', 'Payment Method', 'Actions']; // Added Payment Method
            dataKeys = ['doc_id', 'cost_date', 'description', 'category', 'amount', 'payment_method']; // Added payment_method
        } else if (tableType === 'fixed-costs') {
            headers = ['ID', 'Date', 'Description', 'Type', 'Category', 'Recipient', 'Amount (€)', 'Payment Method', 'Actions']; // Added Payment Method
            dataKeys = ['doc_id', 'cost_date', 'description', 'cost_frequency', 'category', 'recipient', 'amount_eur', 'payment_method']; // Added payment_method
        } else if (tableType === 'income') {
            headers = ['ID', 'Date', 'Tours (€)', 'Transfers (€)', 'Hours Worked', 'Actions'];
            dataKeys = ['doc_id', 'income_date', 'tours_revenue_eur', 'transfers_revenue_eur', 'hours_worked'];
        }

        // Create table headers
        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            // Specific alignment for headers
            if (headerText === 'Amount (€)') { // This is the combined 'Amount (€)' header in search results and specific tables
                th.classList.add('text-center');
            } else if (headerText === 'Source' || headerText === 'Description') { // 'Source' header should be left-aligned
                th.classList.add('text-left');
            } else if (headerText.includes('(€)')) { // This applies to 'Tours (€)', 'Transfers (€)' in specific tables
                th.classList.add('text-right');
            } else if (headerText === 'Hours Worked' || headerText === 'Actions' || headerText === 'Payment Method') { // Added Payment Method
                th.classList.add('text-center');
            }
            thead.appendChild(th);
        });

        // Populate table body
        data.forEach(item => {
            const row = tbody.insertRow();
            if (isSearchMode) {
                // For search results, we need to adapt what's displayed
                const sourceTable = item.sourceTable.replace('-', ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                const date = formatDateToDDMonthYYYY(item.cost_date || item.income_date);
                let description = '';
                let amount = 0;
                let paymentMethod = '-'; // Default for income, or if not applicable

                if (item.sourceTable === 'daily-expenses') {
                    description = item.description;
                    amount = item.amount;
                    paymentMethod = item.payment_method || '-'; // Use '-' if missing
                } else if (item.sourceTable === 'fixed-costs') {
                    description = item.description;
                    amount = item.amount_eur;
                    paymentMethod = item.payment_method || '-'; // Use '-' if missing
                } else if (item.sourceTable === 'income') {
                    description = `Tours: ${formatCurrency(item.tours_revenue_eur)}, Transfers: ${formatCurrency(item.transfers_revenue_eur)}`;
                    amount = item.tours_revenue_eur + item.transfers_revenue_eur;
                    // Income doesn't have a payment method in the same way, so it's '-'
                }

                row.insertCell().textContent = item.doc_id;
                row.insertCell().textContent = sourceTable;
                row.insertCell().textContent = date;
                row.insertCell().textContent = description;
                const amountCell = row.insertCell();
                amountCell.classList.add('text-center'); // Changed to text-center for amount values
                amountCell.textContent = formatCurrency(amount);
                const paymentMethodCell = row.insertCell(); // New cell for payment method
                paymentMethodCell.classList.add('text-center');
                paymentMethodCell.textContent = paymentMethod;

                // Add Action buttons for search results
                const actionCell = row.insertCell();
                actionCell.classList.add('actions');
                const editBtn = document.createElement('button');
                editBtn.textContent = 'Edit';
                editBtn.classList.add('btn-edit');
                editBtn.dataset.docId = item.doc_id;
                editBtn.dataset.tableType = item.sourceTable; // Use sourceTable for editing
                editBtn.addEventListener('click', openEditModal);
                actionCell.appendChild(editBtn);

                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.classList.add('btn-danger');
                deleteBtn.dataset.docId = item.doc_id;
                deleteBtn.dataset.tableType = item.sourceTable; // Use sourceTable for deleting
                deleteBtn.addEventListener('click', handleDeleteRow);
                actionCell.appendChild(deleteBtn);

            } else {
                // Existing logic for single table view
                dataKeys.forEach(key => {
                    const cell = row.insertCell();
                    let value = item[key];

                    if (key.includes('amount') || key.includes('revenue') || key.includes('eur')) {
                        cell.classList.add('text-center'); // Changed to text-center for amount values
                        value = formatCurrency(value);
                    } else if (key === 'cost_date' || key === 'income_date') {
                        value = formatDateToDDMonthYYYY(value);
                    } else if (key === 'hours_worked') {
                        cell.classList.add('text-center');
                    } else if (key === 'payment_method') { // Handle payment_method explicitly
                        cell.classList.add('text-center');
                        value = value || '-'; // Use '-' if missing
                    } else if (key === 'category' || key === 'cost_frequency') {
                        value = value ? value.replace(/_/g, ' ') : '-';
                    }
                    cell.textContent = value !== null && value !== undefined ? value : '-';
                });

                // Add Action buttons
                const actionCell = row.insertCell();
                actionCell.classList.add('actions');
                const editBtn = document.createElement('button');
                editBtn.textContent = 'Edit';
                editBtn.classList.add('btn-edit');
                editBtn.dataset.docId = item.doc_id;
                editBtn.dataset.tableType = tableType;
                editBtn.addEventListener('click', openEditModal);
                actionCell.appendChild(editBtn);

                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.classList.add('btn-danger');
                deleteBtn.dataset.docId = item.doc_id;
                deleteBtn.dataset.tableType = tableType;
                deleteBtn.addEventListener('click', handleDeleteRow);
                actionCell.appendChild(deleteBtn);
            }
        });
    }

    // Function to fetch and display data (for filter section)
    async function loadTableData() {
        const selectedTable = tableSelect.value;
        const selectedYear = yearSelect.value;
        const selectedMonth = monthSelect.value; // 0 for all months

        let endpoint = `/${selectedTable}/`;
        try {
            const response = await fetch(endpoint); // Fetch all data for the selected table type
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            let data = await response.json();

            // Filter data by year and month (client-side)
            data = data.filter(item => {
                const itemDate = new Date((item.cost_date || item.income_date) + 'T00:00:00'); // Ensure consistent date parsing
                const itemYear = itemDate.getFullYear();
                const itemMonth = itemDate.getMonth() + 1; // 1-indexed month

                const yearMatch = itemYear == selectedYear;
                const monthMatch = (selectedMonth === '0' || itemMonth == selectedMonth);

                return yearMatch && monthMatch;
            });

            // Sort data: primary by date (desc), secondary by doc_id (desc)
            data.sort((a, b) => {
                const dateA = new Date((a.cost_date || a.income_date) + 'T00:00:00'); // Ensure consistent date parsing
                const dateB = new Date((b.cost_date || b.income_date) + 'T00:00:00'); // Ensure consistent date parsing

                // Primary sort by date (descending)
                if (dateA.getTime() !== dateB.getTime()) {
                    return dateB - dateA;
                }

                // Secondary sort by doc_id (descending) if dates are the same
                return b.doc_id - a.doc_id;
            });

            // Explicitly add sourceTable to each item for consistency with search results
            // This is the key fix for "Entry not found for editing"
            currentTableData = data.map(item => ({ ...item, sourceTable: selectedTable }));

            renderTable(currentTableData, selectedTable, false); // Pass false for isSearchMode
            showMessage(`Data for ${tableSelect.options[tableSelect.selectedIndex].text} loaded successfully.`, 'success');
        } catch (error) {
            console.error('Error loading table data:', error);
            showMessage(`Error loading data: ${error.message}`, 'error');
            renderTable([], selectedTable, false); // Clear table on error
        }
    }

    // Function to perform global search
    async function performGlobalSearch() {
        const query = globalSearchInput.value.toLowerCase().trim();
        if (!query) {
            showMessage('Please enter a search query.', 'error');
            return;
        }

        let allResults = [];
        const tableTypes = ['daily-expenses', 'fixed-costs', 'income'];

        try {
            for (const tableType of tableTypes) {
                const response = await fetch(`/${tableType}/`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status} for ${tableType}`);
                }
                const data = await response.json();

                data.forEach(item => {
                    let match = false;
                    // Check string fields for a match
                    for (const key in item) {
                        if (typeof item[key] === 'string' && item[key].toLowerCase().includes(query)) {
                            match = true;
                            break;
                        }
                        // Also check number fields if they can be converted to string and match
                        if (typeof item[key] === 'number' && String(item[key]).includes(query)) {
                            match = true;
                            break;
                        }
                        // Check payment_method specifically
                        if (key === 'payment_method' && item[key] && item[key].toLowerCase().includes(query)) {
                            match = true;
                            break;
                        }
                    }
                    if (match) {
                        allResults.push({ ...item, sourceTable: tableType });
                    }
                });
            }

            // Sort search results: primary by date (desc), secondary by doc_id (desc)
            allResults.sort((a, b) => {
                const dateA = new Date((a.cost_date || a.income_date) + 'T00:00:00');
                const dateB = new Date((b.cost_date || b.income_date) + 'T00:00:00');

                if (dateA.getTime() !== dateB.getTime()) {
                    return dateB - dateA;
                }
                return b.doc_id - a.doc_id;
            });

            currentTableData = allResults; // Store search results for editing
            renderTable(allResults, null, true); // Pass true for isSearchMode
            showMessage(`Search completed. Found ${allResults.length} results.`, 'success');

        } catch (error) {
            console.error('Error during global search:', error);
            showMessage(`Error during search: ${error.message}`, 'error');
            renderTable([], null, true); // Clear table on error
        }
    }


    // Function to open the edit modal and populate fields
    function openEditModal(event) {
        const docId = event.target.dataset.docId;
        const tableType = event.target.dataset.tableType;
        // Find the entry in currentTableData using both doc_id and sourceTable
        const entry = currentTableData.find(item => item.doc_id == docId && item.sourceTable === tableType);

        if (!entry) {
            showMessage('Entry not found for editing.', 'error');
            console.error(`Attempted to edit docId: ${docId}, tableType: ${tableType}, but entry not found in currentTableData. currentTableData:`, currentTableData);
            return;
        }

        modalTitle.textContent = `Edit ${tableType.replace('-', ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')} Entry (ID: ${docId})`;
        modalDocId.value = docId;
        modalTableType.value = tableType;
        dynamicFormFields.innerHTML = ''; // Clear previous fields

        let fields = [];
        if (tableType === 'daily-expenses') {
            fields = [
                { id: 'editDailyAmount', name: 'amount', label: 'Amount (€)', type: 'number', step: '0.01', min: '0', value: entry.amount },
                { id: 'editDailyDescription', name: 'description', label: 'Description', type: 'text', value: entry.description },
                { id: 'editDailyCategory', name: 'category', label: 'Category', type: 'select', value: entry.category, options: ['Garage', 'Tuk Maintenance', 'Diesel', 'Food', 'Electricity', 'Others', 'Insurance', 'Licenses', 'Vehicle Purchase', 'Marketing'] },
                { id: 'editDailyCostDate', name: 'cost_date', label: 'Date', type: 'date', value: entry.cost_date },
                { id: 'editDailyPaymentMethod', name: 'payment_method', label: 'Payment Method', type: 'select', value: entry.payment_method, options: ['Cash', 'Bank Transfer', 'Debit Card'] } // Added Payment Method
            ];
        } else if (tableType === 'fixed-costs') {
            fields = [
                { id: 'editFixedAmountEur', name: 'amount_eur', label: 'Amount (€)', type: 'number', step: '0.01', min: '0', value: entry.amount_eur },
                { id: 'editFixedDescription', name: 'description', label: 'Description', type: 'text', value: entry.description },
                { id: 'editFixedCostFrequency', name: 'cost_frequency', label: 'Cost Type', type: 'select', value: entry.cost_frequency, options: ['Annual', 'Monthly', 'One-Off', 'Initial Investment'] },
                { id: 'editFixedCategory', name: 'category', label: 'Category', type: 'select', value: entry.category, options: ['Garage', 'Tuk Maintenance', 'Diesel', 'Food', 'Electricity', 'Others', 'Insurance', 'Licenses', 'Vehicle Purchase', 'Marketing'] },
                { id: 'editFixedRecipient', name: 'recipient', label: 'Recipient', type: 'text', value: entry.recipient },
                { id: 'editFixedCostDate', name: 'cost_date', label: 'Date', type: 'date', value: entry.cost_date },
                { id: 'editFixedPaymentMethod', name: 'payment_method', label: 'Payment Method', type: 'select', value: entry.payment_method, options: ['Cash', 'Bank Transfer', 'Debit Card'] } // Added Payment Method
            ];
        } else if (tableType === 'income') {
            fields = [
                { id: 'editIncomeDate', name: 'income_date', label: 'Date', type: 'date', value: entry.income_date },
                { id: 'editToursRevenue', name: 'tours_revenue_eur', label: 'Tours Revenue (€)', type: 'number', step: '0.01', min: '0', value: entry.tours_revenue_eur },
                { id: 'editTransfersRevenue', name: 'transfers_revenue_eur', label: 'Transfers Revenue (€)', type: 'number', step: '0.01', min: '0', value: entry.transfers_revenue_eur },
                { id: 'editHoursWorked', name: 'hours_worked', label: 'Hours Worked', type: 'number', step: '0.01', min: '0', value: entry.hours_worked }
            ];
        }

        fields.forEach(field => {
            const div = document.createElement('div');
            div.classList.add('form-field');
            const label = document.createElement('label');
            label.setAttribute('for', field.id);
            label.textContent = field.label + ':';
            div.appendChild(label);

            if (field.type === 'select') {
                const select = document.createElement('select');
                select.id = field.id;
                select.name = field.name;
                select.required = true;
                select.classList.add('shadow', 'appearance-none', 'border', 'rounded-md', 'w-full', 'py-2', 'px-3', 'text-gray-700', 'leading-tight', 'focus:outline-none', 'focus:shadow-outline', 'focus:ring-2', 'focus:ring-indigo-500', 'focus:border-transparent');
                
                // Add a default "Select..." option if the field is a payment method
                if (field.name === 'payment_method') {
                    const defaultOption = document.createElement('option');
                    defaultOption.value = ""; // Empty value
                    defaultOption.textContent = "Select payment method";
                    select.appendChild(defaultOption);
                }

                field.options.forEach(optionText => {
                    const option = document.createElement('option');
                    option.value = optionText;
                    option.textContent = optionText;
                    select.appendChild(option);
                });
                // Set the value; if entry[field.name] is undefined/null, it will default to the empty option
                select.value = entry[field.name] || ''; 
                div.appendChild(select);
            } else {
                const input = document.createElement('input');
                input.id = field.id;
                input.name = field.name;
                input.type = field.type;
                input.value = entry[field.name]; // Use entry[field.name] to get the correct value
                input.required = true;
                input.classList.add('shadow', 'appearance-none', 'border', 'rounded-md', 'w-full', 'py-2', 'px-3', 'text-gray-700', 'leading-tight', 'focus:outline-none', 'focus:shadow-outline', 'focus:ring-2', 'focus:ring-indigo-500', 'focus:border-transparent');
                if (field.type === 'number') {
                    input.step = field.step;
                    input.min = field.min;
                }
                div.appendChild(input);
            }
            dynamicFormFields.appendChild(div);
        });

        entryModal.style.display = 'flex'; // Use flex to center the modal
    }

    // Function to close the modal
    function closeModal() {
        entryModal.style.display = 'none';
        messageArea.style.display = 'none'; // Clear any messages in the main area
    }

    // Handle Save Changes
    editForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const docId = modalDocId.value;
        const tableType = modalTableType.value;
        const formData = new FormData(editForm);
        const updates = {};
        for (let [key, value] of formData.entries()) {
            // Convert numbers if necessary
            if (key.includes('amount') || key.includes('revenue') || key.includes('hours_worked') || key.includes('eur')) {
                updates[key] = parseFloat(value);
            } else {
                updates[key] = value;
            }
        }

        try {
            const response = await fetch(`/${tableType}/${docId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updates)
            });

            if (response.ok) {
                showMessage('Entry updated successfully!', 'success');
                closeModal();
                // After update, if we were in search mode, re-search, otherwise reload filtered data
                if (globalSearchInput.value.trim()) {
                    performGlobalSearch();
                } else {
                    loadTableData();
                }
            } else {
                const errorData = await response.json();
                showMessage(`Error updating entry: ${errorData.detail || response.statusText}`, 'error');
                console.error('Error updating entry:', errorData);
            }
        } catch (error) {
            showMessage(`Network error: ${error.message}`, 'error');
            console.error('Network error during update:', error);
        }
    });

    // Handle Delete (for modal's delete button)
    deleteBtn.addEventListener('click', async () => {
        const docId = modalDocId.value;
        const tableType = modalTableType.value;
        if (confirm('Are you sure you want to delete this entry?')) {
            const success = await performDelete(docId, tableType);
            if (success) {
                closeModal(); // Close modal only if deletion was successful
                // After delete, if we were in search mode, re-search, otherwise reload filtered data
                if (globalSearchInput.value.trim()) {
                    performGlobalSearch();
                } else {
                    loadTableData();
                }
            }
        }
    });


    // Event Listeners
    loadDataBtn.addEventListener('click', loadTableData);
    globalSearchBtn.addEventListener('click', performGlobalSearch); // New event listener for global search
    globalSearchInput.addEventListener('keypress', (event) => { // Allow pressing Enter to search
        if (event.key === 'Enter') {
            performGlobalSearch();
        }
    });
    closeButton.addEventListener('click', closeModal);
    window.addEventListener('click', (event) => {
        if (event.target === entryModal) {
            closeModal();
        }
    });

    // Initial load of data when page loads
    loadTableData(); // Call loadTableData on initial page load
});