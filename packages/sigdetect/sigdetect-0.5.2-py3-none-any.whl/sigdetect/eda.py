"""Exploratory data analysis helpers for signature detection output."""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .config import DetectConfiguration

ConsoleInstance = Console()


def _SafeNumber(value: Any, defaultValue: float | None = None) -> float | None:
    """Attempt to coerce ``value`` to ``float`` while tolerating bad input."""

    try:
        return float(value)
    except Exception:
        return defaultValue


def _FormatSizeStatistics(sizeValues: list[float]) -> str:
    """Return a ``min / median / max`` summary for ``sizeValues``."""

    if not sizeValues:
        return "—"
    sortedValues = sorted(value for value in sizeValues if value is not None)
    if not sortedValues:
        return "—"
    minimum = int(round(sortedValues[0]))
    median = int(round(statistics.median(sortedValues)))
    maximum = int(round(sortedValues[-1]))
    return f"{minimum} / {median} / {maximum}"


def _LoadResults(resultsPath: Path) -> list[dict[str, Any]]:
    """Load ``results.json`` from disk and guard against malformed content."""

    if not resultsPath.exists():
        ConsoleInstance.print(f"[yellow]No results.json found at {resultsPath}[/yellow]")
        return []
    try:
        data = json.loads(resultsPath.read_text())
    except Exception as exc:
        ConsoleInstance.print(f"[red]Failed to read {resultsPath}: {exc}[/red]")
        return []
    if not isinstance(data, list):
        ConsoleInstance.print(f"[red]results.json is not a list: {type(data)}[/red]")
        return []
    return data


def _FlattenSignatures(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collate signature dictionaries found within ``rows``."""

    signatures: list[dict[str, Any]] = []
    for row in rows:
        for signature in row.get("signatures") or []:
            if isinstance(signature, dict):
                signatures.append(signature)
    return signatures


def RunExploratoryAnalysis(configuration: DetectConfiguration) -> None:
    """Print a compact summary of the detection output defined by ``configuration``."""

    outputDirectory = configuration.OutputDirectory or configuration.PdfRoot
    resultsPath = outputDirectory / "results.json"
    rows = _LoadResults(resultsPath)

    if not rows:
        ConsoleInstance.print("[yellow]No results to summarize.[/yellow]")
        return

    totalCount = len(rows)
    electronicSignatureCount = sum(1 for row in rows if bool(row.get("esign_found")))
    wetSignatureCount = totalCount - electronicSignatureCount
    scannedCount = sum(1 for row in rows if bool(row.get("scanned_pdf")))
    mixedCount = sum(1 for row in rows if bool(row.get("mixed")))
    sizeValues = [
        _SafeNumber(row.get("size_kb"))
        for row in rows
        if _SafeNumber(row.get("size_kb")) is not None
    ]

    table = Table(show_header=True, header_style="bold")
    table.add_column("Total", justify="right")
    table.add_column("E-sign", justify="right")
    table.add_column("Wet", justify="right")
    table.add_column("Scans", justify="right")
    table.add_column("Mixed", justify="right")
    table.add_column("Size KB (min/med/max)", justify="left")

    table.add_row(
        str(totalCount),
        str(electronicSignatureCount),
        str(wetSignatureCount),
        str(scannedCount),
        str(mixedCount),
        _FormatSizeStatistics(sizeValues),
    )
    ConsoleInstance.print(table)

    signatures = _FlattenSignatures(rows)
    roleCounts = Counter((signature.get("role") or "unknown") for signature in signatures)

    if signatures:
        ConsoleInstance.print("\nSignature roles (per-signature) — including unknown:")
        preferredOrder = [
            "patient",
            "representative",
            "client",
            "firm",
            "attorney",
            "unknown",
        ]
        seenRoles = set()
        orderedRoles: list[str] = []
        for role in preferredOrder:
            if role in roleCounts:
                orderedRoles.append(role)
                seenRoles.add(role)
        for role in sorted(roleCounts):
            if role not in seenRoles:
                orderedRoles.append(role)

        bulletLines = [f" • {role:<13} — {roleCounts[role]}" for role in orderedRoles]
        ConsoleInstance.print("\n".join(bulletLines))
        ConsoleInstance.print(f"(total signatures tallied: {sum(roleCounts.values())})\n")
    else:
        ConsoleInstance.print("\n[dim]No signatures found to break down by role.[/dim]\n")
