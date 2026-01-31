"""PyMuPDF-backed detector that augments PyPDF2 heuristics with geometry."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, cast

from .pypdf2_engine import PyPDF2Detector
from .signature_model import Signature

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    fitz = None  # type: ignore[misc]


class PyMuPDFDetector(PyPDF2Detector):
    """Detector that reuses PyPDF2 heuristics and annotates results via PyMuPDF."""

    Name = "pymupdf"
    SIGNATURE_PADDING = 64.0
    ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
        "client": ("client", "consumer", "claimant"),
        "firm": ("firm", "attorney", "attorneys", "counsel", "company", "llp", "llc", "law", "by:"),
        "patient": ("patient", "self", "plaintiff"),
        "representative": ("representative", "guardian", "parent"),
        "attorney": ("attorney", "counsel", "lawyer"),
    }

    def __init__(self, configuration):
        if fitz is None:  # pragma: no cover - optional dependency
            raise ValueError(
                "PyMuPDF engine requires the optional 'pymupdf' dependency. Install 'pymupdf' or add "
                "it to your environment."
            )
        super().__init__(configuration)

    def Detect(self, pdf_path: Path):  # type: ignore[override]
        result = super().Detect(pdf_path)

        try:
            document = fitz.open(str(pdf_path))
        except Exception:  # pragma: no cover - defensive
            return result

        with document:
            widget_map = self._CollectWidgetRects(document)
            self._ApplyWidgetRects(result.Signatures, widget_map)
            self._InferPseudoRects(result.Signatures, document)
        return result

    # ───────────────────────────────── widget helpers ─────────────────────────────────
    def _CollectWidgetRects(
        self, document
    ) -> dict[tuple[int, str], tuple[float, float, float, float]]:
        mapping: dict[tuple[int, str], tuple[float, float, float, float]] = {}
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            widgets = page.widgets() if hasattr(page, "widgets") else None
            if not widgets:
                continue
            for widget in widgets:
                name = (widget.field_name or "").strip()
                if not name:
                    continue
                # Prefer true signature widgets but fall back to any widget with /Sig appearance
                if getattr(widget, "field_type", None) not in {
                    getattr(fitz, "PDF_WIDGET_TYPE_SIGNATURE", 6)
                }:
                    continue
                rect = self._RectToPdfTuple(widget.rect, page.rect.height)
                mapping[(page_index + 1, name)] = rect
        return mapping

    def _ApplyWidgetRects(
        self,
        signatures: Iterable[Signature],
        widget_map: dict[tuple[int, str], tuple[float, float, float, float]],
    ) -> None:
        for signature in signatures:
            if signature.BoundingBox or not signature.FieldName or not signature.Page:
                continue
            key = (signature.Page, signature.FieldName.strip())
            rect = widget_map.get(key)
            if rect:
                signature.BoundingBox = rect

    # ───────────────────────────── pseudo bbox inference ─────────────────────────────
    def _InferPseudoRects(self, signatures: Iterable[Signature], document) -> None:
        for signature in signatures:
            if signature.BoundingBox or signature.FieldName != "vendor_or_acro_detected":
                continue

            if signature.Page and signature.Page - 1 >= document.page_count:
                continue

            if signature.Page:
                candidate_pages = [signature.Page - 1]
            else:
                candidate_pages = list(range(document.page_count - 1, -1, -1))

            for page_index in candidate_pages:
                if page_index < 0 or page_index >= document.page_count:
                    continue
                page = document.load_page(page_index)
                lines = self._ExtractLines(page)
                rect_info = self._FindRoleLineRect(page, signature.Role, lines)
                if rect_info is None:
                    rect_info = self._FallbackSignatureRect(page, signature.Role, lines)
                if rect_info is not None:
                    rect, exclusion, mode = rect_info
                    padded = self._PadRect(rect, page.rect, signature.Role, exclusion, mode)
                    signature.BoundingBox = self._RectToPdfTuple(padded, page.rect.height)
                    signature.RenderType = "drawn"
                    if signature.Page is None:
                        signature.Page = page_index + 1
                    break

    def _FindRoleLineRect(
        self,
        page,
        role: str,
        lines: list[dict[str, float | str]] | None = None,
    ) -> tuple[fitz.Rect, float | None, str] | None:
        if lines is None:
            lines = self._ExtractLines(page)
        page_height = float(page.rect.height)
        keywords = self.ROLE_KEYWORDS.get(role, ())
        lower_roles = {"client", "firm", "representative", "attorney"}
        if self.Profile == "retainer" and role in {"client", "firm"}:
            min_factor = 0.15 if role == "client" else 0.4
            min_y = page_height * min_factor
        else:
            min_y = page_height * (0.58 if role == "firm" else 0.5) if role in lower_roles else 0.0

        def match_lines(require_signature: bool) -> list[tuple[int, dict[str, float | str]]]:
            selected: list[tuple[int, dict[str, float | str]]] = []
            for idx, line in enumerate(lines):
                lower = line["lower_text"]
                if lower.strip() == "":
                    continue
                if line["y0"] < min_y:
                    continue
                if require_signature and "sign" not in lower:
                    continue
                if not require_signature and "sign" not in lower:
                    if "name" in lower or "print" in lower:
                        continue
                if keywords and not any(keyword in lower for keyword in keywords):
                    continue
                selected.append((idx, line))
            return selected

        matches = match_lines(require_signature=True)
        if matches and matches[-1][1]["y0"] < page_height * 0.6:
            matches = []
        if not matches:
            matches = match_lines(require_signature=False)

        if matches:
            idx, target = matches[-1]
            label_rect = fitz.Rect(target["x0"], target["y0"], target["x1"], target["y1"])
            stroke = self._LocateStrokeLine(lines, idx, label_rect)
            if stroke is not None:
                rect, exclusion = stroke
                return rect, exclusion, "stroke"
            image = self._LocateSignatureImage(page, label_rect)
            if image is not None:
                exclusion = self._NextExclusionY(lines, idx + 1, image.y1)
                return image, exclusion, "image"
            exclusion = self._NextExclusionY(lines, idx + 1, label_rect.y1)
            return label_rect, exclusion, "label"
        return None

    def _FallbackSignatureRect(
        self,
        page,
        role: str | None = None,
        lines: list[dict[str, float | str]] | None = None,
    ) -> tuple[fitz.Rect, float | None, str] | None:
        if lines is None:
            lines = self._ExtractLines(page)
        for idx in range(len(lines) - 1, -1, -1):
            line = lines[idx]
            lower = line["lower_text"]
            if "signature" in lower or "sign" in lower:
                rect = fitz.Rect(line["x0"], line["y0"], line["x1"], line["y1"])
                exclusion = self._NextExclusionY(lines, idx + 1, rect.y1)
                return rect, exclusion, "label"
        if lines:
            line = lines[-1]
            rect = fitz.Rect(line["x0"], line["y0"], line["x1"], line["y1"])
            exclusion = None
            return rect, exclusion, "label"
        return None

    def _ExtractLines(self, page) -> list[dict[str, float | str]]:
        words = page.get_text("words") or []
        buckets: dict[tuple[int, int], dict[str, object]] = {}
        for x0, y0, x1, y1, text, block, line, *_ in words:
            if not text.strip():
                continue
            key = (int(block), int(line))
            bucket = buckets.setdefault(
                key,
                {
                    "tokens": [],
                    "x0": float(x0),
                    "y0": float(y0),
                    "x1": float(x1),
                    "y1": float(y1),
                },
            )
            tokens = cast(list[str], bucket["tokens"])
            tokens.append(text)
            bucket["x0"] = min(float(bucket["x0"]), float(x0))
            bucket["y0"] = min(float(bucket["y0"]), float(y0))
            bucket["x1"] = max(float(bucket["x1"]), float(x1))
            bucket["y1"] = max(float(bucket["y1"]), float(y1))
        lines: list[dict[str, float | str]] = []
        for bucket in buckets.values():
            text = " ".join(bucket["tokens"]).strip()  # type: ignore[arg-type]
            if not text:
                continue
            lines.append(
                {
                    "text": text,
                    "lower_text": text.lower(),
                    "x0": float(bucket["x0"]),
                    "y0": float(bucket["y0"]),
                    "x1": float(bucket["x1"]),
                    "y1": float(bucket["y1"]),
                }
            )
        lines.sort(key=lambda entry: (entry["y0"], entry["x0"]))
        return lines

    def _LocateStrokeLine(
        self,
        lines: list[dict[str, float | str]],
        label_index: int,
        label_rect: fitz.Rect,
    ) -> tuple[fitz.Rect, float | None] | None:
        for idx in range(label_index - 1, max(label_index - 4, -1), -1):
            lower = lines[idx]["lower_text"]
            if "_" in lower or lower.strip().startswith("x"):
                rect = fitz.Rect(
                    lines[idx]["x0"],
                    lines[idx]["y0"],
                    lines[idx]["x1"],
                    lines[idx]["y1"],
                )
                overlap = min(rect.x1, label_rect.x1) - max(rect.x0, label_rect.x0)
                if overlap <= 0:
                    continue
                # Keep crops below the label text.
                return rect, label_rect.y0
        return None

    def _LocateSignatureImage(self, page, label_rect: fitz.Rect) -> fitz.Rect | None:
        candidates: list[tuple[float, fitz.Rect]] = []
        label_mid_x = (label_rect.x0 + label_rect.x1) / 2.0
        for image in page.get_images(full=True):
            bbox = page.get_image_bbox(image)
            if bbox is None:
                continue
            width = float(bbox.width)
            height = float(bbox.height)
            if width < 40.0 or height < 12.0:
                continue
            if width > 380.0 or height > 220.0:
                continue
            # Require the image to sit near the label horizontally and vertically.
            horiz_overlap = min(bbox.x1, label_rect.x1 + 220.0) - max(bbox.x0, label_rect.x0 - 40.0)
            if horiz_overlap <= 0:
                continue
            vertical_gap = abs(((bbox.y0 + bbox.y1) / 2.0) - label_rect.y0)
            if vertical_gap > 220.0:
                continue
            candidates.append((vertical_gap + abs(((bbox.x0 + bbox.x1) / 2.0) - label_mid_x), bbox))

        if not candidates:
            return None
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _NextExclusionY(
        self,
        lines: list[dict[str, float | str]],
        start_index: int,
        minimum_y: float | None = None,
    ) -> float | None:
        threshold = (minimum_y or -float("inf")) + 1.0
        for line in lines[start_index:]:
            y0 = float(line["y0"])
            if y0 <= threshold:
                continue
            lower = line["lower_text"]
            if any(token in lower for token in ("name", "print", "date", "by:")):
                return y0
        return None

    def _RectToPdfTuple(self, rect, page_height: float) -> tuple[float, float, float, float]:
        x0 = float(rect.x0)
        x1 = float(rect.x1)
        y0 = page_height - float(rect.y1)
        y1 = page_height - float(rect.y0)
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        return (x0, y0, x1, y1)

    def _PadRect(
        self,
        rect,
        page_rect,
        role: str | None = None,
        exclusion_y0: float | None = None,
        mode: str = "label",
    ):
        """Return a region focused on the expected signature line beneath ``rect``."""

        max_width = 198.0  # 2.75 inches
        max_height = 72.0  # 1 inch

        pad_x = max(12.0, float(rect.width) * 0.08)
        if mode == "stroke":
            left = max(page_rect.x0, rect.x0 - 8.0)
            right = min(page_rect.x1, rect.x1 + 8.0)
        elif mode == "image":
            left = max(page_rect.x0, rect.x0 - 10.0)
            right = min(page_rect.x1, rect.x1 + 10.0)
        else:
            left = max(page_rect.x0, rect.x0 - pad_x)
            right = min(page_rect.x1, rect.x1 + pad_x)

        if self.Profile == "retainer" and role == "client" and mode in {"image", "label"}:
            left = max(page_rect.x0, rect.x0 - 12.0)
            right = min(page_rect.x1, rect.x1 + 16.0)
        elif self.Profile == "retainer" and role == "firm" and mode in {"image", "label"}:
            left = max(page_rect.x0, rect.x0 - 14.0)
            right = min(page_rect.x1, rect.x1 + 18.0)

        if right - left > max_width:
            if mode == "stroke":
                right = min(page_rect.x1, left + max_width)
            else:
                center = (left + right) / 2.0
                half = max_width / 2.0
                left = center - half
                right = center + half
                if left < page_rect.x0:
                    right += page_rect.x0 - left
                    left = page_rect.x0
                if right > page_rect.x1:
                    left -= right - page_rect.x1
                    right = page_rect.x1
                left = max(page_rect.x0, left)
                right = min(page_rect.x1, right)

        line_height = max(8.0, float(rect.height) or 12.0)
        signature_height = max(40.0, line_height * 2.2)
        if role == "client":
            signature_height = max(signature_height, 65.0)
        elif role == "firm":
            signature_height = max(signature_height, 60.0)
        elif role in {"representative", "patient", "attorney"}:
            signature_height = max(signature_height, 55.0)
        signature_height = min(signature_height, max_height)

        baseline = float(rect.y1)

        if mode == "stroke":
            margin_above = max(6.0, line_height)
            margin_below = max(18.0, line_height * 1.5)
            top = float(rect.y0) - margin_above
            bottom = float(rect.y1) + margin_below
            signature_height = min(bottom - top, max_height)
        elif mode == "image":
            image_height = float(rect.height) or 12.0
            signature_height = min(max_height, max(image_height + 18.0, 40.0))
            extra = max(0.0, signature_height - image_height)
            top = float(rect.y0) - min(extra * 0.25, 12.0)
            bottom = top + signature_height
            top = max(float(rect.y0) - 2.0, top)
            bottom = top + signature_height
        else:
            gap_above = max(10.0, min(24.0, line_height * 0.9))
            top = baseline + gap_above
            bottom = top + signature_height

        original_top = top

        if exclusion_y0 is not None:
            limited = exclusion_y0 - 4.0
            if bottom > limited:
                bottom = limited
                top = max(original_top, bottom - signature_height)
        if mode == "image":
            limit_below = float(rect.y1) + 24.0
            if bottom > limit_below:
                bottom = limit_below
                top = max(float(rect.y0) - 4.0, bottom - signature_height)

        if bottom - top > max_height:
            bottom = top + max_height
            signature_height = min(signature_height, max_height)

        if bottom > page_rect.y1:
            bottom = page_rect.y1
            top = max(original_top, bottom - signature_height)

        if bottom - top > max_height:
            bottom = top + max_height

        if top >= bottom:
            top = max(page_rect.y0, baseline - line_height)
            bottom = min(page_rect.y1, top + min(signature_height, max_height))

        return fitz.Rect(left, top, right, bottom)
