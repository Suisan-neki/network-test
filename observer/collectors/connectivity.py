from __future__ import annotations

import re
from typing import Any, Callable

from .command import CommandResult, run_command

CommandRunner = Callable[[list[str], int], CommandResult]

RTT_RE = re.compile(r"time[=<]([\d.]+)\s*ms")


def parse_ping_result(stdout: str, stderr: str, returncode: int) -> dict[str, Any]:
    match = RTT_RE.search(stdout)
    rtt_ms = float(match.group(1)) if match else None
    ok = (
        returncode == 0
        and ("bytes from" in stdout or "1 received" in stdout or "0% packet loss" in stdout)
    )

    error = None
    if not ok:
        error = stderr.strip() or (stdout.strip().splitlines()[-1] if stdout.strip() else "ping failed")

    return {"ok": ok, "rtt_ms": rtt_ms, "error": error}


def ping_target(target: str, command_runner: CommandRunner = run_command) -> dict[str, Any]:
    result = command_runner(["ping", "-c", "1", "-W", "1", target], 3)
    parsed = parse_ping_result(result.stdout, result.stderr, result.returncode)
    parsed["target"] = target
    return parsed


def collect_connectivity(
    ping_ip: str,
    ping_dns: str,
    command_runner: CommandRunner = run_command,
) -> dict[str, Any]:
    return {
        "ip": ping_target(ping_ip, command_runner=command_runner),
        "dns": ping_target(ping_dns, command_runner=command_runner),
    }

