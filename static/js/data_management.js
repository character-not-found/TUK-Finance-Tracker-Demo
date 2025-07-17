document.addEventListener('DOMContentLoaded', () => {
    const tableSelect = document.getElementById('tableSelect');
    const yearSelect = document.getElementById('yearSelect');
    const monthSelect = document.getElementById('monthSelect');
    const loadDataBtn = document.getElementById('loadDataBtn');
    const dataTable = document.getElementById('dataTable');
    const noDataMessage = document.getElementById('noDataMessage');
    const messageArea = document.getElementById('messageArea');
    const tableDataHeading = document.getElementById('tableDataHeading');

    const globalSearchInput = document.getElementById('globalSearchInput');
    const globalSearchBtn = document.getElementById('globalSearchBtn');

    const entryModal = document.getElementById('entryModal');
    const closeButton = document.querySelector('.close-button');
    const modalTitle = document.getElementById('modalTitle');
    const modalDocId = document.getElementById('modalDocId');
    const modalTableType = document.getElementById('modalTableType');
    const dynamicFormFields = document.getElementById('dynamicFormFields');
    const editForm = document.getElementById('editForm');
    const deleteBtn = document.getElementById('deleteBtn');
    const saveBtn = document.getElementById('saveBtn');

    let currentTableData = [];

    const currentYear = new Date().getFullYear();
    for (let i = currentYear; i >= 2020; i--) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        yearSelect.appendChild(option);
    }
    yearSelect.value = currentYear;

    function showMessage(message, type) {
        messageArea.textContent = message;
        messageArea.classList.remove('hidden', 'success', 'error');
        messageArea.classList.add('message', type);
        messageArea.classList.remove('hidden');

        setTimeout(() => {
            messageArea.classList.add('hidden');
        }, 5000);
    }

    function formatCurrency(value) {
        if (typeof value !== 'number' || isNaN(value)) return '0.00 €';
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            currencyDisplay: 'symbol'
        }).format(value);
    }

    function formatDateToDDMonthYYYY(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString + 'T00:00:00');
        const options = { day: '2-digit', month: 'long', year: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // NEW: Function to format date for mobile tables (DD/MM/YY)
    function formatDateToShortMobile(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString + 'T00:00:00');
        const options = { day: '2-digit', month: '2-digit', year: '2-digit' };
        return date.toLocaleDateString('en-GB', options); // Uses DD/MM/YY format
    }

    async function performDelete(docId, tableType) {
        try {
            const response = await fetch(`/${tableType}/${docId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                showMessage('Entry deleted successfully!', 'success');
                if (globalSearchInput.value.trim()) {
                    performGlobalSearch();
                } else {
                    loadTableData();
                }
                return true;
            } else {
                const errorData = await response.json();
                showMessage(`Error deleting entry: ${errorData.detail || response.statusText}`, 'error');
                console.error('Error deleting entry:', errorData);
                return false;
            }
        } catch (error) {
            showMessage(`Network error: ${error.message}`, 'error');
            console.error('Network error during delete:', error);
            return false;
        }
    }

    // Custom confirmation modal elements
    const confirmModal = document.getElementById('confirmModal');
    const confirmMessage = document.getElementById('confirmMessage');
    const confirmYesBtn = document.getElementById('confirmYes');
    const confirmNoBtn = document.getElementById('confirmNo');

    let confirmAction = null; // Stores the function to call on 'Yes'

    function showConfirmModal(message, onConfirm) {
        confirmMessage.textContent = message;
        confirmAction = onConfirm;
        confirmModal.style.display = 'flex'; // Show the modal
    }

    function hideConfirmModal() {
        confirmModal.style.display = 'none';
        confirmAction = null;
    }

    confirmYesBtn.addEventListener('click', () => {
        if (confirmAction) {
            confirmAction(true);
        }
        hideConfirmModal();
    });

    confirmNoBtn.addEventListener('click', () => {
        if (confirmAction) {
            confirmAction(false);
        }
        hideConfirmModal();
    });

    // Replace direct `confirm()` calls with `showConfirmModal`
    function handleDeleteRow(event) {
        const docId = event.target.dataset.docId;
        const tableType = event.target.dataset.tableType;
        showConfirmModal('Are you sure you want to delete this entry?', async (confirmed) => {
            if (confirmed) {
                await performDelete(docId, tableType);
            }
        });
    }

    function renderTable(data, tableType, isSearchMode = false) {
        const thead = dataTable.querySelector('thead tr');
        const tbody = dataTable.querySelector('tbody');
        thead.innerHTML = '';
        tbody.innerHTML = '';

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
        let headerAlignments = {};
        let cellAlignments = {};

        if (isSearchMode) {
            headers = ['ID', 'Source', 'Date', 'Description', 'Amount (€)', 'Payment Method', 'Actions'];
            headerAlignments = {
                'ID': 'text-center',
                'Source': 'text-left',
                'Date': 'text-left',
                'Description': 'text-left',
                'Amount (€)': 'text-right',
                'Payment Method': 'text-center',
                'Actions': 'text-center'
            };
            cellAlignments = {
                'ID': 'text-center',
                'Source': 'text-left',
                'Date': 'text-left',
                'Description': 'text-left',
                'Amount (€)': 'text-right',
                'Payment Method': 'text-center',
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
                'Payment Method': 'text-center',
                'Actions': 'text-center'
            };
            cellAlignments = {
                'doc_id': 'text-center',
                'cost_date': 'text-left',
                'description': 'text-left',
                'category': 'text-left',
                'amount': 'text-right',
                'payment_method': 'text-center',
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
                'Payment Method': 'text-center',
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
                'payment_method': 'text-center',
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

        headers.forEach(headerText => {
            const th = document.createElement('th');
            th.textContent = headerText;
            const alignmentClass = headerAlignments[headerText];
            if (alignmentClass) {
                th.classList.add(alignmentClass);
            }
            thead.appendChild(th);
        });

        data.forEach(item => {
            const row = tbody.insertRow();
            if (isSearchMode) {
                const sourceTable = item.sourceTable.replace('-', ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
                // NEW: Conditional date formatting for search results table
                const date = window.innerWidth < 768 ? formatDateToShortMobile(item.cost_date || item.income_date) : formatDateToDDMonthYYYY(item.cost_date || item.income_date);
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
                paymentMethodCell.classList.add(cellAlignments['Payment Method']);
                paymentMethodCell.textContent = paymentMethod;

                const actionCell = row.insertCell();
                actionCell.classList.add('actions');
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
                dataKeys.forEach(key => {
                    const cell = row.insertCell();
                    let value = item[key];
                    let alignmentClass = cellAlignments[key] || 'text-left';

                    if (key.includes('amount') || key.includes('revenue') || key.includes('eur')) {
                        value = formatCurrency(value);
                    } else if (key === 'cost_date' || key === 'income_date') {
                        // NEW: Conditional date formatting for regular tables
                        value = window.innerWidth < 768 ? formatDateToShortMobile(value) : formatDateToDDMonthYYYY(value);
                    } else if (key === 'payment_method' || key === 'category' || key === 'cost_frequency' || key === 'recipient') {
                        value = value ? value.replace(/_/g, ' ') : '-';
                    }

                    cell.classList.add(alignmentClass);
                    cell.textContent = value !== null && value !== undefined ? value : '-';
                });

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

    async function loadTableData() {
        const selectedTable = tableSelect.value;
        const selectedYear = yearSelect.value;
        const selectedMonth = monthSelect.value;

        let endpoint = `/${selectedTable}/`;
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            let data = await response.json();

            data = data.filter(item => {
                const itemDate = new Date((item.cost_date || item.income_date) + 'T00:00:00');
                const itemYear = itemDate.getFullYear();
                const itemMonth = itemDate.getMonth() + 1;

                const yearMatch = itemYear == selectedYear;
                const monthMatch = (selectedMonth === '0' || itemMonth == selectedMonth);

                return yearMatch && monthMatch;
            });

            data.sort((a, b) => {
                const dateA = new Date((a.cost_date || a.income_date) + 'T00:00:00');
                const dateB = new Date((b.cost_date || b.income_date) + 'T00:00:00');

                if (dateA.getTime() !== dateB.getTime()) {
                    return dateB - dateA;
                }
                return b.doc_id - a.doc_id;
            });

            currentTableData = data.map(item => ({ ...item, sourceTable: selectedTable }));

            renderTable(currentTableData, selectedTable, false);
        } catch (error) {
            console.error('Error loading table data:', error);
            showMessage(`Error loading data: ${error.message}`, 'error');
            renderTable([], selectedTable, false);
        }
    }

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
                    for (const key in item) {
                        if (typeof item[key] === 'string' && item[key].toLowerCase().includes(query)) {
                            match = true;
                            break;
                        }
                        if (typeof item[key] === 'number' && String(item[key]).includes(query)) {
                            match = true;
                            break;
                        }
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

            allResults.sort((a, b) => {
                const dateA = new Date((a.cost_date || a.income_date) + 'T00:00:00');
                const dateB = new Date((b.cost_date || b.income_date) + 'T00:00:00');

                if (dateA.getTime() !== dateB.getTime()) {
                    return dateB - dateA;
                }
                return b.doc_id - a.doc_id;
            });

            currentTableData = allResults;
            renderTable(allResults, null, true);

        } catch (error) {
            console.error('Error during global search:', error);
            showMessage(`Error during search: ${error.message}`, 'error');
            renderTable([], null, true);
        }
    }

    function openEditModal(event) {
        const docId = event.target.dataset.docId;
        const tableType = event.target.dataset.tableType;
        const entry = currentTableData.find(item => item.doc_id == docId && item.sourceTable === tableType);

        if (!entry) {
            showMessage('Entry not found for editing.', 'error');
            console.error(`Attempted to edit docId: ${docId}, tableType: ${tableType}, but entry not found in currentTableData:`, currentTableData);
            return;
        }

        modalTitle.textContent = `Edit ${tableType.replace('-', ' ').split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')} Entry (ID: ${docId})`;
        modalDocId.value = docId;
        modalTableType.value = tableType;
        dynamicFormFields.innerHTML = '';

        // Define a common class string for modal inputs/selects
        const modalInputClasses = "w-full p-2 border border-gray-300 rounded-md dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 focus:ring focus:ring-indigo-300 focus:border-indigo-300";

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
                { id: 'editFixedRecipient', name: 'recipient', label: 'Recipient', type: 'text', value: entry.recipient, required: false },
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
                select.required = field.required !== undefined ? field.required : true;
                select.classList.add(...modalInputClasses.split(' ')); // Add Tailwind classes

                if (field.name === 'payment_method' || field.name === 'category' || field.name === 'cost_frequency') {
                    const defaultOption = document.createElement('option');
                    defaultOption.value = "";
                    defaultOption.textContent = `Select ${field.label.replace(':', '')}`;
                    select.appendChild(defaultOption);
                }

                field.options.forEach(optionText => {
                    const option = document.createElement('option');
                    option.value = optionText;
                    option.textContent = optionText;
                    select.appendChild(option);
                });
                select.value = entry[field.name] || '';
                div.appendChild(select);
            } else {
                const input = document.createElement('input');
                input.id = field.id;
                input.name = field.name;
                input.type = field.type;
                input.value = entry[field.name];
                input.required = field.required !== undefined ? field.required : true;
                input.classList.add(...modalInputClasses.split(' ')); // Add Tailwind classes
                if (field.type === 'number') {
                    input.step = field.step;
                    input.min = field.min;
                }
                div.appendChild(input);
            }
            dynamicFormFields.appendChild(div);
        });

        entryModal.style.display = 'flex';
    }

    function closeModal() {
        entryModal.style.display = 'none';
    }

    editForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const docId = modalDocId.value;
        const tableType = modalTableType.value;
        const formData = new FormData(editForm);
        const updates = {};
        for (let [key, value] of formData.entries()) {
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

    deleteBtn.addEventListener('click', handleDeleteRow);

    loadDataBtn.addEventListener('click', loadTableData);
    globalSearchBtn.addEventListener('click', performGlobalSearch);
    globalSearchInput.addEventListener('keypress', (event) => {
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

    loadTableData();

    // NEW: Add a resize listener to re-render tables when switching between mobile/desktop
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            loadTableData();
        }, 200);
    });
});
