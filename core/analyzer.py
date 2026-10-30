"""
Traffic Analyzer & Sliding Window State Tracker
Maintains rolling temporal state to detect anomalies (Chapter 4.2 & 5.2-5.5).
"""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple, Set

class TrafficAnalyzer:
    def __init__(self):
        self._lock = threading.Lock()
        # source_ip -> deque of (timestamp, destination_port)
        self.port_history: Dict[str, Deque[Tuple[float, int]]] = defaultdict(deque)
        # source_ip -> deque of timestamps
        self.packet_rate_history: Dict[str, Deque[float]] = defaultdict(deque)
        # (source_ip, destination_ip) -> deque of timestamps
        self.connection_history: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
        # source_ip -> deque of ICMP packet timestamps
        self.icmp_history: Dict[str, Deque[float]] = defaultdict(deque)

    def record_packet(self, source_ip: str, destination_ip: str, protocol: str,
                      destination_port: int = None, is_syn: bool = False,
                      timestamp: float = None):
        """Record packet occurrence into rolling state buffers."""
        ts = timestamp or time.time()

        with self._lock:
            # 1. Packet rate history (all IP packets)
            self.packet_rate_history[source_ip].append(ts)

            # 2. Port history (TCP / UDP destination ports)
            if destination_port is not None:
                self.port_history[source_ip].append((ts, destination_port))

            # 3. Connection history (Track repeated connections / SYN attempts)
            if is_syn or protocol == "TCP":
                self.connection_history[(source_ip, destination_ip)].append(ts)

            # 4. ICMP history
            if protocol == "ICMP":
                self.icmp_history[source_ip].append(ts)

    def get_unique_ports_in_window(self, source_ip: str, window_seconds: float) -> Set[int]:
        """Return unique destination ports contacted by source_ip within window."""
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            history = self.port_history[source_ip]
            # Prune old entries
            while history and history[0][0] < cutoff:
                history.popleft()
            return {port for ts, port in history}

    def get_packet_count_in_window(self, source_ip: str, window_seconds: float) -> int:
        """Return total packet count from source_ip within window."""
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            history = self.packet_rate_history[source_ip]
            while history and history[0] < cutoff:
                history.popleft()
            return len(history)

    def get_connection_count_in_window(self, source_ip: str, destination_ip: str,
                                       window_seconds: float) -> int:
        """Return connection attempts between source and destination within window."""
        now = time.time()
        cutoff = now - window_seconds
        key = (source_ip, destination_ip)
        with self._lock:
            history = self.connection_history[key]
            while history and history[0] < cutoff:
                history.popleft()
            return len(history)

    def get_icmp_count_in_window(self, source_ip: str, window_seconds: float) -> int:
        """Return total ICMP packets from source_ip within window."""
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            history = self.icmp_history[source_ip]
            while history and history[0] < cutoff:
                history.popleft()
            return len(history)

    def reset(self):
        """Clear all active buffers."""
        with self._lock:
            self.port_history.clear()
            self.packet_rate_history.clear()
            self.connection_history.clear()
            self.icmp_history.clear()
