"""
Log and Alert Exporter (Chapter 3.2 Secondary Objective 6)
Exports SQLite traffic and alert data to CSV and JSON formats.
"""

import csv
import json
from pathlib import Path
from typing import Optional
from database.db_manager import DatabaseManager
import config

def export_alerts_to_csv(filepath: Optional[str] = None) -> str:
    db = DatabaseManager()
    alerts = db.get_recent_alerts(limit=10000)
    out_path = Path(filepath or (config.DATA_DIR / "exported_alerts.csv"))

    fieldnames = ["alert_id", "timestamp", "source_ip", "destination_ip", "attack_type", "description", "risk_level", "status"]
    with open(out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(alerts)

    return str(out_path)

def export_traffic_to_csv(filepath: Optional[str] = None) -> str:
    db = DatabaseManager()
    traffic = db.get_recent_traffic(limit=10000)
    out_path = Path(filepath or (config.DATA_DIR / "exported_traffic.csv"))

    fieldnames = ["traffic_id", "timestamp", "source_ip", "destination_ip", "protocol", "source_port", "destination_port", "packet_size"]
    with open(out_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(traffic)

    return str(out_path)

def export_alerts_to_json(filepath: Optional[str] = None) -> str:
    db = DatabaseManager()
    alerts = db.get_recent_alerts(limit=10000)
    out_path = Path(filepath or (config.DATA_DIR / "exported_alerts.json"))

    with open(out_path, mode="w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    return str(out_path)
