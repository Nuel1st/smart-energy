let chart;

function initDashboard(energyUrl, devicesUrl, toggleUrl) {
    loadEnergyData();
    startRealTimeUpdates(energyUrl);
    setupToggleButtons(toggleUrl);
    
    // Initialize chart
    const ctx = document.getElementById('usageChart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Energy Usage (Wh)',
                data: [],
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function loadEnergyData() {
    fetch('/api/energy/')
        .then(response => response.json())
        .then(data => {
            updateChart(data.readings);
        });
}

function startRealTimeUpdates(energyUrl) {
    setInterval(() => {
        fetch(energyUrl)
            .then(response => response.json())
            .then(data => {
                updateChart(data.readings);
                updateTotalUsage();
            });
    }, 5000); // Update every 5 seconds
}

function updateChart(readings) {
    const labels = readings.map(r => new Date(r.timestamp).toLocaleTimeString());
    const data = readings.map(r => r.energy_consumed);
    
    chart.data.labels = labels.slice(-20); // Last 20 readings
    chart.data.datasets[0].data = data.slice(-20);
    chart.update('none');
}

function setupToggleButtons(toggleUrl) {
    document.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const deviceId = this.dataset.device;
            toggleDevice(toggleUrl, deviceId, this);
        });
    });
}

function toggleDevice(toggleUrl, deviceId, button) {
    fetch(`${toggleUrl}${deviceId}/toggle/`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            button.textContent = data.status ? 'OFF' : 'ON';
            button.className = `btn btn-sm btn-outline-${data.status ? 'danger' : 'success'}`;
        });
}

function updateTotalUsage() {
    fetch('/api/energy/?device_id=all')
        .then(response => response.json())
        .then(data => {
            const total = data.readings.reduce((sum, r) => sum + r.energy_consumed, 0) / 1000;
            document.getElementById('totalUsage').textContent = total.toFixed(2) + ' kWh';
        });
}