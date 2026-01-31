"""Detector exports and factory helpers."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Type

from .base_detector import Detector
from .file_result_model import FileResult
from .pypdf2_engine import PyPDF2Detector
from .signature_model import Signature

if TYPE_CHECKING:  # pragma: no cover - typing only
    from sigdetect.config import DetectConfiguration


ENGINE_REGISTRY: dict[str, Type[Detector]] = {
    PyPDF2Detector.Name: PyPDF2Detector,
}

# Accept modern engine alias alongside legacy configuration default.
ENGINE_REGISTRY.setdefault("pypdf", PyPDF2Detector)

try:  # pragma: no cover - optional dependency
    from .pymupdf_engine import PyMuPDFDetector
    from .pymupdf_engine import fitz as pymupdf_fitz  # type: ignore

    if pymupdf_fitz is not None and getattr(PyMuPDFDetector, "Name", None):
        ENGINE_REGISTRY[PyMuPDFDetector.Name] = PyMuPDFDetector
    else:
        PyMuPDFDetector = None  # type: ignore
except Exception:
    PyMuPDFDetector = None  # type: ignore


def BuildDetector(configuration: DetectConfiguration) -> Detector:
    """Instantiate the configured engine or raise a clear error."""

    # Force geometry-capable engine selection (auto prefers PyMuPDF when available).
    engine_name = "auto"
    normalized = str(engine_name).lower()

    if normalized == "auto":
        detector_cls: Type[Detector] | None = None
        if PyMuPDFDetector is not None:
            detector_cls = (
                ENGINE_REGISTRY.get(getattr(PyMuPDFDetector, "Name", "")) or PyMuPDFDetector
            )
        if detector_cls is None:
            detector_cls = ENGINE_REGISTRY.get(PyPDF2Detector.Name) or ENGINE_REGISTRY.get("pypdf")
            warnings.warn(
                "Engine 'auto' falling back to 'pypdf2' because PyMuPDF is unavailable",
                RuntimeWarning,
                stacklevel=2,
            )
        if detector_cls is None:
            available = ", ".join(sorted(ENGINE_REGISTRY)) or "<none>"
            raise ValueError(f"No available detector engines. Available engines: {available}")
        return detector_cls(configuration)

    detector_cls = ENGINE_REGISTRY.get(normalized)
    if detector_cls is None:
        available = ", ".join(sorted(ENGINE_REGISTRY)) or "<none>"
        raise ValueError(f"Unsupported engine '{engine_name}'. Available engines: {available}")
    return detector_cls(configuration)


__all__ = [
    "BuildDetector",
    "Detector",
    "ENGINE_REGISTRY",
    "FileResult",
    "Signature",
]
