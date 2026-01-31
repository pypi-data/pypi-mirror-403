"""Compatibility module exporting detector primitives."""

from __future__ import annotations

from .base_detector import Detector
from .file_result_model import FileResult
from .signature_model import Signature

__all__ = ["Detector", "FileResult", "Signature"]
