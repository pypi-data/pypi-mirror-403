"""Abstract base class for signature detection engines."""

from __future__ import annotations

from pathlib import Path

from .file_result_model import FileResult


class Detector:
    """Common interface implemented by concrete detectors."""

    Name: str = "base"

    def Detect(self, pdfPath: Path) -> FileResult:  # pragma: no cover
        """Analyse ``pdfPath`` and return detection results."""

        raise NotImplementedError

    # Provide backwards compatibility for snake_case callers
    def detect(self, pdfPath: Path) -> FileResult:  # pragma: no cover
        return self.Detect(pdfPath)
