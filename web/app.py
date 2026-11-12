"""
Flask Web Application & API Server for NIDS Dashboard
Provides real-time metrics, alert feed, log export, and interactive simulation trigger.
"""

from pathlib import Path
from flask import Flask, render_template, jsonify, send_file, request

from database.db_manager import DatabaseManager
from core.capture import CaptureEngine
from tools.attack_simulator import AttackSimulator
from tools.export_logs import export_alerts_to_csv, export_traffic_to_csv, export_alerts_to_json

BASE_DIR = Path(__file__).resolve().parent.parent

def create_app(engine: CaptureEngine = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "web" / "templates"),
        static_folder=str(BASE_DIR / "web" / "static")
    )

    db = DatabaseManager()
    capture_engine = engine or CaptureEngine(db_manager=db)
    simulator = AttackSimulator(engine=capture_engine)

    @app.route("/")
    def index():
        return render_template("index.html")

    # API: System summary metrics
    @app.route("/api/metrics")
    def get_metrics():
        metrics = db.get_summary_metrics()
        metrics["is_monitoring"] = capture_engine.is_running
        return jsonify(metrics)

    # API: Protocol breakdown for doughnut chart
    @app.route("/api/protocols")
    def get_protocols():
        distribution = db.get_protocol_distribution()
        return jsonify(distribution)

    # API: Recent alerts feed
    @app.route("/api/alerts")
    def get_alerts():
        limit = request.args.get("limit", default=25, type=int)
        alerts = db.get_recent_alerts(limit=limit)
        return jsonify(alerts)

    # API: Recent raw traffic
    @app.route("/api/traffic")
    def get_traffic():
        limit = request.args.get("limit", default=50, type=int)
        traffic = db.get_recent_traffic(limit=limit)
        return jsonify(traffic)

    # API: Top offending IP sources
    @app.route("/api/top-offenders")
    def get_top_offenders():
        limit = request.args.get("limit", default=5, type=int)
        offenders = db.get_top_offenders(limit=limit)
        return jsonify(offenders)

    # API: Export alerts to CSV
    @app.route("/api/export/alerts/csv")
    def export_alerts_csv():
        out_path = export_alerts_to_csv()
        return send_file(out_path, as_attachment=True, download_name="ids_alerts.csv")

    # API: Export alerts to JSON
    @app.route("/api/export/alerts/json")
    def export_alerts_json():
        out_path = export_alerts_to_json()
        return send_file(out_path, as_attachment=True, download_name="ids_alerts.json")

    # API: Export traffic to CSV
    @app.route("/api/export/traffic/csv")
    def export_traffic_csv():
        out_path = export_traffic_to_csv()
        return send_file(out_path, as_attachment=True, download_name="ids_traffic.csv")

    # API: Interactive simulation trigger from web UI
    @app.route("/api/simulate/<attack_type>", methods=["POST"])
    def simulate_attack(attack_type):
        if attack_type == "portscan":
            simulator.simulate_port_scan()
        elif attack_type == "traffic":
            simulator.simulate_abnormal_traffic()
        elif attack_type == "repeated":
            simulator.simulate_repeated_connections()
        elif attack_type == "icmp":
            simulator.simulate_icmp_anomaly()
        elif attack_type == "benign":
            simulator.simulate_benign_traffic()
        elif attack_type == "all":
            simulator.run_all()
        else:
            return jsonify({"status": "error", "message": "Unknown attack type"}), 400

        return jsonify({"status": "success", "simulated": attack_type})

    # API: Clear / reset database logs
    @app.route("/api/clear", methods=["POST"])
    def clear_database():
        db.clear_all()
        capture_engine.analyzer.reset()
        capture_engine._last_alert_time.clear()
        return jsonify({"status": "cleared"})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
