"""
Risk Classification Algorithm
Implements scoring and threat level assignment (Chapter 5.6).
0–30: LOW
31–70: MEDIUM
71–100: HIGH
"""

from typing import Dict, Any, Tuple
from config import RISK_LEVEL_LOW, RISK_LEVEL_MEDIUM, RISK_LEVEL_HIGH

class RiskScorer:
    BASE_SCORES = {
        "Port Scan": 65,
        "Abnormal Traffic": 70,
        "Repeated Connections": 55,
        "ICMP Anomaly": 50,
    }

    @classmethod
    def calculate_risk(cls, attack_type: str, details: Dict[str, Any]) -> Tuple[int, str]:
        """
        Calculates a 0-100 score based on attack type and magnitude metrics,
        returning (score, risk_level).
        """
        base = cls.BASE_SCORES.get(attack_type, 40)
        multiplier_points = 0

        # Adjust score according to observed metrics
        if attack_type == "Port Scan":
            port_count = details.get("unique_ports", 0)
            threshold = details.get("threshold", 15)
            # More ports = higher severity
            excess_ratio = (port_count - threshold) / max(threshold, 1)
            multiplier_points = int(min(excess_ratio * 25, 30))

        elif attack_type == "Abnormal Traffic":
            packet_count = details.get("packet_count", 0)
            threshold = details.get("threshold", 200)
            excess_ratio = (packet_count - threshold) / max(threshold, 1)
            multiplier_points = int(min(excess_ratio * 30, 30))

        elif attack_type == "Repeated Connections":
            attempts = details.get("attempts", 0)
            threshold = details.get("threshold", 30)
            excess_ratio = (attempts - threshold) / max(threshold, 1)
            multiplier_points = int(min(excess_ratio * 25, 25))

        elif attack_type == "ICMP Anomaly":
            icmp_count = details.get("icmp_count", 0)
            threshold = details.get("threshold", 15)
            excess_ratio = (icmp_count - threshold) / max(threshold, 1)
            multiplier_points = int(min(excess_ratio * 30, 30))

        final_score = max(0, min(100, base + multiplier_points))

        # Classify into Low, Medium, High
        if final_score <= 30:
            level = RISK_LEVEL_LOW
        elif final_score <= 70:
            level = RISK_LEVEL_MEDIUM
        else:
            level = RISK_LEVEL_HIGH

        return final_score, level
