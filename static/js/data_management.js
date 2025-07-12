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

    // Function to show message (kept for error messages, but success messages will be suppressed)
    function showMessage(message, type) {
        messageArea.textContent = message;
        // Clear previous states and add new type
        messageArea.classList.remove('hidden', 'success', 'error'); // Remove all potential previous state classes
        messageArea.classList.add('message', type); // Add 'message' base class and the specific 'type' (success/error)
        messageArea.classList.remove('hidden'); // Ensure it's visible

        setTimeout(() => {
            messageArea.classList.add('hidden'); // Hide after 5 seconds
        }, 5000); 
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
        let headerAlignments = {}; // To store desired alignment for each header
        let cellAlignments = {};  // To store desired alignment for each cell

        if (isSearchMode) {
            headers = ['ID', 'Source', 'Date', 'Description', 'Amount (€)', 'Payment Method', 'Actions'];
            headerAlignments = {
                'ID': 'text-center',
                'Source': 'text-left',
                'Date': 'text-left',
                'Description': 'text-left',
                'Amount (€)': 'text-right',
                'Payment Method': 'text-center', // Changed to text-center
                'Actions': 'text-center' // Actions column is always centered
            };
            cellAlignments = {
                'ID': 'text-center',
                'Source': 'text-left',
                'Date': 'text-left',
                'Description': 'text-left',
                'Amount (€)': 'text-right',
                'Payment Method': 'text-center', // Changed to text-center
            };
        } else if (tableType === 'daily-expenses') {
            headers = ['ID', 'Date', 'Description', 'Category', 'Amount (€)', 'Payment Method', 'Actions'];
            dataKeys = ['doc_id', 'cost_date', 'description', 'category', 'amount', 'payment_method'];
            headerAlignments = {
                'ID': 'text-center',
                'Date': 'text-left',
                'Description': 'text-left',
                'Category': 'text-left',
                'Amount (€)': 'text-right',
                'Payment Method': 'text-center', // Changed to text-center
                'Actions': 'text-center'
            };
            cellAlignments = {
                'doc_id': 'text-center',
                'cost_date': 'text-left',
                'description': 'text-left',
                'category': 'text-left',
                'amount': 'text-right',
                'payment_method': 'text-center', // Changed to text-center
            };
        } else if (tableType === 'fixed-costs') {
            headers = ['ID', 'Date', 'Description', 'Type', 'Category', 'Recipient', 'Amount (€)', 'Payment Method', 'Actions'];
            dataKeys = ['doc_id', 'cost_date', 'description', 'cost_frequency', 'category', 'recipient', 'amount_eur', 'payment_method'];
            headerAlignments = {
                'ID': 'text-center',
                'Date': 'text-left',
                'Description': 'text-left',
                'Type': 'text-left',
                'Category': 'text-left',
                'Recipient': 'text-left',
                'Amount (€)': 'text-right',
                'Payment Method': 'text-center', // Changed to text-center
                'Actions': 'text-center'
            };
            cellAlignments = {
                'doc_id': 'text-center',
                'cost_date': 'text-left',
                'description': 'text-left',
                'cost_frequency': 'text-left',
                'category': 'text-left',
                'recipient': 'text-left',
                'amount_eur': 'text-right',
                'payment_method': 'text-center', // Changed to text-center
            };
        } else if (tableType === 'income') {
            headers = ['ID', 'Date', 'Tours (€)', 'Transfers (€)', 'Hours Worked', 'Actions'];
            dataKeys = ['doc_id', 'income_date', 'tours_revenue_eur', 'transfers_revenue_eur', 'hours_worked'];
            headerAlignments = {
                'ID': 'text-center',
                'Date': 'text-left',
                'Tours (€)': 'text-right',
                'Transfers (€)': 'text-right',
                'Hours Worked': 'text-center',
                'Actions': 'text-center'
            };
            cellAlignments = {
                'doc_id': 'text-center',
                'income_date': 'text-left',
                'tours_revenue_eur': 'text-right',
                'transfers_revenue_eur': 'text-right',
                'hours_worked': 'text-center',
            };
        }

        // Create table headers
        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            const alignmentClass = headerAlignments[headerText];
            if (alignmentClass) {
                th.classList.add(alignmentClass);
            }
            thead.appendChild(th);
        });

        // Populate table body
        data.forEach(item => {
            const row = tbody.insertRow();
            if (isSearchMode) {
                const sourceTable = item.sourceTable.replace('-', ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                const date = formatDateToDDMonthYYYY(item.cost_date || item.income_date);
                let description = '';
                let amount = 0;
                let paymentMethod = '-';

                if (item.sourceTable === 'daily-expenses') {
                    description = item.description;
                    amount = item.amount;
                    paymentMethod = item.payment_method || '-';
                } else if (item.sourceTable === 'fixed-costs') {
                    description = item.description;
                    amount = item.amount_eur;
                    paymentMethod = item.payment_method || '-';
                } else if (item.sourceTable === 'income') {
                    description = `Tours: ${formatCurrency(item.tours_revenue_eur)}, Transfers: ${formatCurrency(item.transfers_revenue_eur)}`;
                    amount = item.tours_revenue_eur + item.transfers_revenue_eur;
                }

                // Create cells and apply alignments
                const idCell = row.insertCell();
                idCell.classList.add(cellAlignments['ID']);
                idCell.textContent = item.doc_id;

                const sourceCell = row.insertCell();
                sourceCell.classList.add(cellAlignments['Source']);
                sourceCell.textContent = sourceTable;

                const dateCell = row.insertCell();
                dateCell.classList.add(cellAlignments['Date']);
                dateCell.textContent = date;

                const descCell = row.insertCell();
                descCell.classList.add(cellAlignments['Description']);
                descCell.textContent = description;

                const amountCell = row.insertCell();
                amountCell.classList.add(cellAlignments['Amount (€)']);
                amountCell.textContent = formatCurrency(amount);

                const paymentMethodCell = row.insertCell();
                paymentMethodCell.classList.add(cellAlignments['Payment Method']); // Use the specific alignment
                paymentMethodCell.textContent = paymentMethod;

                // Add Action buttons for search results
                const actionCell = row.insertCell();
                actionCell.classList.add('actions'); // Keep 'actions' class for specific button styling
                const editBtn = document.createElement('button');
                editBtn.textContent = 'Edit';
                editBtn.classList.add('btn-edit');
                editBtn.dataset.docId = item.doc_id;
                editBtn.dataset.tableType = item.sourceTable;
                editBtn.addEventListener('click', openEditModal);
                actionCell.appendChild(editBtn);

                const deleteBtn = document.createElement('button');
                deleteBtn.textContent = 'Delete';
                deleteBtn.classList.add('btn-danger');
                deleteBtn.dataset.docId = item.doc_id;
                deleteBtn.dataset.tableType = item.sourceTable;
                deleteBtn.addEventListener('click', handleDeleteRow);
                actionCell.appendChild(deleteBtn);

            } else {
                // Existing logic for single table view
                dataKeys.forEach(key => {
                    const cell = row.insertCell();
                    let value = item[key];
                    // Retrieve alignment from cellAlignments based on the key
                    let alignmentClass = cellAlignments[key] || 'text-left'; // Default to left-aligned if not specified

                    if (key.includes('amount') || key.includes('revenue') || key.includes('eur')) {
                        value = formatCurrency(value);
                    } else if (key === 'cost_date' || key === 'income_date') {
                        value = formatDateToDDMonthYYYY(value);
                    } else if (key === 'payment_method' || key === 'category' || key === 'cost_frequency' || key === 'recipient') {
                        value = value ? value.replace(/_/g, ' ') : '-'; // Replace underscores for display
                    }

                    cell.classList.add(alignmentClass);
                    cell.textContent = value !== null && value !== undefined ? value : '-';
                });

                // Add Action buttons
                const actionCell = row.insertCell();
                actionCell.classList.add('actions'); // Keep 'actions' class for specific button styling
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
            currentTableData = data.map(item => ({ ...item, sourceTable: selectedTable }));

            renderTable(currentTableData, selectedTable, false); // Pass false for isSearchMode
            // showMessage(`Data for ${tableSelect.options[tableSelect.selectedIndex].text} loaded successfully.`, 'success'); // REMOVED: Suppress success message
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
            // showMessage(`Search completed. Found ${allResults.length} results.`, 'success'); // REMOVED: Suppress success message

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
                { id: 'editDailyAmount', name: 'amount', label: 'Amount (€)', type: 'number', step: '0.01', min: '0', value: entry.amount, required: true },
                { id: 'editDailyDescription', name: 'description', label: 'Description', type: 'text', value: entry.description, required: true },
                { id: 'editDailyCategory', name: 'category', label: 'Category', type: 'select', value: entry.category, options: ['Garage', 'Tuk Maintenance', 'Diesel', 'Food', 'Electricity', 'Others', 'Insurance', 'Licenses', 'Vehicle Purchase', 'Marketing'], required: true },
                { id: 'editDailyCostDate', name: 'cost_date', label: 'Date', type: 'date', value: entry.cost_date, required: true },
                { id: 'editDailyPaymentMethod', name: 'payment_method', label: 'Payment Method', type: 'select', value: entry.payment_method, options: ['Cash', 'Bank Transfer', 'Debit Card'], required: true }
            ];
        } else if (tableType === 'fixed-costs') {
            fields = [
                { id: 'editFixedAmountEur', name: 'amount_eur', label: 'Amount (€)', type: 'number', step: '0.01', min: '0', value: entry.amount_eur, required: true },
                { id: 'editFixedDescription', name: 'description', label: 'Description', type: 'text', value: entry.description, required: true },
                { id: 'editFixedCostFrequency', name: 'cost_frequency', label: 'Cost Type', type: 'select', value: entry.cost_frequency, options: ['Annual', 'Monthly', 'One-Off', 'Initial Investment'], required: true },
                { id: 'editFixedCategory', name: 'category', label: 'Category', type: 'select', value: entry.category, options: ['Garage', 'Tuk Maintenance', 'Diesel', 'Food', 'Electricity', 'Others', 'Insurance', 'Licenses', 'Vehicle Purchase', 'Marketing'], required: true },
                { id: 'editFixedRecipient', name: 'recipient', label: 'Recipient', type: 'text', value: entry.recipient, required: false }, // THIS IS THE KEY CHANGE
                { id: 'editFixedCostDate', name: 'cost_date', label: 'Date', type: 'date', value: entry.cost_date, required: true },
                { id: 'editFixedPaymentMethod', name: 'payment_method', label: 'Payment Method', type: 'select', value: entry.payment_method, options: ['Cash', 'Bank Transfer', 'Debit Card'], required: true }
            ];
        } else if (tableType === 'income') {
            fields = [
                { id: 'editIncomeDate', name: 'income_date', label: 'Date', type: 'date', value: entry.income_date, required: true },
                { id: 'editToursRevenue', name: 'tours_revenue_eur', label: 'Tours Revenue (€)', type: 'number', step: '0.01', min: '0', value: entry.tours_revenue_eur, required: true },
                { id: 'editTransfersRevenue', name: 'transfers_revenue_eur', label: 'Transfers Revenue (€)', type: 'number', step: '0.01', min: '0', value: entry.transfers_revenue_eur, required: true },
                { id: 'editHoursWorked', name: 'hours_worked', label: 'Hours Worked', type: 'number', step: '0.01', min: '0', value: entry.hours_worked, required: true }
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
                // Use field.required if defined, otherwise default to true for selects that are usually required
                select.required = field.required !== undefined ? field.required : true; // Adjusted for selects
                
                // Add a default "Select..." option if the field is a payment method
                if (field.name === 'payment_method' || field.name === 'category' || field.name === 'cost_frequency') { // Also for category and cost_frequency
                    const defaultOption = document.createElement('option');
                    defaultOption.value = ""; // Empty value
                    defaultOption.textContent = `Select ${field.label.replace(':', '')}`; // Dynamic text
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
                // Use field.required if defined, otherwise default to true for inputs that are usually required
                input.required = field.required !== undefined ? field.required : true; // Adjusted for inputs
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
        // Removed: messageArea.style.display = 'none'; // This line was causing the issue
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
                showMessage('Entry updated successfully!', 'success'); // This line is correct
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
