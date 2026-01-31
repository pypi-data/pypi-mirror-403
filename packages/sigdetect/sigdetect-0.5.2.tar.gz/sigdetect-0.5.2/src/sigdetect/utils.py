"""Utility helpers shared across detectors."""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import suppress
from importlib import resources
from typing import Any, Pattern

import yaml
from pypdf import generic

_PACKAGE_NAME = "sigdetect.data"
_VENDOR_FILE = "vendor_patterns.yml"


def LoadPatterns(profileName: str | None = None) -> dict[str, Any]:
    """Return the merged vendor and role patterns for the requested profile."""

    roleCandidates: list[str] = []
    if profileName:
        roleCandidates.append(f"role_rules.{profileName}.yml")
    roleCandidates.append("role_rules.yml")

    rolePatterns: dict[str, Any] = {}
    for candidate in roleCandidates:
        try:
            with resources.files(_PACKAGE_NAME).joinpath(candidate).open("rb") as handle:
                rolePatterns = yaml.safe_load(handle) or {}
                break
        except FileNotFoundError:
            continue

    with resources.files(_PACKAGE_NAME).joinpath(_VENDOR_FILE).open("rb") as handle:
        vendorPatterns = yaml.safe_load(handle) or {}

    rolePatterns.setdefault("bytes", vendorPatterns.get("bytes"))
    rolePatterns.setdefault("text", vendorPatterns.get("text"))
    return rolePatterns


def NormalizeText(value: str) -> str:
    """Normalize whitespace so downstream regex work consistently."""

    return re.sub(r"\s+", " ", (value or "")).strip()


def AsDictionary(candidate: Any) -> Any:
    """Resolve pypdf indirect objects to their underlying dictionary."""

    if isinstance(candidate, generic.IndirectObject):
        with suppress(Exception):
            return candidate.get_object()
    return candidate


def IterateWidgets(candidate: Any) -> Iterator[Any]:
    """Yield widget dictionaries from any nested structure."""

    if candidate is None:
        return
    if isinstance(candidate, generic.IndirectObject):
        yield from IterateWidgets(candidate.get_object())
    elif isinstance(candidate, generic.ArrayObject):
        for item in candidate:
            yield from IterateWidgets(item)
    elif isinstance(candidate, generic.DictionaryObject):
        yield candidate


def HasSignatureFieldInAncestry(candidate: Any, maxHops: int = 12) -> bool:
    """Check if a dictionary or any parent declares a signature field type."""

    hopCount = 0
    current = AsDictionary(candidate)
    while isinstance(current, generic.DictionaryObject) and hopCount <= maxHops:
        if current.get("/FT") == "/Sig":
            return True
        current = AsDictionary(current.get("/Parent"))
        hopCount += 1
    return False


def HasSignatureValue(candidate: Any) -> bool:
    """Determine whether the widget or any parent contains signature metadata."""

    dictionaryCandidate = AsDictionary(candidate)
    if not isinstance(dictionaryCandidate, generic.DictionaryObject):
        return False

    valueCandidate = AsDictionary(dictionaryCandidate.get("/V"))
    if isinstance(valueCandidate, generic.DictionaryObject):
        if (
            valueCandidate.get("/Type") == "/Sig"
            or valueCandidate.get("/SubFilter")
            or valueCandidate.get("/Filter")
        ):
            return True

    parentCandidate = AsDictionary(dictionaryCandidate.get("/Parent"))
    if isinstance(parentCandidate, generic.DictionaryObject):
        parentValue = AsDictionary(parentCandidate.get("/V"))
        if isinstance(parentValue, generic.DictionaryObject):
            if (
                parentValue.get("/Type") == "/Sig"
                or parentValue.get("/SubFilter")
                or parentValue.get("/Filter")
            ):
                return True
    return False


def GetFieldNameFromAncestry(candidate: Any, maxHops: int = 12) -> str | None:
    """Return the closest field name (``/T``) in the widget hierarchy."""

    hopCount = 0
    current = AsDictionary(candidate)
    while isinstance(current, generic.DictionaryObject) and hopCount <= maxHops:
        fieldName = current.get("/T")
        if fieldName:
            try:
                return str(fieldName)
            except Exception:
                return None
        current = AsDictionary(current.get("/Parent"))
        hopCount += 1
    return None


def RolesFromLabels(text: str, labelPatterns: dict[str, Pattern[str]]) -> set[str]:
    """Identify roles that match the explicit label patterns."""

    normalizedText = NormalizeText(text)
    return {role for role, pattern in labelPatterns.items() if pattern.search(normalizedText)}


def RolesFromGeneral(text: str, generalPatterns: dict[str, Pattern[str]]) -> set[str]:
    """Identify roles using the broader, free-form regex patterns."""

    normalizedText = NormalizeText(text)
    return {role for role, pattern in generalPatterns.items() if pattern.search(normalizedText)}


def ChooseRole(scores: dict[str, int]) -> str:
    """Return the dominant role based on the supplied score mapping."""

    if not scores:
        return "unknown"
    topScore = max(scores.values())
    winners = [role for role, value in scores.items() if value == topScore]
    return winners[0] if len(winners) == 1 and topScore > 0 else "unknown"
