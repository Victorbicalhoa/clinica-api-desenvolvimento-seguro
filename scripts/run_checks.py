"""Executa todas as verificacoes; o gate interpreta os codigos sem mascarar falhas."""

import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    reports = Path("reports")
    reports.mkdir(exist_ok=True)
    # Uma falha de rede/scanner nunca deve reutilizar resultado de execucao anterior.
    for name in (
        "execution.json",
        "pytest.xml",
        "bandit.json",
        "pip-audit.json",
        "zap.json",
        "gate.json",
    ):
        (reports / name).unlink(missing_ok=True)
    checks = {
        "ruff": ["ruff", "check", "--no-cache", "app", "tests", "scripts"],
        "format": ["ruff", "format", "--check", "--no-cache", "app", "tests", "scripts"],
        "pytest": ["pytest", "-q", "-p", "no:cacheprovider", "--junitxml=reports/pytest.xml"],
        "bandit": [
            "bandit",
            "-r",
            "app",
            "--ignore-nosec",
            "-f",
            "json",
            "-o",
            "reports/bandit.json",
        ],
        "pip_audit": [
            "pip_audit",
            "-r",
            "requirements.txt",
            "--no-deps",
            "--disable-pip",
            "--cache-dir",
            ".cache/pip-audit-ex12",
            "--progress-spinner",
            "off",
            "-f",
            "json",
            "-o",
            "reports/pip-audit.json",
        ],
    }
    status = {}
    for name, command in checks.items():
        try:
            result = subprocess.run(
                [sys.executable, "-m", *command],
                capture_output=True,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                timeout=600,
            )
            status[name] = result.returncode
            output = (result.stdout + result.stderr).decode("utf-8", errors="replace")
        except (OSError, subprocess.TimeoutExpired) as exc:
            status[name], output = 99, type(exc).__name__
        (reports / f"{name}.txt").write_text(output, encoding="utf-8")
        print(f"{name}: exit {status[name]}", flush=True)
        (reports / "execution.json").write_text(json.dumps(status, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
