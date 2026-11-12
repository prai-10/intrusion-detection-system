// Humanized Operations Script
let protocolChart = null;
let trafficTrendChart = null;

const timeLabels = [];
const trafficDataPoints = [];
let prevTotalPackets = 0;

// Toast Helper (Replaces native browser alert)
function showToast(message, isError = false) {
  const box = document.getElementById("toast-box");
  const icon = document.getElementById("toast-icon");
  const text = document.getElementById("toast-text");

  icon.innerText = isError ? "⚠️" : "✅";
  text.innerText = message;

  box.classList.add("show");
  setTimeout(() => {
    box.classList.remove("show");
  }, 3000);
}

// Modal Helpers (Replaces native confirm dialog)
function promptResetDatabase() {
  document.getElementById("confirm-modal").classList.add("active");
}

function closeModal() {
  document.getElementById("confirm-modal").classList.remove("active");
}

async function confirmResetDatabase() {
  closeModal();
  try {
    const res = await fetch("/api/clear", { method: "POST" });
    if (res.ok) {
      prevTotalPackets = 0;
      timeLabels.length = 0;
      trafficDataPoints.length = 0;
      await Promise.all([
        fetchMetrics(),
        fetchProtocols(),
        fetchAlerts(),
        fetchTopOffenders()
      ]);
      showToast("All traffic logs and alerts successfully cleared.");
    } else {
      showToast("Failed to reset database logs.", true);
    }
  } catch (err) {
    showToast("Server error during reset.", true);
  }
}

// Initialize Visual Charts
function initCharts() {
  // Protocol Breakdown Doughnut Chart
  const ctxProto = document.getElementById("protocolChart").getContext("2d");
  protocolChart = new Chart(ctxProto, {
    type: "doughnut",
    data: {
      labels: ["TCP", "UDP", "ICMP", "OTHER"],
      datasets: [{
        data: [0, 0, 0, 0],
        backgroundColor: [
          "#3b82f6", // Blue
          "#06b6d4", // Cyan
          "#f59e0b", // Amber
          "#64748b"  // Slate
        ],
        borderColor: "#131923",
        borderWidth: 3,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "70%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#94a3b8",
            padding: 14,
            boxWidth: 12,
            font: { family: "'Inter', sans-serif", size: 11, weight: 500 }
          }
        },
        tooltip: {
          backgroundColor: "#18202c",
          titleColor: "#f0f4f8",
          bodyColor: "#94a3b8",
          borderColor: "#263346",
          borderWidth: 1,
          padding: 8,
          cornerRadius: 6
        }
      }
    }
  });

  // Traffic Ingestion Rate Line Chart
  const ctxTrend = document.getElementById("trendChart").getContext("2d");
  trafficTrendChart = new Chart(ctxTrend, {
    type: "line",
    data: {
      labels: timeLabels,
      datasets: [{
        label: "Packets/sec",
        data: trafficDataPoints,
        borderColor: "#3b82f6",
        borderWidth: 2,
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: true,
        tension: 0.3,
        pointRadius: 2.5,
        pointHoverRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: "#1f2937" },
          ticks: { color: "#64748b", font: { family: "'JetBrains Mono', monospace", size: 10 } }
        },
        y: {
          beginAtZero: true,
          grid: { color: "#1f2937" },
          ticks: { color: "#64748b", font: { family: "'JetBrains Mono', monospace", size: 10 } }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#18202c",
          titleColor: "#f0f4f8",
          bodyColor: "#94a3b8",
          borderColor: "#263346",
          borderWidth: 1,
          padding: 8,
          cornerRadius: 6
        }
      }
    }
  });
}

// Fetch System Metrics
async function fetchMetrics() {
  try {
    const res = await fetch("/api/metrics");
    const data = await res.json();

    document.getElementById("stat-packets").innerText = Number(data.packets_captured).toLocaleString();
    document.getElementById("stat-alerts").innerText = Number(data.total_alerts).toLocaleString();
    document.getElementById("stat-high-risk").innerText = Number(data.high_risk_alerts).toLocaleString();
    document.getElementById("stat-hosts").innerText = Number(data.suspicious_hosts).toLocaleString();

    const nowStr = new Date().toLocaleTimeString([], { hour12: false });
    let currentTotal = data.packets_captured;
    let delta = prevTotalPackets === 0 ? 0 : Math.max(0, currentTotal - prevTotalPackets);
    prevTotalPackets = currentTotal;

    timeLabels.push(nowStr);
    trafficDataPoints.push(delta);
    if (timeLabels.length > 15) {
      timeLabels.shift();
      trafficDataPoints.shift();
    }
    trafficTrendChart.update();
  } catch (err) {
    console.error("Metrics load error:", err);
  }
}

// Fetch Protocol Breakdown
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
    console.error("Protocols load error:", err);
  }
}

// Fetch Alert Records
async function fetchAlerts() {
  try {
    const res = await fetch("/api/alerts?limit=15");
    const alerts = await res.json();
    const tbody = document.getElementById("alerts-table-body");

    if (alerts.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5">
            <div class="empty-state">No alerts recorded yet. Network activity is normal.</div>
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = "";
    alerts.forEach(a => {
      let badgeClass = "badge-low";
      if (a.risk_level === "HIGH") badgeClass = "badge-high";
      else if (a.risk_level === "MEDIUM") badgeClass = "badge-med";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="badge ${badgeClass}">${a.risk_level}</span></td>
        <td><strong style="color: #f1f5f9;">${a.attack_type}</strong></td>
        <td>
          <span class="mono-ip">${a.source_ip}</span>
          <span style="color: var(--text-muted); margin: 0 4px;">&rarr;</span>
          <span class="mono-ip">${a.destination_ip}</span>
        </td>
        <td style="color: #cbd5e1; font-size: 0.82rem;">${a.description}</td>
        <td><span class="timestamp">${a.timestamp}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Alerts load error:", err);
  }
}

// Fetch Top Offending Sources
async function fetchTopOffenders() {
  try {
    const res = await fetch("/api/top-offenders");
    const offenders = await res.json();
    const tbody = document.getElementById("offenders-table-body");

    if (offenders.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="3">
            <div class="empty-state">No hosts flagged</div>
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = "";
    offenders.forEach(o => {
      let badgeClass = "badge-low";
      if (o.highest_risk === "HIGH") badgeClass = "badge-high";
      else if (o.highest_risk === "MEDIUM") badgeClass = "badge-med";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="mono-ip">${o.source_ip}</span></td>
        <td><strong style="font-family: var(--font-mono); font-size: 0.9rem;">${o.alert_count}</strong></td>
        <td><span class="badge ${badgeClass}">${o.highest_risk}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Offenders load error:", err);
  }
}

// Trigger Synthetic Attack Scenario
async function triggerSimulation(attackType, btnElement) {
  const originalText = btnElement.innerText;
  btnElement.innerText = "Running...";
  btnElement.disabled = true;

  try {
    const res = await fetch(`/api/simulate/${attackType}`, { method: "POST" });
    if (res.ok) {
      await Promise.all([
        fetchMetrics(),
        fetchProtocols(),
        fetchAlerts(),
        fetchTopOffenders()
      ]);
      showToast(`Simulation [${attackType.toUpperCase()}] executed.`);
    } else {
      showToast("Simulation execution failed.", true);
    }
  } catch (e) {
    showToast("Server error during simulation.", true);
  } finally {
    btnElement.innerText = originalText;
    btnElement.disabled = false;
  }
}

// Page Initialization & Polling
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  fetchMetrics();
  fetchProtocols();
  fetchAlerts();
  fetchTopOffenders();

  // Poll active data every 3 seconds
  setInterval(() => {
    fetchMetrics();
    fetchProtocols();
    fetchAlerts();
    fetchTopOffenders();
  }, 3000);
});
