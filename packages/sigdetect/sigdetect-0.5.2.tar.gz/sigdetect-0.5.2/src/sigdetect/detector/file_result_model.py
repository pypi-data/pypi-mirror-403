"""Result container returned from detection engines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .signature_model import Signature


@dataclass(slots=True)
class FileResult:
    """Aggregated detection outcome for a single PDF file."""

    File: str
    SizeKilobytes: float | None
    PageCount: int
    ElectronicSignatureFound: bool
    ScannedPdf: bool | None
    MixedContent: bool | None
    SignatureCount: int
    SignaturePages: str
    Roles: str
    Hints: str
    Signatures: list[Signature] = field(default_factory=list)

    # Backwards-compatible attribute aliases
    @property
    def Pages(self) -> int:  # pragma: no cover - simple passthrough
        return self.PageCount

    @property
    def pages(self) -> int:  # pragma: no cover - simple passthrough
        return self.PageCount

    @property
    def sig_pages(self) -> str:  # pragma: no cover - simple passthrough
        return self.SignaturePages

    @property
    def sig_count(self) -> int:  # pragma: no cover - simple passthrough
        return self.SignatureCount

    def to_dict(self) -> dict[str, Any]:
        """Return the legacy snake_case representation used by existing clients."""

        return {
            "file": self.File,
            "size_kb": self.SizeKilobytes,
            "pages": self.PageCount,
            "esign_found": self.ElectronicSignatureFound,
            "scanned_pdf": self.ScannedPdf,
            "mixed": self.MixedContent,
            "sig_count": self.SignatureCount,
            "sig_pages": self.SignaturePages,
            "roles": self.Roles,
            "hints": self.Hints,
            "signatures": [signature.to_dict() for signature in self.Signatures],
        }
