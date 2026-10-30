"""
Packet Parser and Feature Extractor
Extracts network attributes from Scapy packets (Chapter 4.2 & 5.1).
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6
from scapy.packet import Packet

@dataclass
class PacketInfo:
    timestamp: float
    formatted_time: str
    source_ip: str
    destination_ip: str
    protocol: str
    source_port: Optional[int]
    destination_port: Optional[int]
    packet_size: int
    tcp_flags: Optional[str] = None
    is_syn: bool = False
    raw_packet: Optional[Packet] = None

class PacketParser:
    @staticmethod
    def parse(packet: Packet) -> Optional[PacketInfo]:
        """
        Parses a raw Scapy packet into a structured PacketInfo instance.
        Returns None if packet does not contain IP layer.
        """
        timestamp = time.time()
        formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        src_ip = None
        dst_ip = None
        protocol = "OTHER"
        src_port = None
        dst_port = None
        tcp_flags = None
        is_syn = False

        if packet.haslayer(IP):
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
        elif packet.haslayer(IPv6):
            src_ip = packet[IPv6].src
            dst_ip = packet[IPv6].dst
        else:
            return None

        # Protocol & Port Extraction
        if packet.haslayer(TCP):
            protocol = "TCP"
            src_port = int(packet[TCP].sport)
            dst_port = int(packet[TCP].dport)
            tcp_flags = str(packet[TCP].flags)
            is_syn = "S" in tcp_flags and "A" not in tcp_flags
        elif packet.haslayer(UDP):
            protocol = "UDP"
            src_port = int(packet[UDP].sport)
            dst_port = int(packet[UDP].dport)
        elif packet.haslayer(ICMP):
            protocol = "ICMP"
        else:
            protocol = packet.lastlayer().name.upper()

        packet_size = len(packet)

        return PacketInfo(
            timestamp=timestamp,
            formatted_time=formatted_time,
            source_ip=src_ip,
            destination_ip=dst_ip,
            protocol=protocol,
            source_port=src_port,
            destination_port=dst_port,
            packet_size=packet_size,
            tcp_flags=tcp_flags,
            is_syn=is_syn,
            raw_packet=packet
        )
