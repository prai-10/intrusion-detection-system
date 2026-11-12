"""
Unified Launcher for Network Intrusion Detection System (NIDS)
Starts:
1. Web Dashboard (Flask web server on http://localhost:5000)
2. Capture Engine (Live packet sniffing or in-memory simulation)
"""

import sys
import time
import argparse
import threading
import webbrowser
from scapy.layers.inet import IP, TCP, UDP, ICMP

from core.capture import CaptureEngine
from database.db_manager import DatabaseManager
from web.app import create_app
from tools.attack_simulator import AttackSimulator
import config

BANNER = r"""
============================================================
      INTRUSION DETECTION SYSTEM (NIDS) - UNIFIED
============================================================
 Web Dashboard : http://localhost:5000
 Database      : SQLite (data/ids.db)
 Architecture  : Scapy + Flask + Chart.js + Python
============================================================
"""

def print_terminal_summary(db: DatabaseManager):
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

def run_web_server(app, port=5000):
    """Run Flask server."""
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

def main():
    parser = argparse.ArgumentParser(description="Network Intrusion Detection System (NIDS)")
    parser.add_argument(
        "--mode",
        choices=["web", "live", "demo"],
        default="web",
        help="Run mode: 'web' (starts dashboard + interactive simulator), 'demo' (terminal simulation), 'live' (terminal live sniffing). Default: web"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for Web Dashboard (default: 5000)"
    )
    parser.add_argument(
        "--interface",
        type=str,
        default=None,
        help="Network interface name for live capture"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not auto-open default browser"
    )

    args = parser.parse_args()
    print(BANNER)

    db = DatabaseManager()
    engine = CaptureEngine(db_manager=db)

    if args.mode == "demo":
        sim = AttackSimulator(engine=engine)
        print("Running demo simulation...")
        sim.run_all()
        print_terminal_summary(db)
        return

    elif args.mode == "live":
        print(f"[+] Starting live capture on interface: {args.interface or 'Default'}...")
        engine.start(iface=args.interface)
        try:
            while engine.is_running:
                time.sleep(5)
                print_terminal_summary(db)
        except KeyboardInterrupt:
            print("\n[!] Stopping live capture...")
        finally:
            engine.stop()
            print_terminal_summary(db)
        return

    # Default 'web' mode: Start Web Dashboard + optional background engine
    app = create_app(engine=engine)

    # If interface is provided or live mode requested alongside web, start capture thread
    if args.interface:
        print(f"[+] Starting live background packet capture on {args.interface}...")
        engine.start(iface=args.interface)

    # Start Flask in separate thread
    server_thread = threading.Thread(target=run_web_server, args=(app, args.port), daemon=True)
    server_thread.start()

    print(f"\n🚀 Web Dashboard started successfully at: http://localhost:{args.port}")
    print("Press Ctrl+C to terminate.\n")

    if not args.no_browser:
        try:
            webbrowser.open(f"http://localhost:{args.port}")
        except Exception:
            pass

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[!] Shutting down NIDS...")
        if engine.is_running:
            engine.stop()
        print("[+] Goodbye!")

if __name__ == "__main__":
    main()
