"""
Packet Capture & Processing Engine
Runs background sniffing, feeds packets to Parser, Analyzer, RuleEngine,
and logs traffic and detected alerts to SQLite.
"""

import time
import threading
import logging
from typing import Optional, Callable, Dict, Tuple
from scapy.all import sniff
from scapy.packet import Packet

from core.parser import PacketParser, PacketInfo
from core.analyzer import TrafficAnalyzer
from core.rules import RuleEngine, DetectionAlert
from database.db_manager import DatabaseManager
import config

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("IDS_CaptureEngine")

class CaptureEngine:
    def __init__(self, db_manager: Optional[DatabaseManager] = None,
                 on_alert_callback: Optional[Callable[[DetectionAlert], None]] = None,
                 on_packet_callback: Optional[Callable[[PacketInfo], None]] = None):
        self.db = db_manager or DatabaseManager()
        self.analyzer = TrafficAnalyzer()
        self.rules = RuleEngine(self.analyzer)
        
        self.on_alert_callback = on_alert_callback
        self.on_packet_callback = on_packet_callback
        
        self._is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        # Cooldown map: (source_ip, attack_type) -> timestamp of last logged alert
        self._last_alert_time: Dict[Tuple[str, str], float] = {}

    @property
    def is_running(self) -> bool:
        return self._is_running

    def process_packet(self, raw_packet: Packet) -> Optional[DetectionAlert]:
        """
        Core pipeline step:
        Parse packet -> Record to DB -> Evaluate Rules -> (If alert) Log Alert to DB.
        """
        pkt_info = PacketParser.parse(raw_packet)
        if not pkt_info:
            return None

        # 1. Log traffic event to SQLite
        try:
            self.db.log_traffic(
                source_ip=pkt_info.source_ip,
                destination_ip=pkt_info.destination_ip,
                protocol=pkt_info.protocol,
                source_port=pkt_info.source_port,
                destination_port=pkt_info.destination_port,
                packet_size=pkt_info.packet_size,
                timestamp=pkt_info.formatted_time
            )
        except Exception as e:
            logger.error(f"Error logging traffic: {e}")

        # Optional listener callback for UI
        if self.on_packet_callback:
            try:
                self.on_packet_callback(pkt_info)
            except Exception:
                pass

        # 2. Evaluate intrusion detection rules
        alert = self.rules.evaluate(pkt_info)
        if not alert:
            return None

        # 3. Check alert cooldown to prevent repetitive spam in database
        key = (alert.source_ip, alert.attack_type)
        now = time.time()
        last_time = self._last_alert_time.get(key, 0)
        
        if (now - last_time) >= config.ALERT_COOLDOWN_SEC:
            self._last_alert_time[key] = now
            logger.warning(
                f"[{alert.risk_level}] {alert.attack_type} detected from {alert.source_ip} "
                f"(Score: {alert.score}) - {alert.description}"
            )
            
            # Save alert to SQLite
            try:
                self.db.log_alert(
                    source_ip=alert.source_ip,
                    destination_ip=alert.destination_ip,
                    attack_type=alert.attack_type,
                    description=alert.description,
                    risk_level=alert.risk_level,
                    status="ACTIVE",
                    timestamp=pkt_info.formatted_time
                )
            except Exception as e:
                logger.error(f"Error logging alert: {e}")

            # Notify UI callback
            if self.on_alert_callback:
                try:
                    self.on_alert_callback(alert)
                except Exception:
                    pass

            return alert

        return None

    def _sniff_worker(self, iface: Optional[str] = None):
        """Worker function for Scapy sniff in background thread."""
        logger.info(f"Starting packet capture on interface: {iface or 'DEFAULT'}...")
        try:
            sniff(
                iface=iface,
                prn=self.process_packet,
                store=False,
                stop_filter=lambda _: not self._is_running
            )
        except Exception as e:
            logger.error(f"Sniffing error or interface permission issue: {e}")
        finally:
            self._is_running = False
            logger.info("Packet capture stopped.")

    def start(self, iface: Optional[str] = None):
        """Start capturing in a background thread."""
        with self._lock:
            if self._is_running:
                logger.warning("Capture engine is already running.")
                return
            self._is_running = True
            self._thread = threading.Thread(
                target=self._sniff_worker,
                kwargs={"iface": iface or config.DEFAULT_INTERFACE},
                daemon=True
            )
            self._thread.start()

    def stop(self):
        """Stop packet capture thread."""
        with self._lock:
            if not self._is_running:
                return
            self._is_running = False
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=2.0)
            logger.info("Capture engine stopped successfully.")
