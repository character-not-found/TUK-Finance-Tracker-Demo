Chart.register(ChartDataLabels);

document.addEventListener('DOMContentLoaded', async () => {
    let currentYear = new Date().getFullYear();
    let currentMonth = new Date().getMonth() + 1;
    let currentDay = new Date().getDate(); // Added for "last week" logic

    const chartInstances = {};

    function formatDateToDDMonthYYYY(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString + 'T00:00:00');
        const options = { day: '2-digit', month: 'long', year: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }

    // Function to format date for mobile tables (e.g., DD/MM/YY)
    function formatDateToShortMobile(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString + 'T00:00:00');
        const options = { day: '2-digit', month: '2-digit', year: '2-digit' };
        return date.toLocaleDateString('en-GB', options);
    }

    // NEW: Function to format a Date object to YYYY-MM-DD string using local date parts
    function formatLocalDateToYYYYMMDD(date) {
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function formatCurrency(value) {
        if (typeof value !== 'number' || isNaN(value)) return '0.00 €';
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            currencyDisplay: 'symbol'
        }).format(value);
    }

    function getChartColors() {
        const isDarkMode = document.documentElement.classList.contains('dark');
        return {
            primaryTextColor: isDarkMode ? '#e2e8f0' : '#4b5563',
            axisLineColor: isDarkMode ? '#4a5568' : 'rgba(229, 231, 235, 0.5)',
            gridLineColor: isDarkMode ? 'rgba(74, 85, 104, 0.5)' : 'rgba(229, 231, 235, 0.5)',
            tooltipBgColor: isDarkMode ? '#2d3748' : '#ffffff',
            tooltipBorderColor: isDarkMode ? '#4a5568' : '#e5e7eb',
            tooltipTextColor: isDarkMode ? '#e2e8f0' : '#4b5563'
        };
    }

    async function fetchData(endpoint, tableId, noDataMessageId, headers) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            let data = await response.json();
            const tableBody = document.getElementById(tableId).querySelector('tbody');
            const noDataMessage = document.getElementById(noDataMessageId);

            tableBody.innerHTML = '';

            if (data.length === 0) {
                noDataMessage.classList.remove('hidden');
                return;
            } else {
                noDataMessage.classList.add('hidden');
            }

            data.sort((a, b) => {
                const dateA = new Date(a.cost_date || a.income_date);
                const dateB = new Date(b.cost_date || b.income_date);

                if (dateA.getTime() !== dateB.getTime()) {
                    return dateB - dateA;
                }
                return b.doc_id - a.doc_id;
            });

            data = data.slice(0, 10);

            data.forEach(item => {
                const row = tableBody.insertRow();
                headers.forEach(headerKey => {
                    const cell = row.insertCell();
                    let value = item[headerKey];

                    if (headerKey === 'doc_id') {
                        cell.textContent = value !== null && value !== undefined ? value : '-';
                        return; // Skip other formatting for ID
                    }

                    if (headerKey.includes('amount') || headerKey.includes('revenue') || headerKey.includes('eur')) {
                        cell.classList.add('text-right');
                        value = formatCurrency(value);
                    } else if (headerKey === 'hours_worked' || headerKey === 'total_hours_worked') {
                        cell.classList.add('text-center');
                        value = value !== null && value !== undefined ? value : '-';
                    } else if (headerKey === 'cost_date' || headerKey === 'income_date') {
                        // NEW: Use short date format for mobile, full for desktop
                        if (window.innerWidth < 768) { // Check if screen is mobile
                            value = formatDateToShortMobile(value);
                        } else {
                            value = formatDateToDDMonthYYYY(value);
                        }
                    } else if ((headerKey === 'cost_frequency' || headerKey === 'category') && item[headerKey]) {
                        value = item[headerKey].replace(/_/g, ' ');
                    }

                    cell.textContent = value !== null && value !== undefined ? value : '-';
                });
            });
        } catch (error) {
            console.error(`Error fetching data for ${tableId}:`, error);
            document.getElementById(noDataMessageId).textContent = `Error loading data: ${error.message}`;
            document.getElementById(noDataMessageId).classList.remove('hidden');
        }
    }

    async function fetchAndRenderChart(endpoint, chartId, noDataMessageId, chartType, dataProcessor, options = {}) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const rawData = await response.json();
            const noDataMessage = document.getElementById(noDataMessageId);
            const canvas = document.getElementById(chartId);
            
            // Refine totalDisplayDiv identification for weekly summaries
            let totalDisplayDiv = null;
            if (chartId === 'monthlyExpenseCategoriesPieChart') {
                totalDisplayDiv = document.getElementById('totalMonthlyExpensesDisplay');
            } else if (chartId === 'monthlyIncomeChart') {
                totalDisplayDiv = document.getElementById('totalMonthlyIncomeDisplay');
            } else if (chartId === 'globalSummaryChart') {
                totalDisplayDiv = document.getElementById('totalGlobalSummaryDisplay');
            }
            // For weekly summaries, you might want new display divs or to repurpose existing ones
            // For simplicity, we'll reuse the existing ones for now if their context matches
            // If you add dedicated weekly display divs in HTML, update these IDs.

            if (Object.keys(rawData).length === 0 || (Array.isArray(rawData) && rawData.length === 0)) {
                noDataMessage.classList.remove('hidden');
                if (canvas) canvas.style.display = 'none';
                if (totalDisplayDiv) {
                    totalDisplayDiv.classList.add('hidden');
                }
                // If chart exists, destroy it when no data, to ensure a clean state
                if (chartInstances[chartId]) {
                    chartInstances[chartId].destroy();
                    delete chartInstances[chartId];
                }
                return;
            } else {
                noDataMessage.classList.add('hidden');
                if (canvas) canvas.style.display = 'block';
                if (totalDisplayDiv) {
                    totalDisplayDiv.classList.remove('hidden');
                }
            }

            const chartData = dataProcessor(rawData, chartId);

            // Update total display based on chartId
            if (chartId === 'monthlyExpenseCategoriesPieChart' && rawData) {
                const totalExpenses = Object.values(rawData).reduce((sum, val) => sum + val, 0);
                if (totalDisplayDiv) {
                    totalDisplayDiv.textContent = `Total: ${formatCurrency(totalExpenses)}`;
                }
            }
            if (chartId === 'monthlyIncomeChart' && rawData) {
                const totalIncome = Object.values(rawData).reduce((sum, val) => sum + val, 0);
                if (totalDisplayDiv) {
                    totalDisplayDiv.textContent = `Total: ${formatCurrency(totalIncome)}`;
                }
            }
            if (chartId === 'globalSummaryChart' && rawData) {
                const totalProfit = rawData.net_global_profit;
                if (totalDisplayDiv) {
                    totalDisplayDiv.textContent = `Net Profit/Loss: ${formatCurrency(totalProfit)}`;
                    totalDisplayDiv.style.color = totalProfit >= 0 ? 'green' : 'red';
                }
            }

            const colors = getChartColors();

            // Check if chart instance already exists
            if (chartInstances[chartId]) {
                // Update existing chart
                chartInstances[chartId].data = chartData;
                chartInstances[chartId].update(); // This will animate the data change
            } else {
                // Create new chart if it doesn't exist
                if (chartType === 'pie' || chartType === 'doughnut') {
                    options.plugins = options.plugins || {};
                    options.plugins.tooltip = options.plugins.tooltip || {};
                    options.plugins.tooltip.callbacks = options.plugins.tooltip.callbacks || {};

                    options.plugins.tooltip.callbacks.label = function(context) {
                        let label = context.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed !== null) {
                            const value = context.parsed;
                            label += `${formatCurrency(value)}`;
                        }
                        return label;
                    };

                    options.plugins.datalabels = {
                        color: colors.primaryTextColor,
                        formatter: (value, context) => {
                            const total = context.chart.data.datasets[0].data.reduce((sum, current) => sum + current, 0);
                            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                            return percentage + '%';
                        },
                        font: {
                            weight: 'bold',
                            size: 12,
                        }
                    };

                    options.plugins.legend = {
                        position: 'bottom',
                        labels: {
                            color: colors.primaryTextColor
                        }
                    };

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

                } else { // For bar charts (like income)
                    options.plugins = options.plugins || {};
                    options.plugins.legend = options.plugins.legend || { position: 'top' };
                    
                    // Add scales definition for bar charts if not already present in options
                    options.scales = options.scales || {};
                    options.scales.x = {
                        grid: { color: colors.gridLineColor },
                        ticks: { color: colors.primaryTextColor },
                        title: { display: true, text: 'Amount (€)', color: colors.primaryTextColor }
                    };
                    options.scales.y = {
                        title: { display: false },
                        ticks: { color: colors.primaryTextColor },
                        grid: { color: colors.gridLineColor }
                    };
                }

                chartInstances[chartId] = new Chart(canvas, {
                    type: chartType,
                    data: chartData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: {
                                    color: colors.primaryTextColor
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
                                backgroundColor: colors.tooltipBgColor,
                                borderColor: colors.tooltipBorderColor,
                                titleColor: colors.tooltipTextColor,
                                bodyColor: colors.tooltipTextColor
                            }
                        },
                        scales: options.scales || { // Use provided scales or default empty object
                            x: {
                                grid: { color: colors.gridLineColor },
                                ticks: { color: colors.primaryTextColor },
                                title: { display: true, text: 'Category', color: colors.primaryTextColor } // Default for bar chart x-axis
                            },
                            y: {
                                title: { display: true, text: 'Amount (€)', color: colors.primaryTextColor }, // Default for bar chart y-axis
                                ticks: { color: colors.primaryTextColor },
                                grid: { color: colors.gridLineColor }
                            }
                        },
                        ...options // Merge any additional options passed
                    }
                });
            }
        } catch (error) {
            console.error(`Error fetching or rendering chart for ${chartId}:`, error);
            if (canvas) canvas.style.display = 'none';
            document.getElementById(noDataMessageId).textContent = `Error loading data: ${error.message}`;
            document.getElementById(noDataMessageId).classList.remove('hidden');
            let totalDisplayDiv = null; // Re-initialize as it's in a catch block
            if (chartId === 'monthlyExpenseCategoriesPieChart') {
                totalDisplayDiv = document.getElementById('totalMonthlyExpensesDisplay');
            } else if (chartId === 'monthlyIncomeChart') {
                totalDisplayDiv = document.getElementById('totalMonthlyIncomeDisplay');
            } else if (chartId === 'globalSummaryChart') {
                totalDisplayDiv = document.getElementById('totalGlobalSummaryDisplay');
            }
            if (totalDisplayDiv) totalDisplayDiv.classList.add('hidden');
        }
    }

    async function fetchAndDisplayProfitLossAverageAndCashOnHand(year, month, startDate = null, endDate = null) {
        let summaryEndpoint;
        let averageIncomeEndpoint;
        const averageIncomeTitle = document.getElementById('monthlyAverageProfitLossTitle');
        const monthlyAverageValueDisplay = document.getElementById('monthlyAverageValueDisplay');
        const netProfitLossDisplay = document.getElementById('netProfitLossDisplay');
        const cashOnHandDisplay = document.getElementById('cashOnHandDisplay');
        const noDataMessage = document.getElementById('noNetProfitLossChart');

        if (netProfitLossDisplay) netProfitLossDisplay.textContent = '';
        if (monthlyAverageValueDisplay) monthlyAverageValueDisplay.textContent = '';
        if (cashOnHandDisplay) cashOnHandDisplay.textContent = '';
        if (noDataMessage) noDataMessage.classList.add('hidden');

        if (startDate && endDate) {
            const formattedStartDate = startDate.toISOString().split('T')[0];
            const formattedEndDate = endDate.toISOString().split('T')[0];
            summaryEndpoint = `/summary/weekly?start_date=${formattedStartDate}&end_date=${formattedEndDate}`;
            averageIncomeEndpoint = `/summary/daily-income-average?start_date=${formattedStartDate}&end_date=${formattedEndDate}`;
            if (averageIncomeTitle) {
                averageIncomeTitle.textContent = 'Weekly Daily Income Average';
            }
        } else {
            summaryEndpoint = `/summary/monthly?year=${year}&month=${month}`;
            
            const firstDayOfMonth = new Date(year, month - 1, 1);
            const lastDayOfMonth = new Date(year, month, 0);
            const formattedStartDate = firstDayOfMonth.toISOString().split('T')[0];
            const formattedEndDate = lastDayOfMonth.toISOString().split('T')[0];
            
            averageIncomeEndpoint = `/summary/daily-income-average?start_date=${formattedStartDate}&end_date=${formattedEndDate}`;
            if (averageIncomeTitle) {
                averageIncomeTitle.textContent = 'Monthly Daily Income Average';
            }
        }

        try {
            const summaryResponse = await fetch(summaryEndpoint);
            if (!summaryResponse.ok) {
                throw new Error(`HTTP error! status: ${summaryResponse.status}`);
            }
            const summaryData = await summaryResponse.json();

            if (netProfitLossDisplay) {
                let netProfitToDisplay;

                if (startDate && endDate) {
                    netProfitToDisplay = summaryData.net_weekly_profit;
                } else {
                    netProfitToDisplay = summaryData.net_monthly_profit;
                }

                if (netProfitToDisplay !== undefined && netProfitToDisplay !== null) {
                    netProfitLossDisplay.textContent = formatCurrency(netProfitToDisplay);
                    netProfitLossDisplay.style.color = netProfitToDisplay >= 0 ? 'green' : 'red';
                } else {
                    netProfitLossDisplay.textContent = 'N/A';
                }
            }

            const averageIncomeResponse = await fetch(averageIncomeEndpoint);
            if (!averageIncomeResponse.ok) {
                throw new Error(`HTTP error! status: ${averageIncomeResponse.status}`);
            }
            const averageIncomeData = await averageIncomeResponse.json();
            
            if (monthlyAverageValueDisplay) { 
                if (averageIncomeData.daily_average_income !== undefined && averageIncomeData.daily_average_income !== null) {
                    monthlyAverageValueDisplay.textContent = formatCurrency(averageIncomeData.daily_average_income);
                    monthlyAverageValueDisplay.style.color = averageIncomeData.daily_average_income >= 0 ? 'green' : 'red';
                } else {
                    monthlyAverageValueDisplay.textContent = 'N/A';
                }
            }

            const cashOnHandResponse = await fetch('/summary/cash-on-hand');
            if (!cashOnHandResponse.ok) {
                throw new Error(`HTTP error! status: ${cashOnHandResponse.status}`);
            }
            const cashOnHandData = await cashOnHandResponse.json();
            if (cashOnHandDisplay) {
                if (cashOnHandData.balance !== undefined && cashOnHandData.balance !== null) {
                    cashOnHandDisplay.textContent = formatCurrency(cashOnHandData.balance);
                    cashOnHandDisplay.style.color = cashOnHandData.balance >= 0 ? 'green' : 'red';
                } else {
                    cashOnHandDisplay.textContent = 'N/A'; // Or an appropriate default
                }
            }

        } catch (error) {
            console.error('Error fetching dashboard summary data or daily average income:', error);
            if (netProfitLossDisplay) netProfitLossDisplay.textContent = 'Error';
            if (monthlyAverageValueDisplay) monthlyAverageValueDisplay.textContent = 'Error';
            if (cashOnHandDisplay) cashOnHandDisplay.textContent = 'Error';
            
            if (averageIncomeTitle) {
                averageIncomeTitle.textContent = (startDate && endDate) ? 'Weekly Daily Income Average (Error)' : 'Monthly Daily Income Average (Error)';
            }
            if (noDataMessage) {
                noDataMessage.textContent = `Error loading summary data: ${error.message}`;
                noDataMessage.classList.remove('hidden');
            }
        }
    }

    const originalColors = [
        '#ef4444',
        '#f97316',
        '#eab308',
        '#22c55e',
        '#0ea5e9',
        '#8b5cf6',
        '#ec4899',
        '#f43f5e',
        '#facc15',
        '#a3e635'
    ];

    const softerRedHues = [
        '#CD5C5C',
        '#E57373',
        '#FFB6C1',
        '#FFA07A',
        '#FA8072',
        '#F08080',
        '#E9967A',
        '#DB7093',
        '#FFD1DC',
        '#BC8F8F'
    ];

    const softerGreenHues = [
        '#8BC34A',
        '#AED581',
        '#C5E1A5',
        '#DCE775',
        '#9CCC65',
        '#7CB342'
    ];

    const softerBlueHues = [
        '#64B5F6',
        '#90CAF9',
        '#BBDEFB',
        '#E3F2FD'
    ];

    const processCategoryData = (data, chartId) => {
        const labels = Object.keys(data);
        const values = Object.values(data);

        let colorsToUse;
        if (chartId === 'monthlyExpenseCategoriesPieChart') {
            colorsToUse = softerRedHues;
        } else {
            colorsToUse = originalColors;
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

    const processGlobalSummary = (data) => {
        return {
            labels: ['Total Expenses', 'Total Income', 'Net Profit/Loss'],
            datasets: [{
                label: 'Amount (€)',
                data: [data.total_global_expenses, data.total_global_income, data.net_global_profit],
                backgroundColor: [softerRedHues[0], softerGreenHues[0], softerBlueHues[0]],
                borderColor: [softerRedHues[0], softerGreenHues[0], softerBlueHues[0]],
                borderWidth: 1
            }]
        };
    };

    async function updateDashboardChartsAndCards(year, month, startDate = null, endDate = null) {
        const periodText = (startDate && endDate) ? "Weekly" : "Monthly";
        
        document.getElementById('expensesChartTitle').textContent = `${periodText} Expenses`;
        document.getElementById('incomeChartTitle').textContent = `${periodText} Income`;
        
        let expenseCategoriesEndpoint;
        let incomeSourcesEndpoint;

        if (startDate && endDate) {
            const formattedStartDate = startDate.toISOString().split('T')[0];
            const formattedEndDate = endDate.toISOString().split('T')[0];
            expenseCategoriesEndpoint = `/summary/weekly-expense-categories?start_date=${formattedStartDate}&end_date=${formattedEndDate}`;
            incomeSourcesEndpoint = `/summary/weekly-income-sources?start_date=${formattedStartDate}&end_date=${formattedEndDate}`;
        } else {
            expenseCategoriesEndpoint = `/summary/expense-categories?year=${year}&month=${month}`;
            incomeSourcesEndpoint = `/summary/income-sources?year=${year}&month=${month}`;
        }

        await fetchAndRenderChart(expenseCategoriesEndpoint, 'monthlyExpenseCategoriesPieChart', 'noMonthlyExpenseCategoriesPieChart', 'pie', processCategoryData);
        await fetchAndRenderChart(incomeSourcesEndpoint, 'monthlyIncomeChart', 'noMonthlyIncomeChart', 'pie', processMonthlyIncomeData);
        
        await fetchAndDisplayProfitLossAverageAndCashOnHand(year, month, startDate, endDate);
    }

    async function fetchAndCompareDailyIncome(comparisonType) {
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Normalize to start of today's local date

        let comparisonDate = new Date(today); // Start with today's date
        let comparisonDateText = '';
        let timePeriodText = '';

        if (comparisonType === 'lastWeek') {
            comparisonDate.setDate(today.getDate() - 7); // Correctly sets to this day last week
            comparisonDateText = formatDateToDDMonthYYYY(formatLocalDateToYYYYMMDD(comparisonDate)); // Use new local date formatter
            timePeriodText = 'last week';
        } else if (comparisonType === 'lastMonth') {
            comparisonDate.setMonth(today.getMonth() - 1); // Sets to last month
            // This handles if the day doesn't exist in the previous month (e.g., 31st of March -> Feb 28/29)
            if (comparisonDate.getDate() !== today.getDate()) {
                comparisonDate.setDate(0); // Set to the last day of the previous month if day overflows
            }
            comparisonDateText = formatDateToDDMonthYYYY(formatLocalDateToYYYYMMDD(comparisonDate)); // Use new local date formatter
            timePeriodText = 'last month';
        } else {
            return;
        }

        // Use the new local date formatter for fetching data to ensure consistency
        const todayFormatted = formatLocalDateToYYYYMMDD(today);
        const comparisonDateFormatted = formatLocalDateToYYYYMMDD(comparisonDate);

        const incomeComparisonMessageDiv = document.getElementById('incomeComparisonMessage');
        const comparisonMessageTextP = document.getElementById('comparisonMessageText');

        // Reset visibility and styling for transition
        incomeComparisonMessageDiv.style.transition = 'opacity 0.5s ease-in-out'; // Set transition
        incomeComparisonMessageDiv.style.opacity = '0'; // Start hidden for fade-in
        incomeComparisonMessageDiv.classList.remove('hidden'); // Ensure it's not display: none

        // Ensure blue styling
        incomeComparisonMessageDiv.classList.remove('bg-green-100', 'border-green-500', 'text-green-700', 'bg-red-100', 'border-red-500', 'text-red-700');
        incomeComparisonMessageDiv.classList.add('bg-blue-100', 'border-blue-500', 'text-blue-700');


        try {
            const todayIncomeResponse = await fetch(`/income/daily-summary?date_param=${todayFormatted}`);
            if (!todayIncomeResponse.ok) throw new Error(`HTTP error! status: ${todayIncomeResponse.status} for today's income`);
            const todayIncomeData = await todayIncomeResponse.json();

            const comparisonIncomeResponse = await fetch(`/income/daily-summary?date_param=${comparisonDateFormatted}`);
            if (!comparisonIncomeResponse.ok) throw new Error(`HTTP error! status: ${comparisonIncomeResponse.status} for comparison day's income`);
            const comparisonIncomeData = await comparisonIncomeResponse.json();

            const todayTotal = todayIncomeData.total_daily_income_eur || 0;
            const comparisonTotal = comparisonIncomeData.total_daily_income_eur || 0;
            const comparisonTours = comparisonIncomeData.total_tours_revenue_eur || 0;
            const comparisonTransfers = comparisonIncomeData.total_transfers_revenue_eur || 0;

            let message;
            const incomeDifference = comparisonTotal - todayTotal; // How much more is needed to reach comparisonTotal

            if (incomeDifference > 0) {
                message = `Today you did ${formatCurrency(todayTotal)}. On ${comparisonDateText} you did a total ${formatCurrency(comparisonTotal)}: ${formatCurrency(comparisonTours)} in Tours, and ${formatCurrency(comparisonTransfers)} in Transfers. You're getting there, only ${formatCurrency(incomeDifference)} more to reach the income from last ${timePeriodText}.`;
            } else {
                message = `Today you did ${formatCurrency(todayTotal)}. On ${comparisonDateText} you did a total ${formatCurrency(comparisonTotal)}: ${formatCurrency(comparisonTours)} in Tours, and ${formatCurrency(comparisonTransfers)} in Transfers. You surpassed the income from last ${timePeriodText} by ${formatCurrency(Math.abs(incomeDifference))}.`;
            }
            
            comparisonMessageTextP.textContent = message;
            
            // Trigger fade-in
            setTimeout(() => {
                incomeComparisonMessageDiv.style.opacity = '1';
            }, 50); // Small delay to ensure transition applies

            // Trigger fade-out after 10 seconds
            setTimeout(() => {
                incomeComparisonMessageDiv.style.opacity = '0';
                // After transition, hide it completely
                setTimeout(() => {
                    incomeComparisonMessageDiv.classList.add('hidden');
                }, 500); // Matches CSS transition duration
            }, 10000); // 10 seconds

        } catch (error) {
            console.error('Error fetching daily income for comparison:', error);
            comparisonMessageTextP.textContent = `Error loading comparison data: ${error.message}`;
            
            // Ensure error message also fades out after 10 seconds
            setTimeout(() => {
                incomeComparisonMessageDiv.style.opacity = '0';
                setTimeout(() => {
                    incomeComparisonMessageDiv.classList.add('hidden');
                }, 500);
            }, 10000);

            // Trigger fade-in for error message
            setTimeout(() => {
                incomeComparisonMessageDiv.style.opacity = '1';
            }, 50);
        }
    }

    async function renderAllDashboardElements() {
        await updateDashboardChartsAndCards(currentYear, currentMonth);

        await fetchAndRenderChart(`/summary/global`, 'globalSummaryChart', 'noGlobalSummaryChart', 'bar', processGlobalSummary, {
                indexAxis: 'y',
                scales: {
                    x: {
                        beginAtZero: true,
                        title: { display: true, text: 'Amount (€)', color: getChartColors().primaryTextColor },
                        ticks: { callback: function(value) { return formatCurrency(value); }, color: getChartColors().primaryTextColor },
                        grid: { color: getChartColors().gridLineColor }
                    },
                    y: {
                        title: { display: false },
                        ticks: { color: getChartColors().primaryTextColor },
                        grid: { color: getChartColors().gridLineColor }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.x !== null) {
                                    label += formatCurrency(context.parsed.x);
                                }
                                return label;
                            }
                        }
                    },
                    datalabels: {
                        color: getChartColors().primaryTextColor,
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


    const incomeHeaders = ['income_date', 'total_tours_revenue_eur', 'total_transfers_revenue_eur', 'total_daily_income_eur', 'total_hours_worked'];
    const dailyExpensesHeaders = ['doc_id', 'cost_date', 'description', 'category', 'payment_method', 'amount'];
    const fixedCostsHeaders = ['doc_id', 'cost_date', 'description', 'cost_frequency', 'category', 'recipient', 'payment_method', 'amount_eur'];

    // Initial data fetch and render for all elements
    await fetchData('/income/', 'incomeTable', 'noIncome', incomeHeaders);
    await fetchData('/daily-expenses/', 'dailyExpensesTable', 'noDailyExpenses', dailyExpensesHeaders);
    await fetchData('/fixed-costs/', 'fixedCostsTable', 'noFixedCosts', fixedCostsHeaders);
    renderAllDashboardElements();

    // Event Listeners for Date Range Buttons
    document.getElementById('currentMonthBtn').addEventListener('click', async () => {
        const today = new Date();
        currentYear = today.getFullYear();
        currentMonth = today.getMonth() + 1;
        await updateDashboardChartsAndCards(currentYear, currentMonth);
        setActiveButton('currentMonthBtn');
        hideComparisonMessage();
    });

    document.getElementById('lastMonthBtn').addEventListener('click', async () => {
        const today = new Date();
        let lastMonth = today.getMonth(); // 0-indexed
        let yearOfLastMonth = today.getFullYear();

        if (lastMonth === 0) { // If current month is January, last month is December of previous year
            lastMonth = 12;
            yearOfLastMonth -= 1;
        }
        currentYear = yearOfLastMonth;
        currentMonth = lastMonth;
        await updateDashboardChartsAndCards(currentYear, currentMonth);
        setActiveButton('lastMonthBtn');
        hideComparisonMessage();
    });

    document.getElementById('lastWeekBtn').addEventListener('click', async () => {
        const today = new Date();
        const endDate = new Date(today);
        endDate.setDate(today.getDate() - 1);

        const startDate = new Date(endDate);
        startDate.setDate(endDate.getDate() - 6)

        startDate.setHours(0, 0, 0, 0);
        endDate.setHours(23, 59, 59, 999);

        currentYear = endDate.getFullYear();
        currentMonth = endDate.getMonth() + 1
        
        await updateDashboardChartsAndCards(currentYear, currentMonth, startDate, endDate);
        setActiveButton('lastWeekBtn');
        hideComparisonMessage();
    });

    document.getElementById('thisDayLastWeekBtn').addEventListener('click', async () => {
        await fetchAndCompareDailyIncome('lastWeek');
        setActiveButton('thisDayLastWeekBtn');
    });

    // NEW: Event listener for "This Day Last Month" button
    document.getElementById('thisDayLastMonthBtn').addEventListener('click', async () => {
        await fetchAndCompareDailyIncome('lastMonth');
        setActiveButton('thisDayLastMonthBtn');
    });

    function setActiveButton(activeButtonId) {
        const buttons = ['currentMonthBtn', 'lastMonthBtn', 'lastWeekBtn'];
        buttons.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (buttonId === activeButtonId) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }

    function hideComparisonMessage() {
        const incomeComparisonMessageDiv = document.getElementById('incomeComparisonMessage');
        incomeComparisonMessageDiv.style.opacity = '0';
        incomeComparisonMessageDiv.classList.add('hidden');
        // Ensure it's back to default blue state after being hidden
        incomeComparisonMessageDiv.classList.remove('bg-green-100', 'border-green-500', 'text-green-700', 'bg-red-100', 'border-red-500', 'text-red-700');
        incomeComparisonMessageDiv.classList.add('bg-blue-100', 'border-blue-500', 'text-blue-700');
    }

    // Set initial active button
    setActiveButton('currentMonthBtn');

    // Re-render dashboard elements when dark mode is toggled
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                // Only re-fetch tables as charts/cards are handled by updateDashboardChartsAndCards
                fetchData('/income/', 'incomeTable', 'noIncome', incomeHeaders);
                fetchData('/daily-expenses/', 'dailyExpensesTable', 'noDailyExpenses', dailyExpensesHeaders);
                fetchData('/fixed-costs/', 'fixedCostsTable', 'noFixedCosts', fixedCostsHeaders);
                // Call updateDashboardChartsAndCards with current selected month/year
                // Note: currentMonth and currentYear will hold the last selected value from the buttons
                // if a button was clicked. Otherwise, it's the initial current month.
                updateDashboardChartsAndCards(currentYear, currentMonth);
            }
        });
    });

    observer.observe(document.documentElement, { attributes: true });

    // Resize listener to re-render tables when switching between mobile/desktop
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            fetchData('/income/', 'incomeTable', 'noIncome', incomeHeaders);
            fetchData('/daily-expenses/', 'dailyExpensesTable', 'noDailyExpenses', dailyExpensesHeaders);
            fetchData('/fixed-costs/', 'fixedCostsTable', 'noFixedCosts', fixedCostsHeaders);
        }, 200);
    });
});