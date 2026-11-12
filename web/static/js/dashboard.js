// Professional NIDS Dashboard Operations Script
let protocolChart = null;
let trafficTrendChart = null;

const timeLabels = [];
const trafficDataPoints = [];
let prevTotalPackets = 0;

// Notification Toast Utility (No native browser alert)
function showToast(message, isError = false) {
  const toast = document.getElementById("toast-notification");
  const icon = document.getElementById("toast-icon");
  const msg = document.getElementById("toast-msg");

  icon.innerText = isError ? "❌" : "✅";
  msg.innerText = message;

  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3200);
}

// Modal dialog helpers (No native browser confirm dialog)
function promptResetDatabase() {
  document.getElementById("confirm-modal").classList.add("open");
}

function closeModal() {
  document.getElementById("confirm-modal").classList.remove("open");
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
      showToast("Database logs and alert history cleared successfully.");
    } else {
      showToast("Failed to clear database.", true);
    }
  } catch (err) {
    showToast("Server error during reset.", true);
  }
}

// Chart Initializations
function initCharts() {
  // Protocol Distribution Doughnut
  const ctxProto = document.getElementById("protocolChart").getContext("2d");
  protocolChart = new Chart(ctxProto, {
    type: "doughnut",
    data: {
      labels: ["TCP", "UDP", "ICMP", "OTHER"],
      datasets: [{
        data: [0, 0, 0, 0],
        backgroundColor: [
          "#2f81f7", // Blue for TCP
          "#38bdf8", // Light Blue for UDP
          "#d29922", // Amber for ICMP
          "#6e7681"  // Gray for Other
        ],
        borderColor: "#161b22",
        borderWidth: 2,
        hoverOffset: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color: "#8b949e",
            boxWidth: 12,
            padding: 14,
            font: { family: "'Inter', sans-serif", size: 11, weight: 500 }
          }
        },
        tooltip: {
          backgroundColor: "#1f242c",
          titleColor: "#e6edf3",
          bodyColor: "#8b949e",
          borderColor: "#30363d",
          borderWidth: 1,
          padding: 8,
          cornerRadius: 6
        }
      }
    }
  });

  // Packet Ingestion Line Chart
  const ctxTrend = document.getElementById("trendChart").getContext("2d");
  trafficTrendChart = new Chart(ctxTrend, {
    type: "line",
    data: {
      labels: timeLabels,
      datasets: [{
        label: "Packets / sec",
        data: trafficDataPoints,
        borderColor: "#2f81f7",
        borderWidth: 1.8,
        backgroundColor: "rgba(47, 129, 247, 0.08)",
        fill: true,
        tension: 0.25,
        pointRadius: 2,
        pointHoverRadius: 5
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: "#21262d" },
          ticks: { color: "#6e7681", font: { family: "'IBM Plex Mono', monospace", size: 10 } }
        },
        y: {
          beginAtZero: true,
          grid: { color: "#21262d" },
          ticks: { color: "#6e7681", font: { family: "'IBM Plex Mono', monospace", size: 10 } }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#1f242c",
          titleColor: "#e6edf3",
          bodyColor: "#8b949e",
          borderColor: "#30363d",
          borderWidth: 1,
          padding: 8,
          cornerRadius: 6
        }
      }
    }
  });
}

// Fetch Metrics
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
    console.error("Failed to load metrics:", err);
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
    console.error("Failed to load protocols:", err);
  }
}

// Fetch Alert Feed
async function fetchAlerts() {
  try {
    const res = await fetch("/api/alerts?limit=15");
    const alerts = await res.json();
    const tbody = document.getElementById("alerts-table-body");

    if (alerts.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5">
            <div class="empty-table-state">No security alerts detected. System activity is normal.</div>
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
        <td><strong>${a.attack_type}</strong></td>
        <td>
          <span class="mono-ip">${a.source_ip}</span>
          <span style="color: var(--text-muted); margin: 0 4px;">&rarr;</span>
          <span class="mono-ip">${a.destination_ip}</span>
        </td>
        <td style="color: var(--text-secondary);">${a.description}</td>
        <td><span class="timestamp">${a.timestamp}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load alerts:", err);
  }
}

// Fetch Top Offending Hosts
async function fetchTopOffenders() {
  try {
    const res = await fetch("/api/top-offenders");
    const offenders = await res.json();
    const tbody = document.getElementById("offenders-table-body");

    if (offenders.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="3">
            <div class="empty-table-state">No offending hosts identified</div>
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
        <td><strong style="font-family: var(--font-mono);">${o.alert_count}</strong></td>
        <td><span class="badge ${badgeClass}">${o.highest_risk}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load offenders:", err);
  }
}

// Trigger Simulation (With clean in-button loading state)
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
      const readableName = attackType.toUpperCase();
      showToast(`Scenario [${readableName}] executed and analyzed.`);
    } else {
      showToast("Simulation encountered an issue.", true);
    }
  } catch (e) {
    showToast("Failed to communicate with simulation engine.", true);
  } finally {
    btnElement.innerText = originalText;
    btnElement.disabled = false;
  }
}

// Lifecycle Init & Polling
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  fetchMetrics();
  fetchProtocols();
  fetchAlerts();
  fetchTopOffenders();

  // Automatic live telemetry poll every 3 seconds
  setInterval(() => {
    fetchMetrics();
    fetchProtocols();
    fetchAlerts();
    fetchTopOffenders();
  }, 3000);
});
