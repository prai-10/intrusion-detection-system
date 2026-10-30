"""
Global Configuration for Network Intrusion Detection System (NIDS)
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = os.getenv("IDS_DB_PATH", str(DATA_DIR / "ids.db"))

# Network Capture Settings
DEFAULT_INTERFACE = None  # None selects default Scapy interface
PACKET_BUFFER_SIZE = 1000
CAPTURE_FILTER = "ip or icmp"

# Detection Thresholds & Windows
# 1. Port Scan Detection (Chapter 5.2)
PORT_SCAN_WINDOW_SEC = 10
PORT_SCAN_THRESHOLD = 15  # Unique destination ports accessed within window

# 2. Abnormal Traffic / DoS Rate Detection (Chapter 5.3)
TRAFFIC_BURST_WINDOW_SEC = 10
TRAFFIC_BURST_THRESHOLD = 200  # Total packets from single source within window

# 3. Repeated Connection Detection (Chapter 5.4)
REPEATED_CONN_WINDOW_SEC = 15
REPEATED_CONN_THRESHOLD = 30  # Repeated attempts to same target host within window

# 4. ICMP Anomaly Detection (Chapter 5.5)
ICMP_WINDOW_SEC = 5
ICMP_THRESHOLD = 15  # ICMP packets from single source within window

# Alert throttling / cooldown (seconds) to prevent flood of identical alerts
ALERT_COOLDOWN_SEC = 5

# Risk Scoring Boundaries (Chapter 5.6)
RISK_LEVEL_LOW = "LOW"        # 0 - 30
RISK_LEVEL_MEDIUM = "MEDIUM"  # 31 - 70
RISK_LEVEL_HIGH = "HIGH"      # 71 - 100
