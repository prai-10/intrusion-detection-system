"""
Unit & Integration Test Suite for NIDS (Parts 1 & 2)
Verifies:
1. Packet parsing
2. Port Scan detection rule
3. Abnormal traffic detection rule
4. Repeated connection detection rule
5. ICMP anomaly detection rule
6. Risk scoring algorithm
7. SQLite persistence and metric queries
"""

import os
import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scapy.layers.inet import IP, TCP, UDP, ICMP
from database.db_manager import DatabaseManager
from core.capture import CaptureEngine
from core.parser import PacketParser
from core.risk_scorer import RiskScorer
import config

class TestIntrusionDetectionSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use an isolated test database
        cls.test_db_path = str(config.DATA_DIR / "test_ids.db")
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
        cls.db = DatabaseManager(db_path=cls.test_db_path)
        cls.engine = CaptureEngine(db_manager=cls.db)

    def setUp(self):
        self.db.clear_all()
        self.engine.analyzer.reset()
        self.engine._last_alert_time.clear()

    def test_01_packet_parser(self):
        """Test extraction of packet fields (IP, TCP, Ports, Flags)."""
        pkt = IP(src="192.168.1.10", dst="192.168.1.20") / TCP(sport=12345, dport=80, flags="S")
        info = PacketParser.parse(pkt)
        
        self.assertIsNotNone(info)
        self.assertEqual(info.source_ip, "192.168.1.10")
        self.assertEqual(info.destination_ip, "192.168.1.20")
        self.assertEqual(info.protocol, "TCP")
        self.assertEqual(info.source_port, 12345)
        self.assertEqual(info.destination_port, 80)
        self.assertTrue(info.is_syn)

    def test_02_benign_traffic(self):
        """Verify normal traffic is recorded in DB without raising alerts."""
        for port in [80, 443]:
            pkt = IP(src="10.0.0.5", dst="10.0.0.1") / TCP(sport=50000, dport=port, flags="A")
            self.engine.process_packet(pkt)

        metrics = self.db.get_summary_metrics()
        self.assertEqual(metrics["packets_captured"], 2)
        self.assertEqual(metrics["total_alerts"], 0)

    def test_03_port_scan_detection(self):
        """Verify port scan rule detects scans exceeding threshold."""
        scanner_ip = "192.168.1.99"
        target_ip = "192.168.1.1"

        # Send packets to 20 different ports (Threshold is 15)
        triggered_alert = None
        for port in range(1, 22):
            pkt = IP(src=scanner_ip, dst=target_ip) / TCP(sport=40000 + port, dport=port, flags="S")
            alert = self.engine.process_packet(pkt)
            if alert:
                triggered_alert = alert

        self.assertIsNotNone(triggered_alert)
        self.assertEqual(triggered_alert.attack_type, "Port Scan")
        self.assertEqual(triggered_alert.source_ip, scanner_ip)
        self.assertIn(triggered_alert.risk_level, ["MEDIUM", "HIGH"])

        # Check DB persistence
        alerts_in_db = self.db.get_recent_alerts(limit=5)
        self.assertTrue(any(a["attack_type"] == "Port Scan" for a in alerts_in_db))

    def test_04_abnormal_traffic_detection(self):
        """Verify DoS / volumetric burst rule flags abnormal rate."""
        flooder_ip = "10.0.0.100"
        target_ip = "10.0.0.1"

        triggered_alert = None
        # Send packets exceeding TRAFFIC_BURST_THRESHOLD (200)
        for i in range(210):
            pkt = IP(src=flooder_ip, dst=target_ip) / UDP(sport=5000, dport=53)
            alert = self.engine.process_packet(pkt)
            if alert:
                triggered_alert = alert

        self.assertIsNotNone(triggered_alert)
        self.assertEqual(triggered_alert.attack_type, "Abnormal Traffic")
        self.assertEqual(triggered_alert.source_ip, flooder_ip)
        self.assertIn(triggered_alert.risk_level, ["MEDIUM", "HIGH"])

    def test_05_repeated_connections_detection(self):
        """Verify repeated connection rule flags repeated attempts to same host."""
        attacker_ip = "192.168.1.75"
        target_ip = "192.168.1.200"

        triggered_alert = None
        # Send > REPEATED_CONN_THRESHOLD (30) SYN packets
        for _ in range(35):
            pkt = IP(src=attacker_ip, dst=target_ip) / TCP(sport=55555, dport=80, flags="S")
            alert = self.engine.process_packet(pkt)
            if alert:
                triggered_alert = alert

        self.assertIsNotNone(triggered_alert)
        self.assertEqual(triggered_alert.attack_type, "Repeated Connections")
        self.assertEqual(triggered_alert.source_ip, attacker_ip)

    def test_06_icmp_anomaly_detection(self):
        """Verify ICMP ping flood rule triggers correctly."""
        pinger_ip = "192.168.1.88"
        target_ip = "192.168.1.1"

        triggered_alert = None
        # Send > ICMP_THRESHOLD (15) ping packets
        for _ in range(20):
            pkt = IP(src=pinger_ip, dst=target_ip) / ICMP()
            alert = self.engine.process_packet(pkt)
            if alert:
                triggered_alert = alert

        self.assertIsNotNone(triggered_alert)
        self.assertEqual(triggered_alert.attack_type, "ICMP Anomaly")
        self.assertEqual(triggered_alert.source_ip, pinger_ip)

    def test_07_risk_scorer_ranges(self):
        """Verify the 0-100 risk score and range thresholds."""
        score_low, level_low = RiskScorer.calculate_risk("Custom", {})
        score_high, level_high = RiskScorer.calculate_risk("Abnormal Traffic", {"packet_count": 500, "threshold": 200})
        
        self.assertTrue(0 <= score_low <= 100)
        self.assertTrue(0 <= score_high <= 100)
        self.assertEqual(level_high, "HIGH")

    @classmethod
    def tearDownClass(cls):
        # Cleanup test database
        if os.path.exists(cls.test_db_path):
            try:
                os.remove(cls.test_db_path)
            except Exception:
                pass

if __name__ == "__main__":
    unittest.main()
