Chart.register(ChartDataLabels);

document.addEventListener('DOMContentLoaded', async () => {
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth() + 1;

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

                    if (headerKey.includes('amount') || headerKey.includes('revenue') || headerKey.includes('eur')) {
                        cell.classList.add('text-right');
                        value = formatCurrency(value);
                    } else if (tableId === 'incomeTable' && headerKey === 'hours_worked') {
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
            const totalDisplayDiv = (chartId === 'monthlyExpenseCategoriesPieChart') ? document.getElementById('totalMonthlyExpensesDisplay') :
                                    (chartId === 'monthlyIncomeChart') ? document.getElementById('totalMonthlyIncomeDisplay') :
                                    (chartId === 'globalSummaryChart') ? document.getElementById('totalGlobalSummaryDisplay') : null;

            if (Object.keys(rawData).length === 0 || (Array.isArray(rawData) && rawData.length === 0)) {
                noDataMessage.classList.remove('hidden');
                if (canvas) canvas.style.display = 'none';
                if (totalDisplayDiv) {
                    totalDisplayDiv.classList.add('hidden');
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

            if (chartInstances[chartId]) {
                chartInstances[chartId].destroy();
                delete chartInstances[chartId];
            }

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

            } else {
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
                    scales: {
                        x: {
                            grid: {
                                color: colors.gridLineColor
                            },
                            ticks: {
                                color: colors.primaryTextColor
                            },
                            title: {
                                display: true,
                                text: 'Amount (€)',
                                color: colors.primaryTextColor
                            }
                        },
                        y: {
                            title: {
                                display: false
                            },
                            ticks: {
                                color: colors.primaryTextColor
                            },
                            grid: {
                                color: colors.gridLineColor
                            }
                        }
                    },
                    ...options
                }
            });
        } catch (error) {
            console.error(`Error fetching or rendering chart for ${chartId}:`, error);
            if (canvas) canvas.style.display = 'none';
            document.getElementById(noDataMessageId).textContent = `Error loading data: ${error.message}`;
            document.getElementById(noDataMessageId).classList.remove('hidden');
            const totalDisplayDiv = (chartId === 'monthlyExpenseCategoriesPieChart') ? document.getElementById('totalMonthlyExpensesDisplay') :
                                    (chartId === 'monthlyIncomeChart') ? document.getElementById('totalMonthlyIncomeDisplay') :
                                    (chartId === 'globalSummaryChart') ? document.getElementById('totalGlobalSummaryDisplay') : null;
            if (totalDisplayDiv) totalDisplayDiv.classList.add('hidden');
        }
    }

    async function fetchAndDisplayProfitLossAverageAndCashOnHand() {
        const netProfitLossDisplay = document.getElementById('netProfitLossDisplay');
        const monthlyAverageValueDisplay = document.getElementById('monthlyAverageValueDisplay');
        const cashOnHandDisplay = document.getElementById('cashOnHandDisplay');
        const noDataMessage = document.getElementById('noNetProfitLossChart');

        try {
            const monthlySummaryResponse = await fetch(`/summary/monthly?year=${currentYear}&month=${currentMonth}`);
            if (!monthlySummaryResponse.ok) throw new Error(`HTTP error! status: ${monthlySummaryResponse.status}`);
            const monthlySummaryData = await monthlySummaryResponse.json();

            const incomeTableResponse = await fetch('/income/');
            if (!incomeTableResponse.ok) throw new Error(`HTTP error! status: ${incomeTableResponse.status}`);
            const incomeTableData = await incomeTableResponse.json();

            const cashOnHandResponse = await fetch('/summary/cash-on-hand');
            if (!cashOnHandResponse.ok) throw new Error(`HTTP error! status: ${cashOnHandResponse.status}`);
            const cashOnHandData = await cashOnHandResponse.json();

            if (!monthlySummaryData || monthlySummaryData.net_monthly_profit === undefined) {
                noDataMessage.classList.remove('hidden');
                netProfitLossDisplay.textContent = '';
                monthlyAverageValueDisplay.textContent = '';
                cashOnHandDisplay.textContent = '';
                return;
            }

            noDataMessage.classList.add('hidden');
            const netProfit = monthlySummaryData.net_monthly_profit;
            netProfitLossDisplay.textContent = formatCurrency(netProfit);
            netProfitLossDisplay.style.color = netProfit >= 0 ? 'green' : 'red';

            const uniqueIncomeDates = new Set();
            incomeTableData.forEach(item => {
                const incomeDate = new Date(item.income_date);
                if (incomeDate.getFullYear() === currentYear && incomeDate.getMonth() + 1 === currentMonth) {
                    uniqueIncomeDates.add(item.income_date);
                }
            });

            const daysWorked = uniqueIncomeDates.size;
            let totalMonthlyIncome = 0;
            incomeTableData.forEach(item => {
                const incomeDate = new Date(item.income_date);
                if (incomeDate.getFullYear() === currentYear && incomeDate.getMonth() + 1 === currentMonth) {
                    totalMonthlyIncome += (item.tours_revenue_eur || 0) + (item.transfers_revenue_eur || 0);
                }
            });

            const monthlyAverage = daysWorked > 0 ? totalMonthlyIncome / daysWorked : 0;
            monthlyAverageValueDisplay.textContent = formatCurrency(monthlyAverage);

            if (cashOnHandData && cashOnHandData.balance !== undefined) {
                cashOnHandDisplay.textContent = formatCurrency(cashOnHandData.balance);
                cashOnHandDisplay.style.color = cashOnHandData.balance >= 0 ? 'green' : 'red';
            } else {
                cashOnHandDisplay.textContent = 'N/A';
            }

        } catch (error) {
            console.error('Error fetching net profit/loss, monthly average, or cash on hand:', error);
            netProfitLossDisplay.textContent = 'Error loading data.';
            monthlyAverageValueDisplay.textContent = '';
            cashOnHandDisplay.textContent = 'Error loading data.';
            noDataMessage.textContent = `Error loading summary data: ${error.message}`;
            noDataMessage.classList.remove('hidden');
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

    async function renderAllDashboardElements() {
        await fetchAndRenderChart(`/summary/expense-categories?year=${currentYear}&month=${currentMonth}`, 'monthlyExpenseCategoriesPieChart', 'noMonthlyExpenseCategoriesPieChart', 'pie', processCategoryData);
        await fetchAndRenderChart(`/summary/income-sources?year=${currentYear}&month=${currentMonth}`, 'monthlyIncomeChart', 'noMonthlyIncomeChart', 'pie', processMonthlyIncomeData);
        await fetchAndDisplayProfitLossAverageAndCashOnHand();
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

    const incomeHeaders = ['doc_id', 'income_date', 'tours_revenue_eur', 'transfers_revenue_eur', 'daily_total_eur', 'hours_worked'];
    const dailyExpensesHeaders = ['doc_id', 'cost_date', 'description', 'category', 'payment_method', 'amount'];
    const fixedCostsHeaders = ['doc_id', 'cost_date', 'description', 'cost_frequency', 'category', 'recipient', 'payment_method', 'amount_eur'];

    // Initial data fetch and render
    await fetchData('/income/', 'incomeTable', 'noIncome', incomeHeaders);
    await fetchData('/daily-expenses/', 'dailyExpensesTable', 'noDailyExpenses', dailyExpensesHeaders);
    await fetchData('/fixed-costs/', 'fixedCostsTable', 'noFixedCosts', fixedCostsHeaders);

    renderAllDashboardElements();

    // Re-render dashboard elements when dark mode is toggled
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                fetchData('/income/', 'incomeTable', 'noIncome', incomeHeaders);
                fetchData('/daily-expenses/', 'dailyExpensesTable', 'noDailyExpenses', dailyExpensesHeaders);
                fetchData('/fixed-costs/', 'fixedCostsTable', 'noFixedCosts', fixedCostsHeaders);
                renderAllDashboardElements();
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
