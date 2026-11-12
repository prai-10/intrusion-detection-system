"""
Network Intrusion Detection System - Attack Simulator Tool
Generates controlled synthetic traffic to demonstrate all 4 attack vectors (Chapter 5.2 - 5.5).
Can inject packets directly into the running CaptureEngine or transmit over network.
"""

import time
import random
import argparse
from typing import Optional
from scapy.layers.inet import IP, TCP, UDP, ICMP
from core.capture import CaptureEngine
from database.db_manager import DatabaseManager
import config

class AttackSimulator:
    def __init__(self, engine: Optional[CaptureEngine] = None):
        self.engine = engine or CaptureEngine()

    def simulate_benign_traffic(self, count: int = 25):
        """Generates regular web, DNS, and secure browsing traffic."""
        print(f"[+] Simulating {count} normal packets (HTTP, HTTPS, DNS)...")
        sample_ips = ["192.168.1.101", "192.168.1.102", "192.168.1.103", "192.168.1.104"]
        destinations = [("8.8.8.8", 53, "UDP"), ("1.1.1.1", 53, "UDP"),
                        ("142.250.190.46", 443, "TCP"), ("93.184.216.34", 80, "TCP")]

        for _ in range(count):
            src = random.choice(sample_ips)
            dst, dport, proto = random.choice(destinations)
            sport = random.randint(30000, 60000)

            if proto == "TCP":
                pkt = IP(src=src, dst=dst) / TCP(sport=sport, dport=dport, flags="A")
            else:
                pkt = IP(src=src, dst=dst) / UDP(sport=sport, dport=dport)

            self.engine.process_packet(pkt)
            time.sleep(0.02)
        print("    Normal traffic injected successfully.")

    def simulate_port_scan(self, src_ip: str = "192.168.1.45", target_ip: str = "192.168.1.1", port_count: int = 25):
        """
        Simulates Port Scan attack (Chapter 5.2).
        Sends SYN packets to a sequential range of destination ports.
        """
        print(f"[!] Simulating Port Scan from {src_ip} targeting {target_ip} ({port_count} ports)...")
        ports = random.sample(range(20, 1024), min(port_count, 1000))
        for p in ports:
            pkt = IP(src=src_ip, dst=target_ip) / TCP(sport=random.randint(40000, 65000), dport=p, flags="S")
            self.engine.process_packet(pkt)
            time.sleep(0.015)
        print("    Port Scan simulation complete.")

    def simulate_abnormal_traffic(self, src_ip: str = "192.168.1.66", target_ip: str = "192.168.1.1", packet_count: int = 220):
        """
        Simulates Abnormal Traffic / Volumetric Burst (Chapter 5.3).
        Sends high volume of packets in short duration.
        """
        print(f"[!] Simulating Abnormal Traffic / DoS burst from {src_ip} ({packet_count} packets)...")
        for _ in range(packet_count):
            pkt = IP(src=src_ip, dst=target_ip) / UDP(sport=random.randint(20000, 60000), dport=8080)
            self.engine.process_packet(pkt)
        print("    Abnormal traffic burst complete.")

    def simulate_repeated_connections(self, src_ip: str = "192.168.1.77", target_ip: str = "192.168.1.2", attempts: int = 35):
        """
        Simulates Repeated Connection attempts (Chapter 5.4).
        Repeatedly sends connection requests to a single service port.
        """
        print(f"[!] Simulating Repeated Connection attempts from {src_ip} -> {target_ip} ({attempts} attempts)...")
        for _ in range(attempts):
            pkt = IP(src=src_ip, dst=target_ip) / TCP(sport=random.randint(30000, 60000), dport=443, flags="S")
            self.engine.process_packet(pkt)
            time.sleep(0.01)
        print("    Repeated connections simulation complete.")

    def simulate_icmp_anomaly(self, src_ip: str = "192.168.1.88", target_ip: str = "192.168.1.1", ping_count: int = 20):
        """
        Simulates ICMP Anomaly / Ping Flood (Chapter 5.5).
        """
        print(f"[!] Simulating ICMP Ping Flood from {src_ip} -> {target_ip} ({ping_count} pings)...")
        for _ in range(ping_count):
            pkt = IP(src=src_ip, dst=target_ip) / ICMP()
            self.engine.process_packet(pkt)
            time.sleep(0.015)
        print("    ICMP Anomaly simulation complete.")

    def run_all(self):
        """Runs the complete suite of simulation scenarios."""
        print("==================================================")
        print("     STARTING COMPREHENSIVE ATTACK SIMULATION     ")
        print("==================================================")
        self.simulate_benign_traffic(20)
        time.sleep(1)
        self.simulate_port_scan()
        time.sleep(1)
        self.simulate_abnormal_traffic()
        time.sleep(1)
        self.simulate_repeated_connections()
        time.sleep(1)
        self.simulate_icmp_anomaly()
        print("\nAll simulations completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IDS Attack Simulator")
    parser.add_argument("--attack", choices=["all", "portscan", "traffic", "repeated", "icmp", "benign"], default="all")
    args = parser.parse_args()

    db = DatabaseManager()
    sim = AttackSimulator(CaptureEngine(db_manager=db))

    if args.attack == "all":
        sim.run_all()
    elif args.attack == "portscan":
        sim.simulate_port_scan()
    elif args.attack == "traffic":
        sim.simulate_abnormal_traffic()
    elif args.attack == "repeated":
        sim.simulate_repeated_connections()
    elif args.attack == "icmp":
        sim.simulate_icmp_anomaly()
    elif args.attack == "benign":
        sim.simulate_benign_traffic()
