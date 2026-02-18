from __future__ import annotations

from typing import Any, Callable

from .command import CommandResult, run_command

CommandRunner = Callable[[list[str], int], CommandResult]


def parse_nat_postrouting(output: str) -> tuple[bool, str]:
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "MASQUERADE" in line:
            return True, line
    return False, ""


def collect_nat_status(command_runner: CommandRunner = run_command) -> dict[str, Any]:
    result = command_runner(["iptables", "-t", "nat", "-S", "POSTROUTING"], 3)
    enabled, rule = parse_nat_postrouting(result.stdout)
    return {
        "enabled": enabled,
        "rule": rule,
        "error": None if result.returncode == 0 else (result.stderr.strip() or "iptables failed"),
    }

