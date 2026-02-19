from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import Flask, jsonify, render_template

from observer.collectors.connectivity import collect_connectivity
from observer.collectors.dhcp import collect_dhcp_leases
from observer.collectors.interfaces import collect_interface_status
from observer.collectors.logs import collect_logs
from observer.collectors.nat import collect_nat_status
from observer.config import load_config


def build_status(config: dict[str, Any]) -> dict[str, Any]:
    interface_data = collect_interface_status(config["WAN_IF"], config["LAN_IF"])
    nat = collect_nat_status()
    connectivity = collect_connectivity(config["PING_IP"], config["PING_DNS"])
    return {
        "interfaces": interface_data["interfaces"],
        "default_route": interface_data["default_route"],
        "nat": nat,
        "connectivity": connectivity,
        "errors": interface_data.get("errors", []),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def create_app(config_path: str | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    config = load_config(config_path)
    app.config["OBSERVER"] = config

    @app.get("/")
    def index() -> str:
        cfg = app.config["OBSERVER"]
        return render_template(
            "index.html",
            refresh=cfg["REFRESH"],
            wan_if=cfg["WAN_IF"],
            lan_if=cfg["LAN_IF"],
            ping_ip=cfg["PING_IP"],
            ping_dns=cfg["PING_DNS"],
        )

    @app.get("/api/status")
    def api_status():
        return jsonify(build_status(app.config["OBSERVER"]))

    @app.get("/api/dhcp_leases")
    def api_dhcp_leases():
        cfg = app.config["OBSERVER"]
        return jsonify(collect_dhcp_leases(cfg.get("DHCP_LEASE_FILE", "auto")))

    @app.get("/api/logs")
    def api_logs():
        return jsonify(collect_logs())

    return app


if __name__ == "__main__":
    app = create_app()
    cfg = app.config["OBSERVER"]
    app.run(host="0.0.0.0", port=int(cfg["PORT"]))
