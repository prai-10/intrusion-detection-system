"""
Intrusion Detection Rules Engine
Implements the 4 detection methods described in Chapters 5.2 - 5.5:
1. Port Scan Detection
2. Abnormal Traffic Detection
3. Repeated Connection Detection
4. ICMP Anomaly Detection
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from core.parser import PacketInfo
from core.analyzer import TrafficAnalyzer
from core.risk_scorer import RiskScorer
import config

@dataclass
class DetectionAlert:
    source_ip: str
    destination_ip: str
    attack_type: str
    description: str
    score: int
    risk_level: str
    metadata: Dict[str, Any]

class RuleEngine:
    def __init__(self, analyzer: TrafficAnalyzer):
        self.analyzer = analyzer

    def evaluate(self, pkt: PacketInfo) -> Optional[DetectionAlert]:
        """
        Evaluate packet against all detection rules.
        Returns the highest severity alert if any rule triggers.
        """
        # Update rolling state first
        self.analyzer.record_packet(
            source_ip=pkt.source_ip,
            destination_ip=pkt.destination_ip,
            protocol=pkt.protocol,
            destination_port=pkt.destination_port,
            is_syn=pkt.is_syn,
            timestamp=pkt.timestamp
        )

        alerts = []

        # 1. Port Scan Detection (Chapter 5.2)
        if pkt.destination_port is not None:
            unique_ports = self.analyzer.get_unique_ports_in_window(
                pkt.source_ip, config.PORT_SCAN_WINDOW_SEC
            )
            if len(unique_ports) >= config.PORT_SCAN_THRESHOLD:
                details = {
                    "unique_ports": len(unique_ports),
                    "threshold": config.PORT_SCAN_THRESHOLD,
                    "window_sec": config.PORT_SCAN_WINDOW_SEC,
                    "sampled_ports": sorted(list(unique_ports))[:10]
                }
                score, level = RiskScorer.calculate_risk("Port Scan", details)
                alerts.append(DetectionAlert(
                    source_ip=pkt.source_ip,
                    destination_ip=pkt.destination_ip,
                    attack_type="Port Scan",
                    description=(
                        f"Possible Port Scan detected from {pkt.source_ip}: "
                        f"scanned {len(unique_ports)} distinct ports within {config.PORT_SCAN_WINDOW_SEC}s "
                        f"(threshold: {config.PORT_SCAN_THRESHOLD})"
                    ),
                    score=score,
                    risk_level=level,
                    metadata=details
                ))

        # 2. Abnormal Traffic / DoS Detection (Chapter 5.3)
        packet_count = self.analyzer.get_packet_count_in_window(
            pkt.source_ip, config.TRAFFIC_BURST_WINDOW_SEC
        )
        if packet_count >= config.TRAFFIC_BURST_THRESHOLD:
            details = {
                "packet_count": packet_count,
                "threshold": config.TRAFFIC_BURST_THRESHOLD,
                "window_sec": config.TRAFFIC_BURST_WINDOW_SEC
            }
            score, level = RiskScorer.calculate_risk("Abnormal Traffic", details)
            alerts.append(DetectionAlert(
                source_ip=pkt.source_ip,
                destination_ip=pkt.destination_ip,
                attack_type="Abnormal Traffic",
                description=(
                    f"Abnormal traffic volume from {pkt.source_ip}: "
                    f"{packet_count} packets in {config.TRAFFIC_BURST_WINDOW_SEC}s "
                    f"(threshold: {config.TRAFFIC_BURST_THRESHOLD})"
                ),
                score=score,
                risk_level=level,
                metadata=details
            ))

        # 3. Repeated Connection Detection (Chapter 5.4)
        if pkt.is_syn or pkt.protocol == "TCP":
            conn_count = self.analyzer.get_connection_count_in_window(
                pkt.source_ip, pkt.destination_ip, config.REPEATED_CONN_WINDOW_SEC
            )
            if conn_count >= config.REPEATED_CONN_THRESHOLD:
                details = {
                    "attempts": conn_count,
                    "threshold": config.REPEATED_CONN_THRESHOLD,
                    "window_sec": config.REPEATED_CONN_WINDOW_SEC
                }
                score, level = RiskScorer.calculate_risk("Repeated Connections", details)
                alerts.append(DetectionAlert(
                    source_ip=pkt.source_ip,
                    destination_ip=pkt.destination_ip,
                    attack_type="Repeated Connections",
                    description=(
                        f"Repeated connection attempts from {pkt.source_ip} to {pkt.destination_ip}: "
                        f"{conn_count} attempts in {config.REPEATED_CONN_WINDOW_SEC}s "
                        f"(threshold: {config.REPEATED_CONN_THRESHOLD})"
                    ),
                    score=score,
                    risk_level=level,
                    metadata=details
                ))

        # 4. ICMP Anomaly Detection (Chapter 5.5)
        if pkt.protocol == "ICMP":
            icmp_count = self.analyzer.get_icmp_count_in_window(
                pkt.source_ip, config.ICMP_WINDOW_SEC
            )
            if icmp_count >= config.ICMP_THRESHOLD:
                details = {
                    "icmp_count": icmp_count,
                    "threshold": config.ICMP_THRESHOLD,
                    "window_sec": config.ICMP_WINDOW_SEC
                }
                score, level = RiskScorer.calculate_risk("ICMP Anomaly", details)
                alerts.append(DetectionAlert(
                    source_ip=pkt.source_ip,
                    destination_ip=pkt.destination_ip,
                    attack_type="ICMP Anomaly",
                    description=(
                        f"Unusual ICMP traffic rate from {pkt.source_ip}: "
                        f"{icmp_count} ping packets in {config.ICMP_WINDOW_SEC}s "
                        f"(threshold: {config.ICMP_THRESHOLD})"
                    ),
                    score=score,
                    risk_level=level,
                    metadata=details
                ))

        if not alerts:
            return None

        # Return the alert with highest score
        return max(alerts, key=lambda a: a.score)
