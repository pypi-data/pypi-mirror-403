"""Signature model returned by detection engines."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Signature:
    """Metadata describing a detected signature field."""

    Page: int | None
    FieldName: str
    Role: str
    Score: int
    Scores: dict[str, int]
    Evidence: list[str]
    Hint: str
    RenderType: str = "typed"
    BoundingBox: tuple[float, float, float, float] | None = None
    CropPath: str | None = None
    CropBytes: str | None = None
    CropDocxPath: str | None = None
    CropDocxBytes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the legacy snake_case representation used in JSON payloads."""

        return {
            "page": self.Page,
            "field_name": self.FieldName,
            "role": self.Role,
            "score": self.Score,
            "scores": self.Scores,
            "evidence": list(self.Evidence),
            "hint": self.Hint,
            "render_type": self.RenderType,
            "bounding_box": list(self.BoundingBox) if self.BoundingBox else None,
            "crop_path": self.CropPath,
            "crop_bytes": self.CropBytes,
            "crop_docx_path": self.CropDocxPath,
            "crop_docx_bytes": self.CropDocxBytes,
        }
