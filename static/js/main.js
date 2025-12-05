let chart = null;
let locations = [];

// Load data saat halaman dimuat
document.addEventListener('DOMContentLoaded', function() {
    loadLocations();
    document.getElementById('predictBtn').addEventListener('click', performPrediction);
});

// Load daftar lokasi
async function loadLocations() {
    try {
        const response = await fetch('/api/data');
        const data = await response.json();
        
        locations = data.locations_list;
        const locationSelect = document.getElementById('location');
        
        // Clear existing options except "all"
        locationSelect.innerHTML = '<option value="all">Semua Lokasi</option>';
        
        // Add locations
        locations.forEach(location => {
            const option = document.createElement('option');
            option.value = location;
            option.textContent = location;
            locationSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading locations:', error);
        showError('Gagal memuat daftar lokasi');
    }
}

// Perform prediction
async function performPrediction() {
    const location = document.getElementById('location').value;
    const yearsAhead = parseInt(document.getElementById('years_ahead').value);
    const simulations = parseInt(document.getElementById('simulations').value);
    
    // Validasi input
    if (yearsAhead < 1 || yearsAhead > 10) {
        showError('Tahun ke depan harus antara 1-10');
        return;
    }
    
    if (simulations < 1000 || simulations > 50000) {
        showError('Jumlah simulasi harus antara 1000-50000');
        return;
    }
    
    // Show loading
    showLoading();
    hideError();
    hideResults();
    
    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                location: location,
                years_ahead: yearsAhead,
                simulations: simulations
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            showError(data.error);
            return;
        }
        
        // Display results
        displayResults(data);
        
    } catch (error) {
        console.error('Error performing prediction:', error);
        showError('Terjadi kesalahan saat melakukan prediksi: ' + error.message);
    } finally {
        hideLoading();
    }
}

// Display results
function displayResults(data) {
    // Update statistics
    document.getElementById('mean-growth').textContent = 
        (data.statistics.mean_growth_rate * 100).toFixed(2) + '%';
    document.getElementById('std-growth').textContent = 
        (data.statistics.std_growth_rate * 100).toFixed(2) + '%';
    
    // Create chart
    createChart(data);
    
    // Create prediction table
    createPredictionTable(data);
    
    // Show results
    showResults();
}

// Create chart
function createChart(data) {
    const ctx = document.getElementById('predictionChart').getContext('2d');
    
    // Destroy existing chart
    if (chart) {
        chart.destroy();
    }
    
    const historicalYears = data.historical.years;
    const historicalValues = data.historical.values;
    const predictedYears = data.predictions.years;
    const predictedMean = data.predictions.mean;
    const predictedP5 = data.predictions.percentiles.p5;
    const predictedP95 = data.predictions.percentiles.p95;
    
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [...historicalYears, ...predictedYears],
            datasets: [
                {
                    label: 'Data Historis',
                    data: [...historicalValues, ...new Array(predictedYears.length).fill(null)],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 3,
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    tension: 0.4
                },
                {
                    label: 'Prediksi (Mean)',
                    data: [...new Array(historicalYears.length).fill(null), ...predictedMean],
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderWidth: 3,
                    borderDash: [5, 5],
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    tension: 0.4
                },
                {
                    label: '95% Confidence Interval (Upper)',
                    data: [...new Array(historicalYears.length).fill(null), ...predictedP95],
                    borderColor: 'rgba(102, 126, 234, 0.3)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    borderDash: [2, 2],
                    pointRadius: 0,
                    fill: '+1',
                    tension: 0.4
                },
                {
                    label: '95% Confidence Interval (Lower)',
                    data: [...new Array(historicalYears.length).fill(null), ...predictedP5],
                    borderColor: 'rgba(102, 126, 234, 0.3)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    borderDash: [2, 2],
                    pointRadius: 0,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                title: {
                    display: true,
                    text: `Prediksi Kasus HIV - ${data.location} (Mulai dari 2025)`,
                    font: {
                        size: 18,
                        weight: 'bold'
                    }
                },
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Tahun'
                    },
                    grid: {
                        display: true
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Jumlah Kasus'
                    },
                    beginAtZero: true,
                    grid: {
                        display: true
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Create prediction table
function createPredictionTable(data) {
    const tbody = document.getElementById('prediction-table-body');
    tbody.innerHTML = '';
    
    const predictedYears = data.predictions.years;
    const mean = data.predictions.mean;
    const median = data.predictions.median;
    const min = data.predictions.min;
    const max = data.predictions.max;
    const std = data.predictions.std;
    const p5 = data.predictions.percentiles.p5;
    const p95 = data.predictions.percentiles.p95;
    
    for (let i = 0; i < predictedYears.length; i++) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${predictedYears[i]}</strong></td>
            <td>${Math.round(mean[i])}</td>
            <td>${Math.round(median[i])}</td>
            <td>${Math.round(min[i])}</td>
            <td>${Math.round(max[i])}</td>
            <td>${Math.round(std[i])}</td>
            <td>${Math.round(p5[i])}</td>
            <td>${Math.round(p95[i])}</td>
        `;
        tbody.appendChild(row);
    }
}

// UI Helper functions
function showLoading() {
    document.getElementById('loading').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading').classList.add('hidden');
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

function hideError() {
    document.getElementById('error').classList.add('hidden');
}

function showResults() {
    document.getElementById('chart-container').classList.remove('hidden');
    document.getElementById('stats-container').classList.remove('hidden');
    document.getElementById('prediction-table-container').classList.remove('hidden');
}

function hideResults() {
    document.getElementById('chart-container').classList.add('hidden');
    document.getElementById('stats-container').classList.add('hidden');
    document.getElementById('prediction-table-container').classList.add('hidden');
}

