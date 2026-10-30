"""
Network Intrusion Detection System (NIDS) - Main Runner
Allows running in:
1. Live Mode: Captures and analyzes packets from active network interface.
2. Demo / Simulation Mode: Generates synthetic normal and malicious packets
   (Port Scan, DoS burst, ICMP flood, Repeated Connections) to demonstrate
   real-time detection without requiring special driver permissions.
"""

import sys
import time
import argparse
from typing import Optional
from scapy.layers.inet import IP, TCP, UDP, ICMP

from core.capture import CaptureEngine
from database.db_manager import DatabaseManager
import config

BANNER = r"""
============================================================
       INTRUSION DETECTION SYSTEM (NIDS) - ENGINE
============================================================
"""

def print_status_summary(db: DatabaseManager):
    """Prints status metrics matching Chapter 5.9."""
    metrics = db.get_summary_metrics()
    alerts = db.get_recent_alerts(limit=5)

    print("\n" + "=" * 55)
    print("              SYSTEM STATUS: MONITORING")
    print("=" * 55)
    print(f" Packets Captured   : {metrics['packets_captured']:,}")
    print(f" Suspicious Packets : {metrics['suspicious_packets']:,}")
    print(f" Total Alerts       : {metrics['total_alerts']:,}")
    print(f" High Risk Alerts   : {metrics['high_risk_alerts']:,}")
    print("-" * 55)
    print("                   RECENT ALERTS")
    print("-" * 55)

    if not alerts:
        print("  [No alerts triggered yet - traffic normal]")
    else:
        for a in alerts:
            print(f"  [{a['risk_level']}] {a['attack_type']}")
            print(f"    Source: {a['source_ip']}  -->  Target: {a['destination_ip']}")
            print(f"    Details: {a['description']}")
            print(f"    Time: {a['timestamp']}")
            print("  " + "-" * 51)
    print("=" * 55 + "\n")

def run_demo_mode(engine: CaptureEngine, db: DatabaseManager):
    """
    Simulates network traffic and security incidents sequentially
    to demonstrate all 4 detection capabilities.
    """
    print("\n>>> DEMO MODE STARTED <<<")
    print("Simulating network traffic and automated intrusion patterns...\n")

    time.sleep(1)

    # 1. Benign Traffic
    print("[1/5] Injecting normal web browsing traffic (HTTP/HTTPS)...")
    for _ in range(8):
        pkt = IP(src="192.168.1.50", dst="93.184.216.34") / TCP(sport=54321, dport=443, flags="A")
        engine.process_packet(pkt)
        time.sleep(0.05)
    print("   -> Normal traffic logged to database.")

    time.sleep(1)

    # 2. Port Scan Attack
    print("\n[2/5] Simulating PORT SCAN attack from 192.168.1.15 on 192.168.1.20...")
    for port in range(20, 42):  # Contacts 22 distinct ports (exceeds threshold 15)
        pkt = IP(src="192.168.1.15", dst="192.168.1.20") / TCP(sport=49152 + port, dport=port, flags="S")
        engine.process_packet(pkt)
        time.sleep(0.03)

    time.sleep(1)

    # 3. Abnormal Traffic / DoS Burst Attack
    print("\n[3/5] Simulating ABNORMAL TRAFFIC / DoS flood from 192.168.1.18...")
    for _ in range(210):  # Exceeds burst threshold 200
        pkt = IP(src="192.168.1.18", dst="192.168.1.1") / UDP(sport=60000, dport=53)
        engine.process_packet(pkt)
    print("   -> 210 packets transmitted in burst.")

    time.sleep(1)

    # 4. Repeated Connection Attempt Attack
    print("\n[4/5] Simulating REPEATED CONNECTION attempts from 192.168.1.25...")
    for _ in range(35):  # Exceeds threshold 30
        pkt = IP(src="192.168.1.25", dst="192.168.1.5") / TCP(sport=33333, dport=80, flags="S")
        engine.process_packet(pkt)
        time.sleep(0.02)

    time.sleep(1)

    # 5. ICMP Ping Flood Anomaly
    print("\n[5/5] Simulating ICMP PING FLOOD from 192.168.1.99...")
    for _ in range(20):  # Exceeds threshold 15
        pkt = IP(src="192.168.1.99", dst="192.168.1.1") / ICMP()
        engine.process_packet(pkt)
        time.sleep(0.02)

    time.sleep(1)

    print("\n>>> SIMULATION COMPLETE! Printing final system dashboard summary: <<<")
    print_status_summary(db)

def run_live_mode(engine: CaptureEngine, db: DatabaseManager, iface: Optional[str] = None):
    """Runs live packet capture on network interface."""
    print(f"\n[+] Starting live packet capture on interface: {iface or 'System Default'}...")
    print("[+] Press Ctrl+C at any time to stop monitoring.\n")

    engine.start(iface=iface)

    try:
        while engine.is_running:
            time.sleep(5)
            print_status_summary(db)
    except KeyboardInterrupt:
        print("\n[!] Stopping packet capture...")
    finally:
        engine.stop()
        print("[+] Final session summary:")
        print_status_summary(db)

def main():
    parser = argparse.ArgumentParser(description="Network Intrusion Detection System (NIDS)")
    parser.add_argument(
        "--mode",
        choices=["live", "demo"],
        default="demo",
        help="Run mode: 'demo' (simulates attacks & shows alerts) or 'live' (sniffs active network traffic). Default: demo"
    )
    parser.add_argument(
        "--interface",
        type=str,
        default=None,
        help="Network interface name or IP for live capture (optional)"
    )

    args = parser.parse_args()

    print(BANNER)
    db = DatabaseManager()
    engine = CaptureEngine(db_manager=db)

    if args.mode == "demo":
        run_demo_mode(engine, db)
    else:
        run_live_mode(engine, db, iface=args.interface)

if __name__ == "__main__":
    main()
