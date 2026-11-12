// Humanized, high-performance dashboard charts and event pipeline
let protocolChart = null;
let trafficTrendChart = null;

const timeLabels = [];
const trafficDataPoints = [];
let prevTotalPackets = 0;

function initCharts() {
  // 1. Doughnut: Protocol Composition
  const ctxProto = document.getElementById("protocolChart").getContext("2d");
  protocolChart = new Chart(ctxProto, {
    type: "doughnut",
    data: {
      labels: ["TCP", "UDP", "ICMP", "OTHER"],
      datasets: [{
        data: [0, 0, 0, 0],
        backgroundColor: [
          "#6366f1", // Indigo for TCP
          "#06b6d4", // Cyan for UDP
          "#f59e0b", // Amber for ICMP
          "#64748b"  // Slate for Other
        ],
        borderColor: "#0f172a",
        borderWidth: 3,
        hoverOffset: 6
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
            padding: 16,
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: 500 }
          }
        },
        tooltip: {
          backgroundColor: "#1e293b",
          titleColor: "#f8fafc",
          bodyColor: "#cbd5e1",
          borderColor: "rgba(255, 255, 255, 0.1)",
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8
        }
      }
    }
  });

  // 2. Line Chart: Live Packet Rate
  const ctxTrend = document.getElementById("trendChart").getContext("2d");
  const gradient = ctxTrend.createLinearGradient(0, 0, 0, 240);
  gradient.addColorStop(0, "rgba(99, 102, 241, 0.35)");
  gradient.addColorStop(1, "rgba(99, 102, 241, 0.0)");

  trafficTrendChart = new Chart(ctxTrend, {
    type: "line",
    data: {
      labels: timeLabels,
      datasets: [{
        label: "Packets/sec",
        data: trafficDataPoints,
        borderColor: "#818cf8",
        borderWidth: 2.5,
        backgroundColor: gradient,
        fill: true,
        tension: 0.35,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: "#6366f1",
        pointBorderColor: "#fff"
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: { color: "#64748b", font: { family: "'JetBrains Mono', monospace", size: 10 } }
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(255, 255, 255, 0.04)" },
          ticks: { color: "#64748b", font: { family: "'JetBrains Mono', monospace", size: 10 } }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#1e293b",
          titleColor: "#f8fafc",
          bodyColor: "#cbd5e1",
          borderColor: "rgba(255, 255, 255, 0.1)",
          borderWidth: 1,
          padding: 10,
          cornerRadius: 8
        }
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

    // Calculate rolling packet delta for the live curve
    const nowStr = new Date().toLocaleTimeString();
    let currentTotal = data.packets_captured;
    let delta = prevTotalPackets === 0 ? 0 : Math.max(0, currentTotal - prevTotalPackets);
    prevTotalPackets = currentTotal;

    timeLabels.push(nowStr);
    trafficDataPoints.push(delta);
    if (timeLabels.length > 14) {
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

    if (alerts.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5">
            <div class="empty-box">
              <div class="empty-icon">🛡️</div>
              <p>No threats detected yet. System traffic is normal.</p>
            </div>
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = "";
    alerts.forEach(a => {
      let pillClass = "pill-low";
      if (a.risk_level === "HIGH") pillClass = "pill-high";
      else if (a.risk_level === "MEDIUM") pillClass = "pill-med";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="pill ${pillClass}">${a.risk_level}</span></td>
        <td><strong style="color: #f1f5f9;">${a.attack_type}</strong></td>
        <td>
          <span class="ip-tag">${a.source_ip}</span>
          <span style="color: var(--text-dim); margin: 0 4px;">&rarr;</span>
          <span class="ip-tag">${a.destination_ip}</span>
        </td>
        <td style="color: #cbd5e1; font-size: 0.82rem;">${a.description}</td>
        <td><span class="time-tag">${a.timestamp}</span></td>
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

    if (offenders.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="3">
            <div class="empty-box">
              <p>No active threat hosts</p>
            </div>
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = "";
    offenders.forEach(o => {
      let pillClass = "pill-low";
      if (o.highest_risk === "HIGH") pillClass = "pill-high";
      else if (o.highest_risk === "MEDIUM") pillClass = "pill-med";

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="ip-tag">${o.source_ip}</span></td>
        <td><strong style="font-family: var(--font-mono); color: #f8fafc;">${o.alert_count}</strong></td>
        <td><span class="pill ${pillClass}">${o.highest_risk}</span></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error fetching offenders:", err);
  }
}

async function triggerSimulation(attackType) {
  const btn = event.currentTarget;
  const originalHtml = btn.innerHTML;
  btn.innerHTML = `⏳ Simulating...`;
  btn.disabled = true;

  try {
    await fetch(`/api/simulate/${attackType}`, { method: "POST" });
    // Immediate multi-point refresh
    await Promise.all([
      fetchMetrics(),
      fetchProtocols(),
      fetchAlerts(),
      fetchTopOffenders()
    ]);
  } catch (e) {
    console.error("Simulation request failed:", e);
  } finally {
    btn.innerHTML = originalHtml;
    btn.disabled = false;
  }
}

async function clearDatabase() {
  if (!confirm("Are you sure you want to reset all collected traffic logs and security alerts?")) return;
  try {
    await fetch("/api/clear", { method: "POST" });
    prevTotalPackets = 0;
    timeLabels.length = 0;
    trafficDataPoints.length = 0;
    await Promise.all([
      fetchMetrics(),
      fetchProtocols(),
      fetchAlerts(),
      fetchTopOffenders()
    ]);
  } catch (e) {
    console.error("Failed to clear database:", e);
  }
}

// Lifecycle Init & Polling Interval
document.addEventListener("DOMContentLoaded", () => {
  initCharts();
  fetchMetrics();
  fetchProtocols();
  fetchAlerts();
  fetchTopOffenders();

  // Smooth polling every 2.5 seconds
  setInterval(() => {
    fetchMetrics();
    fetchProtocols();
    fetchAlerts();
    fetchTopOffenders();
  }, 2500);
});
