// Real-time Dashboard Chart and Polling Logic
let protocolChart = null;
let trafficTrendChart = null;

const timeLabels = [];
const trafficDataPoints = [];
let prevTotalPackets = 0;

function initCharts() {
  // Protocol Distribution Doughnut
  const ctxProto = document.getElementById("protocolChart").getContext("2d");
  protocolChart = new Chart(ctxProto, {
    type: "doughnut",
    data: {
      labels: ["TCP", "UDP", "ICMP", "OTHER"],
      datasets: [{
        data: [0, 0, 0, 0],
        backgroundColor: ["#3b82f6", "#06b6d4", "#f59e0b", "#6b7280"],
        borderColor: "#111827",
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#9ca3af", font: { size: 11 } }
        }
      }
    }
  });

  // Traffic Trend Line Chart
  const ctxTrend = document.getElementById("trendChart").getContext("2d");
  trafficTrendChart = new Chart(ctxTrend, {
    type: "line",
    data: {
      labels: timeLabels,
      datasets: [{
        label: "Packets / sec",
        data: trafficDataPoints,
        borderColor: "#06b6d4",
        backgroundColor: "rgba(6, 182, 212, 0.1)",
        fill: true,
        tension: 0.35,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: "rgba(31, 41, 55, 0.5)" },
          ticks: { color: "#9ca3af", font: { size: 10 } }
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(31, 41, 55, 0.5)" },
          ticks: { color: "#9ca3af", font: { size: 10 } }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

async function fetchMetrics() {
  try {
    const res = await fetch("/api/metrics");
    const data = await res.json();

    document.getElementById("stat-packets").innerText = Number(data.packets_captured).toLocaleString();
    document.getElementById("stat-alerts").innerText = Number(data.total_alerts).toLocaleString();
    document.getElementById("stat-high-risk").innerText = Number(data.high_risk_alerts).toLocaleString();
    document.getElementById("stat-hosts").innerText = Number(data.suspicious_hosts).toLocaleString();

    // Update traffic rate line chart
    const nowStr = new Date().toLocaleTimeString();
    let currentTotal = data.packets_captured;
    let rate = prevTotalPackets === 0 ? 0 : Math.max(0, currentTotal - prevTotalPackets);
    prevTotalPackets = currentTotal;

    timeLabels.push(nowStr);
    trafficDataPoints.push(rate);
    if (timeLabels.length > 12) {
      timeLabels.shift();
      trafficDataPoints.shift();
    }
    trafficTrendChart.update();

  } catch (err) {
    console.error("Error fetching metrics:", err);
  }
}

async function fetchProtocols() {
  try {
    const res = await fetch("/api/protocols");
    const data = await res.json();

    const labels = Object.keys(data);
    const counts = Object.values(data);

    if (labels.length > 0) {
      protocolChart.data.labels = labels;
      protocolChart.data.datasets[0].data = counts;
      protocolChart.update();
    }
  } catch (err) {
    console.error("Error fetching protocols:", err);
  }
}

async function fetchAlerts() {
  try {
    const res = await fetch("/api/alerts?limit=15");
    const alerts = await res.json();
    const tbody = document.getElementById("alerts-table-body");
    tbody.innerHTML = "";

    if (alerts.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #9ca3af; padding: 1.5rem;">No security alerts detected. System normal.</td></tr>`;
      return;
    }

    alerts.forEach(a => {
      let badgeClass = "badge-low";
      if (a.risk_level === "HIGH") badgeClass = "badge-high";
      else if (a.risk_level === "MEDIUM") badgeClass = "badge-med";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="badge ${badgeClass}">${a.risk_level}</span></td>
        <td><strong>${a.attack_type}</strong></td>
        <td><code>${a.source_ip}</code> &rarr; <code>${a.destination_ip}</code></td>
        <td style="color: #9ca3af; font-size: 0.8rem;">${a.description}</td>
        <td style="white-space: nowrap; font-size: 0.8rem; color: #6b7280;">${a.timestamp}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error fetching alerts:", err);
  }
}

async function fetchTopOffenders() {
  try {
    const res = await fetch("/api/top-offenders");
    const offenders = await res.json();
    const tbody = document.getElementById("offenders-table-body");
    tbody.innerHTML = "";

    if (offenders.length === 0) {
      tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color: #9ca3af;">No threat hosts</td></tr>`;
      return;
    }

    offenders.forEach(o => {
      let badgeClass = "badge-low";
      if (o.highest_risk === "HIGH") badgeClass = "badge-high";
      else if (o.highest_risk === "MEDIUM") badgeClass = "badge-med";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${o.source_ip}</code></td>
        <td><strong>${o.alert_count}</strong></td>
        <td><span class="badge ${badgeClass}">${o.highest_risk}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error fetching offenders:", err);
  }
}

async function triggerSimulation(attackType) {
  const btn = event.target;
  const originalText = btn.innerText;
  btn.innerText = "Simulating...";
  btn.disabled = true;

  try {
    const res = await fetch(`/api/simulate/${attackType}`, { method: "POST" });
    const data = await res.json();
    console.log(data);
    // Immediate refresh
    await fetchMetrics();
    await fetchProtocols();
    await fetchAlerts();
    await fetchTopOffenders();
  } catch (e) {
    console.error("Simulation failed:", e);
  } finally {
    btn.innerText = originalText;
    btn.disabled = false;
  }
}

async function clearDatabase() {
  if (!confirm("Are you sure you want to clear all traffic logs and alerts from the database?")) return;
  try {
    await fetch("/api/clear", { method: "POST" });
    prevTotalPackets = 0;
    timeLabels.length = 0;
    trafficDataPoints.length = 0;
    await fetchMetrics();
    await fetchProtocols();
    await fetchAlerts();
    await fetchTopOffenders();
  } catch (e) {
    console.error(e);
  }
}

// Lifecycle Init
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  fetchMetrics();
  fetchProtocols();
  fetchAlerts();
  fetchTopOffenders();

  // Poll every 3 seconds for real-time visualization updates
  setInterval(() => {
    fetchMetrics();
    fetchProtocols();
    fetchAlerts();
    fetchTopOffenders();
  }, 3000);
});
