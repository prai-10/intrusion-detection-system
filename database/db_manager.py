"""
SQLite Database Manager for Network Intrusion Detection System
Implements the tables and query interfaces specified in Chapter 5.8
"""

import sqlite3
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional
from config import DB_PATH

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: Optional[str] = None):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return
        self.db_path = db_path or DB_PATH
        self._thread_local = threading.local()
        self._init_db()
        self._initialized = True

    def _get_connection(self) -> sqlite3.Connection:
        """Provide a thread-local SQLite connection with WAL enabled."""
        if not hasattr(self._thread_local, "conn") or self._thread_local.conn is None:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for high concurrent throughput
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            self._thread_local.conn = conn
        return self._thread_local.conn

    def _init_db(self):
        """Create necessary tables and indices as specified in Chapter 5.8."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Network Traffic Table (Chapter 5.8)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_traffic (
                traffic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                destination_ip TEXT NOT NULL,
                protocol TEXT NOT NULL,
                source_port INTEGER,
                destination_port INTEGER,
                packet_size INTEGER NOT NULL
            );
        """)

        # Alerts Table (Chapter 5.8)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                source_ip TEXT NOT NULL,
                destination_ip TEXT NOT NULL,
                attack_type TEXT NOT NULL,
                description TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ACTIVE'
            );
        """)

        # Create indices for fast dashboard queries and stats
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_time ON network_traffic(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_src ON network_traffic(source_ip);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alerts_risk ON alerts(risk_level);")
        conn.commit()

    def log_traffic(self, source_ip: str, destination_ip: str, protocol: str,
                    source_port: Optional[int], destination_port: Optional[int],
                    packet_size: int, timestamp: Optional[str] = None) -> int:
        """Insert a captured packet record into network_traffic table."""
        ts = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO network_traffic (
                timestamp, source_ip, destination_ip, protocol,
                source_port, destination_port, packet_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ts, source_ip, destination_ip, protocol, source_port, destination_port, packet_size))
        conn.commit()
        return cursor.lastrowid

    def log_alert(self, source_ip: str, destination_ip: str, attack_type: str,
                  description: str, risk_level: str, status: str = "ACTIVE",
                  timestamp: Optional[str] = None) -> int:
        """Insert a detected intrusion event into alerts table."""
        ts = timestamp or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (
                timestamp, source_ip, destination_ip, attack_type,
                description, risk_level, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (ts, source_ip, destination_ip, attack_type, description, risk_level, status))
        conn.commit()
        return cursor.lastrowid

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch latest alerts ordered by timestamp descending."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT alert_id, timestamp, source_ip, destination_ip,
                   attack_type, description, risk_level, status
            FROM alerts
            ORDER BY alert_id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_recent_traffic(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetch latest network packets ordered by timestamp descending."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT traffic_id, timestamp, source_ip, destination_ip,
                   protocol, source_port, destination_port, packet_size
            FROM network_traffic
            ORDER BY traffic_id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_summary_metrics(self) -> Dict[str, int]:
        """Return high level dashboard metrics (Chapter 5.9)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM network_traffic")
        total_packets = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM alerts WHERE risk_level = 'HIGH'")
        high_risk_alerts = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT source_ip) FROM alerts")
        suspicious_hosts = cursor.fetchone()[0]

        return {
            "packets_captured": total_packets,
            "total_alerts": total_alerts,
            "high_risk_alerts": high_risk_alerts,
            "suspicious_packets": total_alerts * 5,  # Estimated suspicious packet cluster
            "suspicious_hosts": suspicious_hosts
        }

    def get_protocol_distribution(self) -> Dict[str, int]:
        """Return packet counts grouped by protocol."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT protocol, COUNT(*) as count
            FROM network_traffic
            GROUP BY protocol
            ORDER BY count DESC
        """)
        return {row["protocol"]: row["count"] for row in cursor.fetchall()}

    def get_top_offenders(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Return source IPs with highest number of triggered alerts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT source_ip, COUNT(*) as alert_count,
                   MAX(risk_level) as highest_risk
            FROM alerts
            GROUP BY source_ip
            ORDER BY alert_count DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def clear_all(self):
        """Helper to clear database for testing purposes."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM alerts;")
        cursor.execute("DELETE FROM network_traffic;")
        conn.commit()
