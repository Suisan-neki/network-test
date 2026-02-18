from __future__ import annotations

from typing import Any, Callable

from .command import CommandResult, run_command

CommandRunner = Callable[[list[str], int], CommandResult]


def parse_ip_br_addr(output: str) -> dict[str, dict[str, Any]]:
    interfaces: dict[str, dict[str, Any]] = {}

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        parts = line.split()
        if len(parts) < 2:
            continue

        name = parts[0]
        state = parts[1]
        ipv4 = None

        for token in parts[2:]:
            if "/" in token and ":" not in token:
                ipv4 = token.split("/", 1)[0]
                break

        interfaces[name] = {"name": name, "state": state, "ip": ipv4}

    return interfaces


def parse_default_route(output: str) -> dict[str, str]:
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line.startswith("default "):
            continue

        tokens = line.split()
        route: dict[str, str] = {"raw": line}
        if "via" in tokens:
            idx = tokens.index("via")
            if idx + 1 < len(tokens):
                route["via"] = tokens[idx + 1]
        if "dev" in tokens:
            idx = tokens.index("dev")
            if idx + 1 < len(tokens):
                route["dev"] = tokens[idx + 1]
        return route

    return {}


def collect_interface_status(
    wan_if: str,
    lan_if: str,
    command_runner: CommandRunner = run_command,
) -> dict[str, Any]:
    errors: list[str] = []
    addr_result = command_runner(["ip", "-br", "addr"], 3)
    route_result = command_runner(["ip", "route"], 3)

    if addr_result.returncode != 0:
        errors.append(addr_result.stderr.strip() or "ip -br addr failed")
    if route_result.returncode != 0:
        errors.append(route_result.stderr.strip() or "ip route failed")

    interfaces = parse_ip_br_addr(addr_result.stdout)
    wan = interfaces.get(wan_if, {"name": wan_if, "state": "UNKNOWN", "ip": None})
    lan = interfaces.get(lan_if, {"name": lan_if, "state": "UNKNOWN", "ip": None})

    return {
        "interfaces": {"wan": wan, "lan": lan, "all": interfaces},
        "default_route": parse_default_route(route_result.stdout),
        "errors": errors,
    }

