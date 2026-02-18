from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

LEASE_BLOCK_RE = re.compile(r"lease\s+(\S+)\s+\{(.*?)\}", re.DOTALL)
MAC_RE = re.compile(r"hardware ethernet\s+([0-9a-fA-F:]+);")
HOST_RE = re.compile(r'client-hostname\s+"([^"]+)";')
STATE_RE = re.compile(r"binding state\s+(\w+);")
TIME_RE = re.compile(r"(?:\d+\s+)?(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})")


def _parse_lease_time(raw: str) -> datetime | None:
    matched = TIME_RE.search(raw)
    if not matched:
        return None
    try:
        return datetime.strptime(matched.group(1), "%Y/%m/%d %H:%M:%S")
    except ValueError:
        return None


def parse_dhcp_leases(content: str) -> list[dict[str, Any]]:
    leases_by_ip: dict[str, dict[str, Any]] = {}

    for ip, body in LEASE_BLOCK_RE.findall(content):
        mac_match = MAC_RE.search(body)
        host_match = HOST_RE.search(body)
        state_match = STATE_RE.search(body)

        time_candidates: list[datetime] = []
        for key in ("starts", "ends", "cltt"):
            m = re.search(rf"{key}\s+([^;]+);", body)
            if m:
                parsed = _parse_lease_time(m.group(1))
                if parsed:
                    time_candidates.append(parsed)

        lease_ts = max(time_candidates) if time_candidates else None
        lease = {
            "ip": ip,
            "mac": mac_match.group(1).lower() if mac_match else "",
            "hostname": host_match.group(1) if host_match else "",
            "state": state_match.group(1) if state_match else "unknown",
            "last_seen": lease_ts.isoformat(sep=" ") if lease_ts else "",
            "_ts": lease_ts or datetime.min,
        }

        existing = leases_by_ip.get(ip)
        if not existing or lease["_ts"] >= existing["_ts"]:
            leases_by_ip[ip] = lease

    leases = sorted(leases_by_ip.values(), key=lambda x: x["_ts"], reverse=True)
    for lease in leases:
        lease.pop("_ts", None)
    return leases


def collect_dhcp_leases(path: str = "/var/lib/dhcp/dhcpd.leases") -> list[dict[str, Any]]:
    lease_path = Path(path)
    try:
        content = lease_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    return parse_dhcp_leases(content)

