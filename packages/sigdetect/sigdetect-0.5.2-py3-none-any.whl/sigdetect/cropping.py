"""Helpers for converting signature bounding boxes into PNG or DOCX crops."""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, overload

from PIL import Image

from .detector.file_result_model import FileResult
from .detector.signature_model import Signature

try:  # pragma: no cover - optional dependency
    import fitz  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    fitz = None  # type: ignore[misc]

try:  # pragma: no cover - optional dependency
    from docx import Document  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Document = None  # type: ignore[assignment]


class SignatureCroppingUnavailable(RuntimeError):
    """Raised when PNG cropping cannot be performed (e.g., PyMuPDF missing)."""


class SignatureDocxUnavailable(SignatureCroppingUnavailable):
    """Raised when DOCX creation cannot be performed (e.g., python-docx missing)."""


@dataclass(slots=True)
class SignatureCrop:
    """Crop metadata and in-memory content."""

    path: Path
    image_bytes: bytes
    signature: Signature
    docx_bytes: bytes | None = None
    saved_to_disk: bool = True


@overload
def crop_signatures(
    pdf_path: Path,
    file_result: FileResult,
    *,
    output_dir: Path,
    dpi: int = 200,
    logger: logging.Logger | None = None,
    return_bytes: Literal[False] = False,
    save_files: bool = True,
    docx: bool = False,
    trim: bool = True,
) -> list[Path]: ...


@overload
def crop_signatures(
    pdf_path: Path,
    file_result: FileResult,
    *,
    output_dir: Path,
    dpi: int = 200,
    logger: logging.Logger | None = None,
    return_bytes: Literal[True],
    save_files: bool = True,
    docx: bool = False,
    trim: bool = True,
) -> list[SignatureCrop]: ...


def crop_signatures(
    pdf_path: Path,
    file_result: FileResult,
    *,
    output_dir: Path,
    dpi: int = 200,
    logger: logging.Logger | None = None,
    return_bytes: bool = False,
    save_files: bool = True,
    docx: bool = False,
    trim: bool = True,
) -> list[Path] | list[SignatureCrop]:
    """Render each signature bounding box to a PNG image and optionally wrap it in DOCX.

    Set ``return_bytes=True`` to collect in-memory PNG bytes for each crop while also writing
    the files to ``output_dir``. Set ``save_files=False`` to skip writing PNGs to disk.
    When ``docx=True``, DOCX files are written instead of PNGs. When ``return_bytes`` is True
    and ``docx=True``, ``SignatureCrop.docx_bytes`` will contain the DOCX payload.
    When ``trim`` is enabled, the crop is tightened around the detected ink where possible.
    """

    if fitz is None:  # pragma: no cover - exercised when dependency absent
        raise SignatureCroppingUnavailable(
            "PyMuPDF is required for PNG crops. Install 'pymupdf' or add it to your environment."
        )
    if not save_files and not return_bytes:
        raise ValueError("At least one of save_files or return_bytes must be True")

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    if save_files:
        output_dir.mkdir(parents=True, exist_ok=True)
    generated_paths: list[Path] = []
    generated_crops: list[SignatureCrop] = []

    docx_enabled = docx
    docx_available = Document is not None
    if docx_enabled and not docx_available:
        raise SignatureDocxUnavailable(
            "python-docx is required to generate DOCX outputs for signature crops."
        )

    with fitz.open(pdf_path) as document:  # type: ignore[attr-defined]
        per_document_dir = output_dir / pdf_path.stem
        if save_files:
            per_document_dir.mkdir(parents=True, exist_ok=True)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)

        for index, signature in enumerate(file_result.Signatures, start=1):
            if not signature.BoundingBox or not signature.Page:
                continue
            try:
                page = document.load_page(signature.Page - 1)
            except Exception as exc:  # pragma: no cover - defensive
                if logger:
                    logger.warning(
                        "Failed to load page for signature crop",
                        extra={
                            "file": pdf_path.name,
                            "page": signature.Page,
                            "error": str(exc),
                        },
                    )
                continue

            clip = _to_clip_rect(page, signature.BoundingBox)
            if clip is None:
                continue

            filename = _build_filename(index, signature)
            png_destination = per_document_dir / filename
            docx_destination = png_destination.with_suffix(".docx")

            try:
                image_bytes: bytes | None = None
                pixmap = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
                raw_bytes = pixmap.tobytes("png")
                final_bytes = _trim_signature_image_bytes(raw_bytes) if trim else raw_bytes
                if save_files and not docx_enabled:
                    png_destination.write_bytes(final_bytes)
                if return_bytes or docx_enabled:
                    image_bytes = final_bytes
            except Exception as exc:  # pragma: no cover - defensive
                if logger:
                    logger.warning(
                        "Failed to render signature crop",
                        extra={
                            "file": pdf_path.name,
                            "page": signature.Page,
                            "field": signature.FieldName,
                            "error": str(exc),
                        },
                    )
                continue

            docx_bytes: bytes | None = None
            if docx_enabled:
                if image_bytes is None:  # pragma: no cover - defensive
                    continue
                try:
                    docx_bytes = _build_docx_bytes(image_bytes)
                    if save_files:
                        docx_destination.write_bytes(docx_bytes)
                except SignatureDocxUnavailable as exc:
                    if logger:
                        logger.warning(
                            "Signature DOCX output unavailable",
                            extra={"error": str(exc)},
                        )
                    docx_available = False
                except Exception as exc:  # pragma: no cover - defensive
                    if logger:
                        logger.warning(
                            "Failed to write signature DOCX",
                            extra={"file": pdf_path.name, "error": str(exc)},
                        )

            if save_files:
                if docx_enabled:
                    signature.CropPath = None
                    signature.CropDocxPath = str(docx_destination)
                    generated_paths.append(docx_destination)
                else:
                    signature.CropDocxPath = None
                    signature.CropPath = str(png_destination)
                    generated_paths.append(png_destination)
            if return_bytes:
                if image_bytes is None:  # pragma: no cover - defensive
                    continue
                generated_crops.append(
                    SignatureCrop(
                        path=docx_destination if docx_enabled else png_destination,
                        image_bytes=image_bytes,
                        signature=signature,
                        docx_bytes=docx_bytes,
                        saved_to_disk=save_files,
                    )
                )

    return generated_crops if return_bytes else generated_paths


def _build_docx_bytes(image_bytes: bytes) -> bytes:
    if Document is None:
        raise SignatureDocxUnavailable(
            "python-docx is required to generate DOCX outputs for signature crops."
        )
    document = Document()
    document.add_picture(io.BytesIO(image_bytes))
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _trim_signature_image_bytes(
    image_bytes: bytes,
    *,
    pad_px: int = 4,
    gap_px: int = 4,
    min_density_ratio: float = 0.004,
) -> bytes:
    image = Image.open(io.BytesIO(image_bytes))
    gray = image.convert("L")
    width, height = gray.size

    histogram = gray.histogram()
    total_pixels = width * height
    cutoff = int(total_pixels * 0.995)
    cumulative = 0
    white_level = 255
    for idx, count in enumerate(histogram):
        cumulative += count
        if cumulative >= cutoff:
            white_level = idx
            break

    if white_level < 200:
        return image_bytes

    thresholds = [min(254, max(200, white_level - delta)) for delta in (6, 4, 2, 1, 0)]
    min_density = max(2, int(width * min_density_ratio))
    pixels = gray.load()

    row_densities: dict[int, list[int]] = {}
    for threshold in thresholds:
        row_density = []
        for y in range(height):
            dark = sum(1 for x in range(width) if pixels[x, y] < threshold)
            row_density.append(dark)
        row_densities[threshold] = row_density

    line_bounds = _detect_horizontal_rule_cutoff(row_densities[thresholds[-1]], width)
    scan_limit = None
    descender_limit = height - 1
    if line_bounds is not None:
        line_start, line_end = line_bounds
        scan_limit = max(0, line_start - 1)
        descender_limit = min(height - 1, line_end + max(2, int(height * 0.02)))

    min_band_height = max(4, int(height * 0.02))
    best = None
    best_small = None
    best_small_threshold = None
    best_threshold = None
    line_threshold = int(width * 0.6)
    for threshold in thresholds:
        row_density = row_densities[threshold]
        segments: list[tuple[int, int]] = []
        start: int | None = None
        for y, dark in enumerate(row_density):
            if scan_limit is not None and y > scan_limit:
                if start is not None:
                    segments.append((start, y - 1))
                    start = None
                break
            if dark >= min_density:
                if start is None:
                    start = y
            else:
                if start is not None:
                    segments.append((start, y - 1))
                    start = None
        if start is not None:
            segments.append((start, height - 1))

        if not segments:
            continue

        merged: list[list[int]] = []
        for seg in segments:
            if not merged:
                merged.append([seg[0], seg[1]])
                continue
            if seg[0] - merged[-1][1] <= gap_px:
                merged[-1][1] = seg[1]
            else:
                merged.append([seg[0], seg[1]])

        candidates = []
        for y0, y1 in merged:
            min_x, max_x = width, -1
            total_dark = 0
            for y in range(y0, y1 + 1):
                for x in range(width):
                    if pixels[x, y] < threshold:
                        total_dark += 1
                        if x < min_x:
                            min_x = x
                        if x > max_x:
                            max_x = x
            if max_x < 0:
                continue
            band_height = y1 - y0 + 1
            band_width = max_x - min_x + 1
            score = total_dark * (band_height**1.3)
            if line_bounds is not None:
                distance = max(0, line_bounds[0] - y1)
                proximity = 1.0 / (1.0 + (distance / 20.0))
                score *= 1.0 + 0.5 * proximity
            candidates.append(
                {
                    "y0": y0,
                    "y1": y1,
                    "min_x": min_x,
                    "max_x": max_x,
                    "total": total_dark,
                    "height": band_height,
                    "width": band_width,
                    "score": score,
                }
            )

        if not candidates:
            continue

        candidates.sort(key=lambda item: item["score"], reverse=True)
        top_candidate = candidates[0]
        if top_candidate["height"] >= min_band_height:
            if best is None or top_candidate["score"] > best["score"]:
                best = top_candidate
                best_threshold = threshold
        else:
            if best_small is None or top_candidate["score"] > best_small["score"]:
                best_small = top_candidate
                best_small_threshold = threshold

    if best is None:
        best = best_small
        best_threshold = best_small_threshold

    if best is None:
        return image_bytes

    expansion_density = row_densities.get(best_threshold, row_densities[thresholds[-1]])
    expand_threshold = max(1, int(min_density * 0.4))
    y0 = best["y0"]
    y1 = best["y1"]

    while y0 > 0 and expansion_density[y0 - 1] >= expand_threshold:
        y0 -= 1
    while y1 < descender_limit and expansion_density[y1 + 1] >= expand_threshold:
        y1 += 1

    min_x, max_x = width, -1
    for y in range(y0, y1 + 1):
        if expansion_density[y] >= line_threshold:
            continue
        for x in range(width):
            if pixels[x, y] < thresholds[-1]:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
    if max_x >= 0:
        best = {
            "y0": y0,
            "y1": y1,
            "min_x": min_x,
            "max_x": max_x,
        }

    x0 = max(0, best["min_x"] - pad_px)
    x1 = min(width - 1, best["max_x"] + pad_px)
    y0 = max(0, best["y0"] - pad_px)
    y1 = min(height - 1, best["y1"] + pad_px)

    if x1 <= x0 or y1 <= y0:
        return image_bytes
    if (x1 - x0) < max(10, int(width * 0.2)) or (y1 - y0) < max(6, int(height * 0.08)):
        return image_bytes

    cropped = image.crop((x0, y0, x1 + 1, y1 + 1))
    buffer = io.BytesIO()
    cropped.save(buffer, format="PNG")
    return buffer.getvalue()


def _detect_horizontal_rule_cutoff(
    row_density: list[int],
    width: int,
) -> tuple[int, int] | None:
    if not row_density:
        return None
    line_threshold = int(width * 0.6)
    max_thickness = 4
    segments: list[tuple[int, int]] = []
    start = None
    for y, density in enumerate(row_density):
        if density >= line_threshold:
            if start is None:
                start = y
        else:
            if start is not None:
                segments.append((start, y - 1))
                start = None
    if start is not None:
        segments.append((start, len(row_density) - 1))

    if not segments:
        return None

    total_dark = sum(row_density)
    if total_dark <= 0:
        return None

    for y0, y1 in segments:
        thickness = y1 - y0 + 1
        if thickness > max_thickness:
            continue
        above_dark = sum(row_density[:y0])
        below_dark = sum(row_density[y1 + 1 :])
        if above_dark < 40:
            continue
        midpoint_ratio = ((y0 + y1) / 2.0) / max(1, len(row_density))
        if midpoint_ratio >= 0.35:
            return (y0, y1)
        if above_dark >= max(40, int(below_dark * 0.3)):
            return (y0, y1)
    return None


def _to_clip_rect(page, bbox: tuple[float, float, float, float]):
    width = float(page.rect.width)
    height = float(page.rect.height)

    x0, y0, x1, y1 = bbox
    left = _clamp(min(x0, x1), 0.0, width)
    right = _clamp(max(x0, x1), 0.0, width)

    top = _clamp(height - max(y0, y1), 0.0, height)
    bottom = _clamp(height - min(y0, y1), 0.0, height)

    if right - left <= 0 or bottom - top <= 0:
        return None
    return fitz.Rect(left, top, right, bottom)


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def _build_filename(index: int, signature: Signature) -> str:
    base = signature.Role or signature.FieldName or "signature"
    slug = _slugify(base)
    return f"sig_{index:02d}_{slug}.png"


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip().lower())
    cleaned = cleaned.strip("_")
    return cleaned or "signature"
