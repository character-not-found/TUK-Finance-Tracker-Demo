// Register the ChartDataLabels plugin globally
Chart.register(ChartDataLabels);

document.addEventListener('DOMContentLoaded', async () => {
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1; // Month is 0-indexed

    // Store chart instances globally to manage their lifecycle
    const chartInstances = {};

    // Function to format date from YYYY-MM-DD to DD Month YYYY
    function formatDateToDDMonthYYYY(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString + 'T00:00:00'); // Add T00:00:00 to avoid timezone issues
        const options = { day: '2-digit', month: 'long', year: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // Function to format currency in European style (e.g., 1 234,56 €)
    function formatCurrency(value) {
        if (typeof value !== 'number' || isNaN(value)) return '0.00 €';
        // Using 'fr-FR' locale for space as thousands separator, comma as decimal, and symbol after
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            currencyDisplay: 'symbol' // Displays '€'
        }).format(value);
    }

    // Function to get chart colors based on theme
    function getChartColors() {
        const isDarkMode = document.documentElement.classList.contains('dark');
        return {
            primaryTextColor: isDarkMode ? '#e2e8f0' : '#4b5563', // Light gray for dark, dark gray for light
            axisLineColor: isDarkMode ? '#4a5568' : 'rgba(229, 231, 235, 0.5)', // Darker gray for dark, light gray for light
            gridLineColor: isDarkMode ? 'rgba(74, 85, 104, 0.5)' : 'rgba(229, 231, 235, 0.5)', // Transparent darker gray for dark
            tooltipBgColor: isDarkMode ? '#2d3748' : '#ffffff',
            tooltipBorderColor: isDarkMode ? '#4a5568' : '#e5e7eb',
            tooltipTextColor: isDarkMode ? '#e2e8f0' : '#4b5563'
        };
    }

    // Function to fetch and display table data
    async function fetchData(endpoint, tableId, noDataMessageId, headers) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            let data = await response.json();
            const tableBody = document.getElementById(tableId).querySelector('tbody');
            const noDataMessage = document.getElementById(noDataMessageId);

            tableBody.innerHTML = ''; // Clear existing data

            if (data.length === 0) {
                noDataMessage.classList.remove('hidden');
                return;
            } else {
                noDataMessage.classList.add('hidden');
            }

            // Sort data: primary by date (desc), secondary by doc_id (desc)
            data.sort((a, b) => {
                const dateA = new Date(a.cost_date || a.income_date);
                const dateB = new Date(b.cost_date || b.income_date);

                // Primary sort by date (descending)
                if (dateA.getTime() !== dateB.getTime()) {
                    return dateB - dateA;
                }

                // Secondary sort by doc_id (descending) if dates are the same
                return b.doc_id - a.doc_id;
            });

            // Limit to top 10 most recent items
            data = data.slice(0, 10);

            data.forEach(item => {
                const row = tableBody.insertRow();
                headers.forEach(headerKey => {
                    const cell = row.insertCell();
                    let value = item[headerKey];

                    // Apply text-right class to currency columns and format currency
                    if (headerKey.includes('amount') || headerKey.includes('revenue') || headerKey.includes('eur')) {
                        cell.classList.add('text-right');
                        value = formatCurrency(value); // Use new currency formatter
                    }
                    // Special handling for hours_worked to be centered
                    else if (tableId === 'incomeTable' && headerKey === 'hours_worked') {
                        cell.classList.add('text-center'); // Added text-center class
                        value = value !== null && value !== undefined ? value : '-';
                    }
                    // Format dates and ensure left alignment (default)
                    else if (headerKey === 'cost_date' || headerKey === 'income_date') {
                        value = formatDateToDDMonthYYYY(value);
                        // No class added, so it defaults to left-aligned
                    }
                    // Handle enum values for display and ensure left alignment (default)
                    else if ((headerKey === 'cost_frequency' || headerKey === 'category') && item[headerKey]) {
                        value = item[headerKey].replace(/_/g, ' '); // Replace underscores for readability
                        // No class added, so it defaults to left-aligned
                    }
                    // Ensure ID, Description, and Recipient cells are left-aligned (default)
                    else if (headerKey === 'doc_id' || headerKey === 'description' || headerKey === 'recipient') {
                        // No class added, so it defaults to left-aligned
                    }

                    cell.textContent = value !== null && value !== undefined ? value : '-';
                });
            });
        } catch (error) {
            console.error(`Error fetching data for ${tableId}:`, error); // Keep error logs
            document.getElementById(noDataMessageId).textContent = `Error loading data: ${error.message}`;
            document.getElementById(noDataMessageId).classList.remove('hidden');
        }
    }

    // Function to fetch data and render a chart
    async function fetchAndRenderChart(endpoint, chartId, noDataMessageId, chartType, dataProcessor, options = {}) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const rawData = await response.json();
            const noDataMessage = document.getElementById(noDataMessageId);
            const canvas = document.getElementById(chartId);
            // Correctly target total display divs based on chartId
            const totalDisplayDiv = (chartId === 'monthlyExpenseCategoriesPieChart') ? document.getElementById('totalMonthlyExpensesDisplay') :
                                    (chartId === 'monthlyIncomeChart') ? document.getElementById('totalMonthlyIncomeDisplay') :
                                    (chartId === 'globalSummaryChart') ? document.getElementById('totalGlobalSummaryDisplay') : null;

            console.log(`[${chartId}] Fetching data. Raw data:`, rawData); // Debugging log

            if (Object.keys(rawData).length === 0 || (Array.isArray(rawData) && rawData.length === 0)) {
                noDataMessage.classList.remove('hidden');
                if (canvas) canvas.style.display = 'none'; // Hide canvas if no data
                if (totalDisplayDiv) {
                    totalDisplayDiv.classList.add('hidden');
                    console.log(`[${chartId}] Total display hidden due to no data.`); // Debugging log
                }
                console.log(`[${chartId}] No data. Hiding chart and total display.`); // Debugging log
                return;
            } else {
                noDataMessage.classList.add('hidden');
                if (canvas) canvas.style.display = 'block'; // Show canvas if data is present
                // Only show totalDisplayDiv if it exists and there's data
                if (totalDisplayDiv) {
                    totalDisplayDiv.classList.remove('hidden');
                    console.log(`[${chartId}] Data found. Showing chart and total display.`); // Debugging log
                }
            }

            const chartData = dataProcessor(rawData, chartId); // Pass chartId to dataProcessor

            // Update total display for the monthly expense categories pie chart
            if (chartId === 'monthlyExpenseCategoriesPieChart' && rawData) {
                const totalExpenses = Object.values(rawData).reduce((sum, val) => sum + val, 0);
                if (totalDisplayDiv) {
                    totalDisplayDiv.textContent = `Total: ${formatCurrency(totalExpenses)}`;
                    console.log(`[${chartId}] Calculated Total: ${formatCurrency(totalExpenses)}`); // Debugging log
                } else {
                    console.log(`[${chartId}] totalDisplayDiv not found for updating text (after data processing).`); // Debugging log
                }
            }
            // Update total display for the monthly income pie chart
            if (chartId === 'monthlyIncomeChart' && rawData) {
                const totalIncome = Object.values(rawData).reduce((sum, val) => sum + val, 0);
                    if (totalDisplayDiv) {
                    totalDisplayDiv.textContent = `Total: ${formatCurrency(totalIncome)}`;
                    console.log(`[${chartId}] Calculated Total: ${formatCurrency(totalIncome)}`); // Debugging log
                } else {
                    console.log(`[${chartId}] totalDisplayDiv not found for updating text (after data processing).`); // Debugging log
                }
            }
            // Update total display for the global summary chart
            if (chartId === 'globalSummaryChart' && rawData) {
                const totalProfit = rawData.net_global_profit;
                if (totalDisplayDiv) {
                    totalDisplayDiv.textContent = `Net Profit/Loss: ${formatCurrency(totalProfit)}`;
                    totalDisplayDiv.style.color = totalProfit >= 0 ? 'green' : 'red';
                    console.log(`[${chartId}] Calculated Global Profit/Loss: ${formatCurrency(totalProfit)}`); // Debugging log
                } else {
                    console.log(`[${chartId}] totalGlobalSummaryDisplay not found for updating text (after data processing).`); // Debugging log
                }
            }

            const colors = getChartColors(); // Get colors based on theme

            // Destroy existing chart instance if it exists
            if (chartInstances[chartId]) {
                chartInstances[chartId].destroy();
                delete chartInstances[chartId];
            }

            // Specific options for pie charts to show percentages statically and values in tooltips
            if (chartType === 'pie' || chartType === 'doughnut') {
                options.plugins = options.plugins || {};
                options.plugins.tooltip = options.plugins.tooltip || {};
                options.plugins.tooltip.callbacks = options.plugins.tooltip.callbacks || {};

                // Tooltip callback to show ONLY value (no percentage)
                options.plugins.tooltip.callbacks.label = function(context) {
                    let label = context.label || '';
                    if (label) {
                        label += ': ';
                    }
                    if (context.parsed !== null) {
                        const value = context.parsed;
                        label += `${formatCurrency(value)}`; // Only show the formatted amount
                    }
                    return label;
                };

                // Datalabels plugin configuration for static percentages
                options.plugins.datalabels = {
                    color: colors.primaryTextColor, // Changed to dynamic color for better contrast
                    formatter: (value, context) => {
                        const total = context.chart.data.datasets[0].data.reduce((sum, current) => sum + current, 0);
                        const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0; // One decimal place for percentage
                        return percentage + '%';
                    },
                    font: {
                        weight: 'bold',
                        size: 12,
                    }
                };

                // Move legend to bottom
                options.plugins.legend = {
                    position: 'bottom',
                    labels: {
                        color: colors.primaryTextColor // Set legend text color dynamically
                    }
                };

                // Remove scales/axis grid for pie charts
                options.scales = {
                    x: {
                        display: false,
                        grid: { display: false },
                        ticks: { display: false }
                    },
                    y: {
                        display: false,
                        grid: { display: false },
                        ticks: { display: false }
                    }
                };

            } else {
                // Default legend position for non-pie charts (if not already set in options)
                options.plugins = options.plugins || {};
                options.plugins.legend = options.plugins.legend || { position: 'top' };
            }


            chartInstances[chartId] = new Chart(canvas, {
                type: chartType,
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        // Default plugins for non-pie charts, overridden by specific pie chart options
                        legend: {
                            position: 'top',
                            labels: {
                                color: colors.primaryTextColor // Set legend text color dynamically
                            }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let label = context.dataset.label || '';
                                    if (label) {
                                        label += ': ';
                                    }
                                    if (context.parsed.y !== null) {
                                        label += formatCurrency(context.parsed.y);
                                    }
                                    return label;
                                }
                            },
                            backgroundColor: colors.tooltipBgColor, // Set tooltip background
                            borderColor: colors.tooltipBorderColor, // Set tooltip border
                            titleColor: colors.tooltipTextColor, // Set tooltip title color
                            bodyColor: colors.tooltipTextColor // Set tooltip body text color
                        }
                    },
                    scales: { // Apply dynamic colors to scales for bar charts
                        x: {
                            grid: {
                                color: colors.gridLineColor // Dynamic grid line color
                            },
                            ticks: {
                                color: colors.primaryTextColor // Dynamic tick label color
                            },
                            title: {
                                display: true,
                                text: 'Amount (€)',
                                color: colors.primaryTextColor // Dynamic axis title color
                            }
                        },
                        y: {
                            grid: {
                                color: colors.gridLineColor // Dynamic grid line color
                            },
                            ticks: {
                                color: colors.primaryTextColor // Dynamic tick label color
                            },
                            title: {
                                display: false // No title needed for categories
                            }
                        }
                    },
                    ...options // Merge custom options (which might override default plugins for pie charts)
                }
            });
        } catch (error) {
            console.error(`Error fetching or rendering chart for ${chartId}:`, error); // Keep error logs
            if (canvas) canvas.style.display = 'none'; // Hide canvas on error
            document.getElementById(noDataMessageId).textContent = `Error loading data: ${error.message}`;
            document.getElementById(noDataMessageId).classList.remove('hidden');
            const totalDisplayDiv = (chartId === 'monthlyExpenseCategoriesPieChart') ? document.getElementById('totalMonthlyExpensesDisplay') :
                                    (chartId === 'monthlyIncomeChart') ? document.getElementById('totalMonthlyIncomeDisplay') :
                                    (chartId === 'globalSummaryChart') ? document.getElementById('totalGlobalSummaryDisplay') : null;
            if (totalDisplayDiv) totalDisplayDiv.classList.add('hidden');
        }
    }

    // Function to fetch and display Net Profit/Loss, Monthly Average Income, and Cash on Hand
    async function fetchAndDisplayProfitLossAverageAndCashOnHand() {
        const netProfitLossDisplay = document.getElementById('netProfitLossDisplay');
        const monthlyAverageValueDisplay = document.getElementById('monthlyAverageValueDisplay');
        const cashOnHandDisplay = document.getElementById('cashOnHandDisplay'); // Get the new element
        const noDataMessage = document.getElementById('noNetProfitLossChart');

        try {
            const monthlySummaryResponse = await fetch(`/summary/monthly?year=${currentYear}&month=${currentMonth}`);
            if (!monthlySummaryResponse.ok) throw new Error(`HTTP error! status: ${monthlySummaryResponse.status}`);
            const monthlySummaryData = await monthlySummaryResponse.json();

            const incomeTableResponse = await fetch('/income/');
            if (!incomeTableResponse.ok) throw new Error(`HTTP error! status: ${incomeTableResponse.status}`);
            const incomeTableData = await incomeTableResponse.json();

            const cashOnHandResponse = await fetch('/summary/cash-on-hand'); // Fetch cash on hand
            if (!cashOnHandResponse.ok) throw new Error(`HTTP error! status: ${cashOnHandResponse.status}`);
            const cashOnHandData = await cashOnHandResponse.json();

            // Corrected key name from 'net_profit' to 'net_monthly_profit'
            if (!monthlySummaryData || monthlySummaryData.net_monthly_profit === undefined) {
                noDataMessage.classList.remove('hidden');
                netProfitLossDisplay.textContent = '';
                monthlyAverageValueDisplay.textContent = '';
                cashOnHandDisplay.textContent = ''; // Clear cash on hand if no monthly data
                return;
            }

            noDataMessage.classList.add('hidden');
            const netProfit = monthlySummaryData.net_monthly_profit; // Corrected key name
            netProfitLossDisplay.textContent = formatCurrency(netProfit);
            netProfitLossDisplay.style.color = netProfit >= 0 ? 'green' : 'red';

            // Calculate Monthly Average Income based on days with income
            const uniqueIncomeDates = new Set();
            incomeTableData.forEach(item => {
                const incomeDate = new Date(item.income_date);
                if (incomeDate.getFullYear() === currentYear && incomeDate.getMonth() + 1 === currentMonth) {
                    uniqueIncomeDates.add(item.income_date); // Add unique date string
                }
            });

            const daysWorked = uniqueIncomeDates.size;
            let totalMonthlyIncome = 0;
            // Recalculate total monthly income from incomeTableData for the current month
            incomeTableData.forEach(item => {
                const incomeDate = new Date(item.income_date);
                if (incomeDate.getFullYear() === currentYear && incomeDate.getMonth() + 1 === currentMonth) {
                    totalMonthlyIncome += (item.tours_revenue_eur || 0) + (item.transfers_revenue_eur || 0);
                }
            });

            const monthlyAverage = daysWorked > 0 ? totalMonthlyIncome / daysWorked : 0;
            monthlyAverageValueDisplay.textContent = formatCurrency(monthlyAverage);

            // Display Cash on Hand
            if (cashOnHandData && cashOnHandData.balance !== undefined) {
                cashOnHandDisplay.textContent = formatCurrency(cashOnHandData.balance);
                cashOnHandDisplay.style.color = cashOnHandData.balance >= 0 ? 'green' : 'red'; // Color based on balance
            } else {
                cashOnHandDisplay.textContent = 'N/A';
            }

        } catch (error) {
            console.error('Error fetching net profit/loss, monthly average, or cash on hand:', error);
            netProfitLossDisplay.textContent = 'Error loading data.';
            monthlyAverageValueDisplay.textContent = '';
            cashOnHandDisplay.textContent = 'Error loading data.'; // Show error for cash on hand too
            noDataMessage.textContent = `Error loading summary data: ${error.message}`;
            noDataMessage.classList.remove('hidden');
        }
    }


    // Original color palette
    const originalColors = [
        '#ef4444', // Red
        '#f97316', // Orange
        '#eab308', // Yellow
        '#22c55e', // Green
        '#0ea5e9', // Blue
        '#8b5cf6', // Violet
        '#ec4899', // Pink
        '#f43f5e', // Rose
        '#facc15', // Amber
        '#a3e635'  // Lime
    ];

    // Softer red hues for expenses - updated for better contrast
    const softerRedHues = [
        '#CD5C5C', // Indian Red (darker for contrast)
        '#E57373', // Light Red
        '#FFB6C1', // Light Pink
        '#FFA07A', // Light Salmon
        '#FA8072', // Salmon
        '#F08080', // Light Coral
        '#E9967A', // Dark Salmon
        '#DB7093', // Pale Violet Red
        '#FFD1DC', // Pale Pink
        '#BC8F8F'  // Rosy Brown
    ];

    // Softer green hues for income
    const softerGreenHues = [
        '#8BC34A', // Light Green
        '#AED581', // Light Green (lighter)
        '#C5E1A5', // Light Green (paler)
        '#DCE775', // Lime Green (soft)
        '#9CCC65', // Green (medium)
        '#7CB342'  // Light Green (darker)
    ];

    // Softer blue hues for profit/loss
    const softerBlueHues = [
        '#64B5F6', // Light Blue
        '#90CAF9', // Lighter Blue
        '#BBDEFB', // Pale Blue
        '#E3F2FD'  // Very Light Blue
    ];


    // Data Processers for Charts
    const processCategoryData = (data, chartId) => { // Accept chartId
        const labels = Object.keys(data);
        const values = Object.values(data);

        let colorsToUse;
        if (chartId === 'monthlyExpenseCategoriesPieChart') {
            colorsToUse = softerRedHues; // Use softer red hues for expenses
        } else { // For income sources chart
            colorsToUse = originalColors; // Use original colors for Income Sources (as requested)
        }

        return {
            labels: labels,
            datasets: [{
                label: 'Amount (€)',
                data: values,
                backgroundColor: colorsToUse.slice(0, labels.length),
                borderColor: colorsToUse.slice(0, labels.length),
                borderWidth: 1
            }]
        };
    };

    // New data processor for Monthly Income pie chart (Tours vs Transfers)
    const processMonthlyIncomeData = (data) => {
        const labels = [];
        const values = [];

        if (data.Tours !== undefined) {
            labels.push('Tours');
            values.push(data.Tours);
        }
        if (data.Transfers !== undefined) {
            labels.push('Transfers');
            values.push(data.Transfers);
        }

        if (labels.length === 0) {
            Object.keys(data).forEach(key => {
                labels.push(key);
                values.push(data[key]);
            });
        }

        return {
            labels: labels,
            datasets: [{
                label: 'Amount (€)',
                data: values,
                backgroundColor: softerGreenHues.slice(0, labels.length),
                borderColor: softerGreenHues.slice(0, labels.length),
                borderWidth: 1
            }]
        };
    };

    // Data processor for Global Summary
    const processGlobalSummary = (data) => {
        return {
            labels: ['Total Expenses', 'Total Income', 'Net Profit/Loss'], // Labels for global summary
            datasets: [{
                label: 'Amount (€)',
                data: [data.total_global_expenses, data.total_global_income, data.net_global_profit], // Use global data keys
                backgroundColor: [softerRedHues[0], softerGreenHues[0], softerBlueHues[0]], // Softer Red, Green, Blue
                borderColor: [softerRedHues[0], softerGreenHues[0], softerBlueHues[0]],
                borderWidth: 1
            }]
        };
    };

    // Function to re-render all charts and summary displays
    async function renderAllDashboardElements() {
        // Fetch and render charts
        await fetchAndRenderChart(`/summary/expense-categories?year=${currentYear}&month=${currentMonth}`, 'monthlyExpenseCategoriesPieChart', 'noMonthlyExpenseCategoriesPieChart', 'pie', processCategoryData);
        await fetchAndRenderChart(`/summary/income-sources?year=${currentYear}&month=${currentMonth}`, 'monthlyIncomeChart', 'noMonthlyIncomeChart', 'pie', processMonthlyIncomeData);
        await fetchAndDisplayProfitLossAverageAndCashOnHand();
        await fetchAndRenderChart(`/summary/global`, 'globalSummaryChart', 'noGlobalSummaryChart', 'bar', processGlobalSummary, {
                indexAxis: 'y', // Makes the bar chart horizontal
                scales: {
                    x: { // x-axis for horizontal bar chart
                        beginAtZero: true,
                        title: { display: true, text: 'Amount (€)', color: getChartColors().primaryTextColor }, // Dynamic title color
                        ticks: { callback: function(value) { return formatCurrency(value); }, color: getChartColors().primaryTextColor }, // Dynamic label color
                        grid: { color: getChartColors().gridLineColor } // Dynamic grid line color
                    },
                    y: { // y-axis for horizontal bar chart
                        title: { display: false }, // No title needed for categories
                        ticks: { color: getChartColors().primaryTextColor }, // Dynamic label color
                        grid: { color: getChartColors().gridLineColor } // Dynamic grid line color
                    }
                },
                plugins: {
                    legend: {
                        display: false // Hide legend for simplicity as labels are on bars
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.x !== null) { // Use context.parsed.x for horizontal bar chart
                                    label += formatCurrency(context.parsed.x);
                                }
                                return label;
                            }
                        }
                    },
                    datalabels: { // Add datalabels for values on bars
                        color: getChartColors().primaryTextColor, // Dynamic color for better contrast
                        anchor: 'end',
                        align: 'start',
                        formatter: (value) => formatCurrency(value),
                        font: {
                            weight: 'bold',
                            size: 12
                        }
                    }
                }
        });
    }


    // Fetch and display data for tables
    const incomeHeaders = ['doc_id', 'income_date', 'tours_revenue_eur', 'transfers_revenue_eur', 'daily_total_eur', 'hours_worked'];
    const dailyExpensesHeaders = ['doc_id', 'cost_date', 'description', 'category', 'amount'];
    const fixedCostsHeaders = ['doc_id', 'cost_date', 'description', 'cost_frequency', 'category', 'recipient', 'amount_eur'];

    await fetchData('/income/', 'incomeTable', 'noIncome', incomeHeaders);
    await fetchData('/daily-expenses/', 'dailyExpensesTable', 'noDailyExpenses', dailyExpensesHeaders);
    await fetchData('/fixed-costs/', 'fixedCostsTable', 'noFixedCosts', fixedCostsHeaders);

    // Initial render of all elements
    renderAllDashboardElements();

    // Setup MutationObserver to watch for theme changes (dark mode class on <html>)
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                console.log('HTML class attribute changed. Re-rendering charts.');
                renderAllDashboardElements(); // Re-render all charts and summary displays
            }
        });
    });

    // Start observing the <html> element for attribute changes
    observer.observe(document.documentElement, { attributes: true });
});
