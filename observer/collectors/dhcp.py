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
CANDIDATE_LEASE_PATHS = (
    "/var/lib/dhcp/dhcpd.leases",
    "/var/lib/misc/dnsmasq.leases",
)


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


def parse_dnsmasq_leases(content: str) -> list[dict[str, Any]]:
    leases: list[dict[str, Any]] = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        # dnsmasq format: <epoch> <mac> <ip> <hostname> <client-id>
        parts = line.split()
        if len(parts) < 4:
            continue

        expires_raw, mac, ip, hostname = parts[0], parts[1], parts[2], parts[3]
        last_seen = ""
        try:
            last_seen = datetime.utcfromtimestamp(int(expires_raw)).isoformat(sep=" ")
        except ValueError:
            last_seen = ""

        leases.append(
            {
                "ip": ip,
                "mac": mac.lower(),
                "hostname": "" if hostname == "*" else hostname,
                "state": "active",
                "last_seen": last_seen,
            }
        )

    return sorted(leases, key=lambda x: x["last_seen"], reverse=True)


def _resolve_lease_path(path: str) -> Path | None:
    if path and path.lower() != "auto":
        lease_path = Path(path)
        return lease_path if lease_path.exists() else None

    for candidate in CANDIDATE_LEASE_PATHS:
        candidate_path = Path(candidate)
        if candidate_path.exists():
            return candidate_path
    return None


def collect_dhcp_leases(path: str = "auto") -> list[dict[str, Any]]:
    lease_path = _resolve_lease_path(path)
    if lease_path is None:
        return []

    try:
        content = lease_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    if lease_path.name == "dnsmasq.leases":
        return parse_dnsmasq_leases(content)
    return parse_dhcp_leases(content)
