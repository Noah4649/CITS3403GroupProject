// ─── AJAX ADD MEAL ──────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    const addMealForm = document.getElementById('add-meal-form');
    const mealsTableBody = document.getElementById('meals-table-body');

    const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

    function formatNumber(value) {
        return Number(value || 0).toFixed(1);
    }

    function updateConsumedChartForToday(totalConsumed) {
        if (!window.caloriesChart || !window.caloriesChartData) {
            console.warn('Calories chart or chart data is missing.');
            return;
        }

        const currentDayIndex = window.caloriesChartData.currentDayIndex;

        if (currentDayIndex === null || currentDayIndex === undefined) {
            console.warn('Current day index is missing. Chart will only update on This week.');
            return;
        }

        const consumedDataset = window.caloriesChart.data.datasets.find(
            dataset => dataset.label === 'Calories Consumed'
        );

        if (!consumedDataset) {
            console.warn('Calories Consumed dataset could not be found.');
            return;
        }

        consumedDataset.data[currentDayIndex] = Number(totalConsumed || 0);

        window.caloriesChart.update();
    }


    if (!addMealForm || !mealsTableBody) return;

    addMealForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const mealData = {
            name: document.getElementById('meal-name').value,
            calories: document.getElementById('meal-calories').value,
            protein: document.getElementById('meal-protein').value,
            carbs: document.getElementById('meal-carbs').value,
            fats: document.getElementById('meal-fats').value,
            water_ml: document.getElementById('meal-water').value
        };

        fetch('/api/add-meal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(mealData)
        })
        .then(response => response.json().then(data => ({
            status: response.status,
            body: data
        })))
        .then(result => {
            if (!result.body.success) {
                alert(result.body.message || 'Could not add meal.');
                return;
            }

            const meal = result.body.meal;

            const noMealsRow = document.getElementById('no-meals-row');
            if (noMealsRow) {
                noMealsRow.remove();
            }

            const newRow = document.createElement('tr');

            newRow.id = `meal-row-${meal.id}`;

            newRow.innerHTML = `
                <td>${meal.name}</td>
                <td>${formatNumber(meal.calories)} kcal</td>
                <td>${formatNumber(meal.protein)} g</td>
                <td>${formatNumber(meal.carbs)} g</td>
                <td>${formatNumber(meal.fats)} g</td>
                <td>${formatNumber(meal.water_ml)} ml</td>
                <td>
                    <button type="button"
                            class="btn btn-outline-secondary btn-sm delete-meal-btn"
                            data-meal-id="${meal.id}">
                        Delete
                    </button>
                </td>
            `;

            mealsTableBody.appendChild(newRow);

            // Update the summary cards without reloading the page
            const totals = result.body.totals;

            if (totals) {
                // Update summary cards
                document.getElementById('total-calories-consumed').textContent = formatNumber(totals.total_calories_consumed);
                document.getElementById('net-calories').textContent = formatNumber(totals.net_calories);

                // Update meals table footer totals
                document.getElementById('table-total-calories').textContent = `${formatNumber(totals.total_calories_consumed)} kcal`;
                document.getElementById('table-total-protein').textContent = `${formatNumber(totals.total_protein)} g`;
                document.getElementById('table-total-carbs').textContent = `${formatNumber(totals.total_carbs)} g`;
                document.getElementById('table-total-fats').textContent = `${formatNumber(totals.total_fats)} g`;
                document.getElementById('table-total-water').textContent = `${formatNumber(totals.total_water_ml)} ml`;

                // Update calories chart totals
                updateConsumedChartForToday(totals.total_calories_consumed);
            }

            addMealForm.reset();
        })
        .catch(error => {
            console.error('Error adding meal:', error);
            alert('Something went wrong while adding the meal.');
        });
    });

// ─── AJAX DELETE MEAL ───────────────────────────────────
    mealsTableBody.addEventListener('click', function (event) {
        if (!event.target.classList.contains('delete-meal-btn')) return;

        const mealId = event.target.dataset.mealId;

        const confirmed = confirm('Are you sure you want to delete this meal?');

        if (!confirmed) {
            return;
        }

        fetch(`/api/delete-meal/${mealId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                alert(data.message || 'Could not delete meal.');
                return;
            }

            // Remove the deleted meal row from the table
            const row = document.getElementById(`meal-row-${mealId}`);

            if (row) {
                row.remove();
            }

            // If there are no meals left, show the empty table message
            if (mealsTableBody.children.length === 0) {
                mealsTableBody.innerHTML = `
                    <tr id="no-meals-row">
                        <td colspan="7">No meals logged today.</td>
                    </tr>
                `;
            }

            // Update the summary cards and table totals
            const totals = data.totals;

            if (totals) {
                document.getElementById('total-calories-consumed').textContent = formatNumber(totals.total_calories_consumed);
                document.getElementById('net-calories').textContent = formatNumber(totals.net_calories);

                document.getElementById('table-total-calories').textContent = `${formatNumber(totals.total_calories_consumed)} kcal`;
                document.getElementById('table-total-protein').textContent = `${formatNumber(totals.total_protein)} g`;
                document.getElementById('table-total-carbs').textContent = `${formatNumber(totals.total_carbs)} g`;
                document.getElementById('table-total-fats').textContent = `${formatNumber(totals.total_fats)} g`;
                document.getElementById('table-total-water').textContent = `${formatNumber(totals.total_water_ml)} ml`;

                // Update calories chart totals
                updateConsumedChartForToday(totals.total_calories_consumed);
            }
        })
        .catch(error => {
            console.error('Error deleting meal:', error);
            alert('Something went wrong while deleting the meal.');
        });
    });
});

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

    const burnedLineColor = styles.getPropertyValue('--chart-calories-line').trim();
    const burnedFillColor = styles.getPropertyValue('--chart-calories-fill').trim();
    const consumedLineColor = styles.getPropertyValue('--chart-consumed-line').trim();
    const consumedFillColor = styles.getPropertyValue('--chart-consumed-fill').trim();
    const chartGridColor = styles.getPropertyValue('--chart-grid-line').trim();
    const chartTextColor = styles.getPropertyValue('--color-text').trim();

    const todayLinePlugin = {
        id: 'todayLine',
        afterDraw(chart) {
            const todayIndex = window.caloriesChartData.todayIndex;

            if (todayIndex === null || todayIndex === undefined) return;

            const xScale = chart.scales.x;
            const chartArea = chart.chartArea;
            const ctx = chart.ctx;

            const x = xScale.getPixelForValue(todayIndex);

            ctx.save();
            ctx.beginPath();
            ctx.moveTo(x, chartArea.top);
            ctx.lineTo(x, chartArea.bottom);
            ctx.lineWidth = 1;
            ctx.setLineDash([6, 6]);
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.45)';
            ctx.stroke();
            ctx.restore();
        }
    };

    window.caloriesChart = new Chart(caloriesChart, {
        type: 'line',
        data: {
            labels: window.caloriesChartData.labels,
            datasets: [
                {
                    label: 'Calories Burned',
                    data: window.caloriesChartData.burnedData,
                    borderWidth: 2,
                    tension: 0,
                    fill: true,
                    spanGaps: false,
                    backgroundColor: burnedFillColor,
                    borderColor: burnedLineColor,
                    pointBackgroundColor: burnedLineColor,
                    pointBorderColor: burnedLineColor
                },
                {
                    label: 'Calories Consumed',
                    data: window.caloriesChartData.consumedData,
                    borderWidth: 2,
                    tension: 0,
                    fill: true,
                    spanGaps: false,
                    backgroundColor: consumedFillColor,
                    borderColor: consumedLineColor,
                    pointBackgroundColor: consumedLineColor,
                    pointBorderColor: consumedLineColor
                }
            ]
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
        },
        plugins: [todayLinePlugin]
    });
    
// ─── AJAX WEEKLY CHART UPDATE ──────────────────────────
    const weekSelector = document.getElementById('week');
    const weeklyCaloriesTitle = document.getElementById('weekly-calories-title');

    if (weekSelector) {
        weekSelector.addEventListener('change', function () {
            const selectedWeek = weekSelector.value;

            fetch(`/api/calories-chart-data?week=${selectedWeek}`)
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        alert('Could not update calories chart.');
                        return;
                    }

                    // Update stored chart data
                    window.caloriesChartData.labels = data.labels;
                    window.caloriesChartData.burnedData = data.burnedData;
                    window.caloriesChartData.consumedData = data.consumedData;
                    window.caloriesChartData.todayIndex = data.todayIndex;
                    window.caloriesChartData.currentDayIndex = data.currentDayIndex;

                    // Update Chart.js data
                    window.caloriesChart.data.labels = data.labels;

                    const burnedDataset = window.caloriesChart.data.datasets.find(
                        dataset => dataset.label === 'Calories Burned'
                    );

                    const consumedDataset = window.caloriesChart.data.datasets.find(
                        dataset => dataset.label === 'Calories Consumed'
                    );

                    if (burnedDataset) {
                        burnedDataset.data = data.burnedData;
                    }

                    if (consumedDataset) {
                        consumedDataset.data = data.consumedData;
                    }

                    // Update chart title
                    if (weeklyCaloriesTitle) {
                        weeklyCaloriesTitle.textContent = `Weekly Calories: ${data.weekStart} – ${data.weekEnd}`;
                    }

                    window.caloriesChart.update();
                })
                .catch(error => {
                    console.error('Error updating calories chart:', error);
                    alert('Something went wrong while updating the chart.');
                });
        });
    }
});