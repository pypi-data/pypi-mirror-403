"""Wet signature detection via OCR-backed heuristics."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image

from sigdetect.config import DetectConfiguration
from sigdetect.detector.file_result_model import FileResult
from sigdetect.detector.signature_model import Signature

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    fitz = None  # type: ignore[misc]

try:  # pragma: no cover - optional dependency
    import pytesseract  # type: ignore
    from pytesseract import Output as TesseractOutput
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None  # type: ignore[assignment]
    TesseractOutput = None  # type: ignore[assignment]


LOGGER = logging.getLogger("sigdetect.wet")

SIGNATURE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsignature\b"),
    re.compile(r"\bsigned\b"),
    re.compile(r"\bsign\b"),
    re.compile(r"\bsignature\s+of\b"),
    re.compile(r"\bsignature\s*:"),
    re.compile(r"\bsignature\s*-"),
    re.compile(r"\bby:\b"),
)

ROLE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "client": ("client", "consumer", "claimant"),
    "firm": ("firm", "attorney", "counsel", "by:", "esq", "law"),
    "patient": ("patient", "self", "plaintiff"),
    "representative": ("guardian", "representative", "parent", "poa"),
    "attorney": ("attorney", "counsel", "lawyer"),
}


class WetDetectionUnavailable(RuntimeError):
    """Raised when OCR-backed detection cannot run."""


@dataclass
class OcrLine:
    """Structured OCR line extracted from pytesseract."""

    text: str
    confidence: float
    left: int
    top: int
    right: int
    bottom: int


def should_run_wet_pipeline(file_result: FileResult) -> bool:
    """Return ``True`` when the OCR pipeline should run for ``file_result``."""

    return not bool(file_result.ElectronicSignatureFound)


def apply_wet_detection(
    pdf_path: Path,
    configuration: DetectConfiguration,
    file_result: FileResult,
    *,
    logger: logging.Logger | None = None,
) -> bool:
    """Augment ``file_result`` with OCR-detected wet signatures when possible."""

    if not should_run_wet_pipeline(file_result):
        return False

    try:
        _ensure_dependencies()
    except WetDetectionUnavailable as exc:
        _mark_manual_review(file_result, str(exc))
        if logger:
            logger.warning("Wet detection unavailable", extra={"error": str(exc)})
        return False

    original_esign = file_result.ElectronicSignatureFound
    original_mixed = file_result.MixedContent
    try:
        added = _detect(pdf_path, configuration, file_result, logger=logger)
        if added and configuration.Profile == "hipaa":
            updated = False
            for signature in file_result.Signatures:
                if signature.RenderType == "wet" and (signature.Role or "unknown") == "unknown":
                    signature.Role = "patient"
                    signature.Scores = {"patient": int(signature.Score or 0)}
                    signature.Evidence = list(signature.Evidence or [])
                    signature.Evidence.append("role_default:patient")
                    updated = True
            if updated:
                _refresh_metadata(file_result)
        if not added:
            _mark_manual_review(file_result, "NoHighConfidenceWetSignature")
        return added
    except Exception as exc:  # pragma: no cover - defensive
        _mark_manual_review(file_result, "WetDetectionError")
        if logger:
            logger.warning("Wet detection failed", extra={"error": str(exc)})
        return False
    finally:
        file_result.ElectronicSignatureFound = original_esign
        file_result.MixedContent = original_mixed


def _detect(
    pdf_path: Path,
    configuration: DetectConfiguration,
    file_result: FileResult,
    *,
    logger: logging.Logger | None = None,
) -> bool:
    if fitz is None or pytesseract is None:
        raise WetDetectionUnavailable("PyMuPDF or pytesseract not available")

    document = fitz.open(pdf_path)  # type: ignore[attr-defined]
    try:
        new_signatures: list[Signature] = []
        matrix = fitz.Matrix(configuration.WetOcrDpi / 72.0, configuration.WetOcrDpi / 72.0)
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = _pixmap_to_image(pixmap)
            ocr_lines = _extract_ocr_lines(image, configuration.WetOcrLanguages)
            candidates = list(
                _build_candidates(
                    ocr_lines,
                    image=image,
                    page_rect=page.rect,
                    pix_width=pixmap.width,
                    pix_height=pixmap.height,
                    scale=configuration.WetOcrDpi / 72.0,
                )
            )
            if not candidates:
                candidates = list(
                    _build_candidates(
                        ocr_lines,
                        image=image,
                        page_rect=page.rect,
                        pix_width=pixmap.width,
                        pix_height=pixmap.height,
                        scale=configuration.WetOcrDpi / 72.0,
                        min_y_ratio=0.2,
                    )
                )
            candidates.extend(_image_candidates(page))
            candidates = _filter_candidates_for_page(candidates)
            accepted = [
                candidate
                for candidate in candidates
                if candidate.Score >= configuration.WetPrecisionThreshold
            ]
            if logger:
                logger.debug(
                    "Wet detection page summary",
                    extra={
                        "pdf": pdf_path.name,
                        "page": page_index + 1,
                        "candidates": len(candidates),
                        "accepted": len(accepted),
                    },
                )
            new_signatures.extend(_to_signatures(accepted, page_index + 1))
        if not new_signatures:
            return False

        filtered_signatures = _dedupe_wet_signatures(new_signatures)
        if not filtered_signatures:
            return False

        file_result.Signatures.extend(filtered_signatures)
        _refresh_metadata(file_result)
        return True
    finally:
        document.close()


def _ensure_dependencies() -> None:
    if fitz is None:
        raise WetDetectionUnavailable("PyMuPDF is required for wet detection (install 'pymupdf').")
    if pytesseract is None or TesseractOutput is None:
        raise WetDetectionUnavailable(
            "pytesseract is required for wet detection and depends on the Tesseract OCR binary."
        )


def _pixmap_to_image(pixmap) -> Image.Image:
    mode = "RGB"
    if pixmap.alpha:
        mode = "RGBA"
    image = Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)
    if mode == "RGBA":
        image = image.convert("RGB")
    return image


def _extract_ocr_lines(image: Image.Image, languages: str) -> list[OcrLine]:
    if pytesseract is None or TesseractOutput is None:
        raise WetDetectionUnavailable("pytesseract unavailable")

    try:
        data = pytesseract.image_to_data(image, lang=languages, output_type=TesseractOutput.DICT)
    except Exception as exc:  # pragma: no cover - passthrough to manual review
        raise WetDetectionUnavailable(f"OCR failed: {exc}") from exc
    total = len(data.get("text", []))
    lines: dict[tuple[int, int, int], OcrLine] = {}
    for idx in range(total):
        text = (data["text"][idx] or "").strip()
        if not text:
            continue
        conf_raw = float(data["conf"][idx])
        if conf_raw <= 0:
            continue
        key = (data["block_num"][idx], data["par_num"][idx], data["line_num"][idx])
        left = int(data["left"][idx])
        top = int(data["top"][idx])
        width = int(data["width"][idx])
        height = int(data["height"][idx])
        right = left + width
        bottom = top + height
        existing = lines.get(key)
        if existing is None:
            lines[key] = OcrLine(
                text=text,
                confidence=conf_raw / 100.0,
                left=left,
                top=top,
                right=right,
                bottom=bottom,
            )
        else:
            existing.text = f"{existing.text} {text}"
            existing.confidence = min(1.0, (existing.confidence + conf_raw / 100.0) / 2.0)
            existing.left = min(existing.left, left)
            existing.top = min(existing.top, top)
            existing.right = max(existing.right, right)
            existing.bottom = max(existing.bottom, bottom)
    return list(lines.values())


@dataclass
class WetCandidate:
    bbox: tuple[float, float, float, float]
    Role: str
    Score: float
    Evidence: list[str]


def _build_candidates(
    lines: Iterable[OcrLine],
    *,
    image: Image.Image,
    page_rect,
    pix_width: int,
    pix_height: int,
    scale: float,
    min_y_ratio: float = 0.4,
) -> Iterable[WetCandidate]:
    for line in lines:
        normalized = line.text.lower()
        if not _has_signature_keyword(normalized):
            continue
        if len(normalized) > 80:
            # Ignore long paragraph-like OCR lines
            continue
        if (line.bottom / pix_height) < min_y_ratio:
            # Ignore lines in the upper section of the page
            continue
        role = _infer_role(normalized)
        stroke_found, stroke_y = _stroke_under_line(image, line)
        bonus = _keyword_bonus(normalized)
        if stroke_found:
            bonus += 0.12
        # Slight positional prior: lines in lower quarter are more likely signatures.
        if (line.bottom / pix_height) > 0.7:
            bonus += 0.05
        confidence = min(1.0, line.confidence + bonus)
        bbox = _expand_bbox(line, page_rect, pix_height, scale, stroke_y=stroke_y)
        yield WetCandidate(
            bbox=bbox,
            Role=role,
            Score=confidence,
            Evidence=[
                f"ocr_line:{line.text.strip()}",
                f"ocr_conf:{confidence:.2f}",
                "wet:true",
                "stroke:yes" if stroke_found else "stroke:no",
            ],
        )


def _has_evidence(candidate: WetCandidate, token: str) -> bool:
    return token in candidate.Evidence


def _is_image_candidate(candidate: WetCandidate) -> bool:
    return _has_evidence(candidate, "image_signature:true")


def _has_stroke(candidate: WetCandidate) -> bool:
    return _has_evidence(candidate, "stroke:yes")


def _filter_candidates_for_page(candidates: Sequence[WetCandidate]) -> list[WetCandidate]:
    if not candidates:
        return []
    has_image = any(_is_image_candidate(candidate) for candidate in candidates)
    if not has_image:
        return list(candidates)
    return [
        candidate
        for candidate in candidates
        if _is_image_candidate(candidate) or _has_stroke(candidate)
    ]


def _infer_role(normalized_text: str) -> str:
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword in normalized_text for keyword in keywords):
            return role
    return "unknown"


def _keyword_bonus(normalized_text: str) -> float:
    bonus = 0.0
    if "signature" in normalized_text:
        bonus += 0.05
    if "date" in normalized_text:
        bonus -= 0.02
    if "by:" in normalized_text:
        bonus += 0.03
    return bonus


def _has_signature_keyword(normalized_text: str) -> bool:
    return any(pattern.search(normalized_text) for pattern in SIGNATURE_PATTERNS)


def _expand_bbox(
    line: OcrLine,
    page_rect,
    pix_height: int,
    scale: float,
    *,
    stroke_y: float | None = None,
) -> tuple[float, float, float, float]:
    x0 = line.left / scale
    x1 = line.right / scale
    y_top = (pix_height - line.top) / scale
    y_bottom = (pix_height - line.bottom) / scale

    pad_x = max(14.0, (x1 - x0) * 0.25)
    left = max(page_rect.x0, x0 - pad_x)
    right = min(page_rect.x1, x1 + pad_x)

    gap = 14.0
    line_height = max(1.0, (line.bottom - line.top) / scale)
    signature_height = max(70.0, line_height * 6.0)
    upper = min(page_rect.y1, y_bottom - gap)
    upper = max(page_rect.y0, upper)
    lower = max(page_rect.y0, upper - signature_height)

    if stroke_y is not None:
        # Anchor to the detected stroke (signature line) beneath the label.
        sy = (pix_height - stroke_y) / scale
        field_lower = min(page_rect.y1, max(page_rect.y0, sy + 2.0))
        field_upper = min(page_rect.y1, y_bottom - gap)
        if field_upper > field_lower + 6.0:
            lower = field_lower
            upper = field_upper
        else:
            upper = min(page_rect.y1, field_lower + signature_height)
            lower = max(page_rect.y0, upper - signature_height)

    return (float(left), float(lower), float(right), float(upper))


def _stroke_under_line(image: Image.Image, line: OcrLine) -> tuple[bool, float | None]:
    """Heuristic: look for a dark horizontal stroke beneath the OCR line."""

    gray = image.convert("L")
    pad_x = 10
    strip_height = 28
    x0 = max(0, line.left - pad_x)
    x1 = min(gray.width, line.right + pad_x)
    y0 = min(gray.height, line.bottom + 2)
    y1 = min(gray.height, y0 + strip_height)
    if x1 <= x0 or y1 <= y0:
        return False, None

    crop = gray.crop((x0, y0, x1, y1))
    width = crop.width or 1
    max_density = 0.0
    best_row = None
    # Simple density scan: percentage of dark pixels per row.
    threshold = 160
    for row in range(crop.height):
        row_pixels = [crop.getpixel((col, row)) for col in range(width)]
        dark = sum(1 for px in row_pixels if px < threshold)
        density = dark / width
        if density > max_density:
            max_density = density
            best_row = row
    if max_density < 0.32 or best_row is None:
        return False, None
    return True, float(y0 + best_row)


def _image_candidates(page) -> list[WetCandidate]:
    """Heuristic: treat small, wide images near signature areas as wet signatures."""

    candidates: list[WetCandidate] = []
    page_width = float(page.rect.width)
    page_height = float(page.rect.height)
    page_area = page_width * page_height
    words = page.get_text("words") or []

    for info in page.get_image_info(xrefs=True) or []:
        rect = info.get("bbox") or info.get("rect")
        if rect is None:
            continue
        if hasattr(rect, "x0"):
            x0, y0, x1, y1 = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
        elif isinstance(rect, tuple | list) and len(rect) == 4:
            x0, y0, x1, y1 = map(float, rect)
        else:
            continue
        width = float(x1 - x0)
        height = float(y1 - y0)
        if width <= 40 or height <= 15:
            # Skip tiny marks/logos
            continue
        aspect = width / height if height else 0.0
        if aspect < 1.6:
            continue
        if (width * height) / page_area > 0.1:
            # Ignore large illustrations/backgrounds
            continue

        role = _infer_role_nearby(rect, words)
        score = 0.9 if role != "unknown" else 0.84

        bbox = (x0, float(page_height - y1), x1, float(page_height - y0))

        evidence = ["image_signature:true"]
        if role != "unknown":
            evidence.append(f"role_hint:{role}")

        candidates.append(
            WetCandidate(
                bbox=bbox,
                Role=role,
                Score=min(1.0, score),
                Evidence=evidence,
            )
        )
    return candidates


def _infer_role_nearby(rect, words) -> str:
    """Best-effort role inference using text near the image rectangle."""

    proximity_y = 48.0
    proximity_x = 140.0
    if hasattr(rect, "x0"):
        rx0, ry0, rx1, ry1 = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
    elif isinstance(rect, tuple | list) and len(rect) == 4:
        rx0, ry0, rx1, ry1 = map(float, rect)
    else:
        return "unknown"

    nearby_tokens: list[str] = []
    for word in words:
        if len(word) < 5:
            continue
        x0, y0, x1, y1, token, *_ = word
        if y1 < ry0 - proximity_y or y0 > ry1 + proximity_y:
            continue
        if x1 < rx0 - proximity_x or x0 > rx1 + proximity_x:
            continue
        nearby_tokens.append(str(token))
    if not nearby_tokens:
        return "unknown"
    normalized = " ".join(nearby_tokens).lower()
    return _infer_role(normalized)


def _needs_wet_enhancement(file_result: FileResult) -> bool:
    """Return True when we should run wet OCR to refine pseudo/unknown signatures."""

    return False


def _to_signatures(
    candidates: Sequence[WetCandidate],
    page_number: int,
) -> list[Signature]:
    signatures: list[Signature] = []
    for candidate in candidates:
        signatures.append(
            Signature(
                Page=page_number,
                FieldName="wet_signature_detected",
                Role=candidate.Role,
                Score=int(round(candidate.Score * 100)),
                Scores={candidate.Role: int(round(candidate.Score * 100))},
                Evidence=candidate.Evidence,
                Hint="WetSignatureOCR",
                RenderType="wet",
                BoundingBox=candidate.bbox,
            )
        )
    return signatures


def _signature_rank(signature: Signature) -> tuple[int, int, int]:
    evidence = set(signature.Evidence or [])
    if "image_signature:true" in evidence:
        source_rank = 3
    elif "stroke:yes" in evidence:
        source_rank = 2
    else:
        source_rank = 1
    return (source_rank, int(signature.Score or 0), int(signature.Page or 0))


def _dedupe_wet_signatures(signatures: Sequence[Signature]) -> list[Signature]:
    best_by_role: dict[str, Signature] = {}
    best_unknown: Signature | None = None
    for signature in signatures:
        role = (signature.Role or "unknown").strip().lower()
        if role == "unknown":
            if best_unknown is None or _signature_rank(signature) > _signature_rank(best_unknown):
                best_unknown = signature
            continue
        existing = best_by_role.get(role)
        if existing is None or _signature_rank(signature) > _signature_rank(existing):
            best_by_role[role] = signature
    if best_by_role:
        return sorted(best_by_role.values(), key=lambda sig: (int(sig.Page or 0), sig.Role or ""))
    return [best_unknown] if best_unknown is not None else []


def _mark_manual_review(file_result: FileResult, reason: str) -> None:
    hints = _split_hints(file_result.Hints)
    hints.add(f"ManualReview:{reason}")
    file_result.Hints = ";".join(sorted(hints)) if hints else file_result.Hints


def _refresh_metadata(file_result: FileResult) -> None:
    file_result.SignatureCount = len(file_result.Signatures)
    signature_pages = sorted({sig.Page for sig in file_result.Signatures if sig.Page})
    file_result.SignaturePages = ",".join(map(str, signature_pages))
    roles = sorted({sig.Role for sig in file_result.Signatures if sig.Role != "unknown"})
    if roles:
        file_result.Roles = ";".join(roles)
    file_result.ElectronicSignatureFound = file_result.SignatureCount > 0
    file_result.MixedContent = file_result.ElectronicSignatureFound and bool(file_result.ScannedPdf)
    hints = _split_hints(file_result.Hints)
    hints |= {sig.Hint for sig in file_result.Signatures if sig.Hint}
    file_result.Hints = ";".join(sorted(hints))


def _split_hints(hints: str | None) -> set[str]:
    if not hints:
        return set()
    return {hint for hint in hints.split(";") if hint}
