from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    stdout: str
    stderr: str
    returncode: int


def run_command(cmd: list[str], timeout: int = 3) -> CommandResult:
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CommandResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )
    except Exception as exc:
        return CommandResult(stdout="", stderr=str(exc), returncode=1)

