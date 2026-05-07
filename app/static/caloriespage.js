document.addEventListener('DOMContentLoaded', function () {
    const caloriesChart = document.getElementById('caloriesChart');

    // Only run on pages that contain the calories chart
    if (!caloriesChart) return;

    // Make sure Chart.js has loaded
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js is not loaded.');
        return;
    }

    // Make sure Flask/Jinja passed chart data into the page
    if (!window.caloriesChartData) {
        console.warn('Calories chart data is missing.');
        return;
    }

    const styles = getComputedStyle(document.documentElement);

    const chartLineColor = styles.getPropertyValue('--chart-calories-line').trim();
    const chartFillColor = styles.getPropertyValue('--chart-calories-fill').trim();
    const chartGridColor = styles.getPropertyValue('--chart-grid-line').trim();
    const chartTextColor = styles.getPropertyValue('--color-text').trim();

    new Chart(caloriesChart, {
        type: 'line',
        data: {
            labels: window.caloriesChartData.labels,
            datasets: [{
                label: 'Calories Burned',
                data: window.caloriesChartData.burnedData,
                borderWidth: 2,
                tension: 0,
                fill: true,
                backgroundColor: chartFillColor,
                borderColor: chartLineColor,
                pointBackgroundColor: chartLineColor,
                pointBorderColor: chartLineColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: chartTextColor
                    },
                    grid: {
                        color: chartGridColor
                    }
                },
                x: {
                    ticks: {
                        color: chartTextColor
                    },
                    grid: {
                        color: chartGridColor
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: chartTextColor
                    }
                }
            }
        }
    });
});