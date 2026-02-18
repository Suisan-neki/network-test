from __future__ import annotations

import re
from typing import Any, Callable

from .command import CommandResult, run_command

CommandRunner = Callable[[list[str], int], CommandResult]
LOG_RE = re.compile(r"^(\S+)\s+\S+\s+([^:]+):\s?(.*)$")


def classify_log_message(message: str) -> str:
    msg = message.lower()
    if "dhcpack" in msg or "discover" in msg:
        return "DHCP"
    if "link is up" in msg or "link is down" in msg:
        return "LINK"
    if "get /" in msg or "post /" in msg:
        return "HTTP"
    if "started" in msg or "failed" in msg:
        return "SYSTEM"
    return "OTHER"


def parse_journal_output(output: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = LOG_RE.match(line)
        if match:
            ts, source, msg = match.groups()
        else:
            parts = line.split(maxsplit=2)
            ts = parts[0] if parts else ""
            source = "journal"
            msg = parts[2] if len(parts) > 2 else line

        entries.append(
            {
                "ts": ts,
                "source": source,
                "type": classify_log_message(msg),
                "msg": msg,
            }
        )
    return entries


def collect_logs(limit: int = 200, command_runner: CommandRunner = run_command) -> list[dict[str, Any]]:
    result = command_runner(["journalctl", "-n", str(limit), "--no-pager", "-o", "short-iso"], 4)
    if result.returncode != 0 and not result.stdout:
        return []
    return parse_journal_output(result.stdout)

