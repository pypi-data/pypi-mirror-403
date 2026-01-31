import io
from pathlib import Path

import pytest
from pypdf import PdfWriter
from PIL import Image, ImageDraw
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

from sigdetect.api import CropSignatureImages, DetectPdf
from sigdetect.config import DetectConfiguration
from sigdetect.cropping import SignatureCrop, _trim_signature_image_bytes, crop_signatures
from sigdetect.detector.pypdf2_engine import PyPDF2Detector

pytest.importorskip("fitz")


def _pdf_with_signature(path: Path) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(300, 300)

    field = DictionaryObject()
    field.update({NameObject("/FT"): NameObject("/Sig"), NameObject("/T"): TextStringObject("sig")})
    field_ref = writer._add_object(field)

    widget = DictionaryObject()
    widget.update(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/Rect"): ArrayObject(
                [NumberObject(50), NumberObject(50), NumberObject(200), NumberObject(120)]
            ),
            NameObject("/Parent"): field_ref,
        }
    )
    widget_ref = writer._add_object(widget)
    field.update({NameObject("/Kids"): ArrayObject([widget_ref])})

    page[NameObject("/Annots")] = ArrayObject([widget_ref])
    acro = DictionaryObject()
    acro.update({NameObject("/Fields"): ArrayObject([field_ref])})
    writer._root_object.update({NameObject("/AcroForm"): acro})

    with open(path, "wb") as handle:
        writer.write(handle)


def _build_test_crop_bytes() -> bytes:
    image = Image.new("RGB", (200, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([20, 10, 80, 20], fill="black")
    draw.rectangle([10, 60, 190, 80], fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_trim_signature_image_bytes_prefers_lower_band() -> None:
    original = _build_test_crop_bytes()
    trimmed = _trim_signature_image_bytes(original, pad_px=2)

    original_image = Image.open(io.BytesIO(original))
    trimmed_image = Image.open(io.BytesIO(trimmed))

    assert trimmed_image.height < original_image.height

    gray = trimmed_image.convert("L")
    pixels = gray.load()
    width, height = gray.size
    top_dark = sum(1 for x in range(width) for y in range(min(8, height)) if pixels[x, y] < 240)
    assert top_dark == 0


def test_trim_signature_image_bytes_respects_horizontal_rule() -> None:
    image = Image.new("RGB", (200, 120), "white")
    draw = ImageDraw.Draw(image)
    # Signature scribble above the line.
    draw.line([20, 20, 180, 30], fill="black", width=3)
    draw.line([25, 28, 140, 18], fill="black", width=2)
    # Horizontal rule separating signature from print name.
    draw.line([10, 50, 190, 50], fill="black", width=2)
    # Text-ish block below the line.
    draw.rectangle([20, 70, 120, 85], fill="black")

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    trimmed = _trim_signature_image_bytes(buffer.getvalue(), pad_px=2)

    trimmed_image = Image.open(io.BytesIO(trimmed)).convert("L")
    width, height = trimmed_image.size
    # Ensure we trimmed off the lower text block (should be well above original height).
    assert height < 90


def test_crop_signatures(tmp_path: Path):
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    cfg = DetectConfiguration(pdf_root=tmp_path, out_dir=tmp_path, engine="pypdf2")
    result = PyPDF2Detector(cfg).Detect(pdf_path)

    out_dir = tmp_path / "crops"
    generated = crop_signatures(pdf_path, result, output_dir=out_dir, dpi=120)

    assert generated, "Expected at least one cropped image"
    for sig in result.Signatures:
        if sig.BoundingBox:
            assert sig.CropPath is not None
            crop_path = Path(sig.CropPath)
            assert crop_path.suffix == ".png"
            assert crop_path.exists()
            assert not crop_path.with_suffix(".docx").exists()
            assert sig.CropDocxPath is None


def test_crop_signatures_docx_toggle(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    cfg = DetectConfiguration(pdf_root=tmp_path, out_dir=tmp_path, engine="pypdf2")
    result = PyPDF2Detector(cfg).Detect(pdf_path)

    out_dir = tmp_path / "crops_docx"
    generated = crop_signatures(pdf_path, result, output_dir=out_dir, dpi=120, docx=True)

    assert generated, "Expected at least one cropped docx"
    for sig in result.Signatures:
        if sig.BoundingBox:
            assert sig.CropDocxPath is not None
            crop_path = Path(sig.CropDocxPath)
            assert crop_path.suffix == ".docx"
            assert crop_path.exists()
            assert not crop_path.with_suffix(".png").exists()
            assert sig.CropPath is None


def test_crop_signature_images_accepts_dict(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    result_dict = DetectPdf(pdf_path, engineName="pymupdf")
    out_dir = tmp_path / "dict_crops"
    paths = CropSignatureImages(pdf_path, result_dict, outputDirectory=out_dir)

    assert paths
    assert result_dict["signatures"][0]["crop_path"] is not None
    assert result_dict["signatures"][0]["crop_path"].endswith(".png")
    assert result_dict["signatures"][0]["crop_docx_path"] is None


def test_crop_signature_images_returns_bytes(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    result_dict = DetectPdf(pdf_path, engineName="pymupdf")
    out_dir = tmp_path / "dict_byte_crops"
    crops = CropSignatureImages(
        pdf_path,
        result_dict,
        outputDirectory=out_dir,
        returnBytes=True,
    )

    assert crops
    assert isinstance(crops[0], SignatureCrop)
    assert crops[0].image_bytes
    assert crops[0].docx_bytes is None
    assert result_dict["signatures"][0]["crop_path"] is not None
    assert result_dict["signatures"][0]["crop_path"].endswith(".png")
    assert result_dict["signatures"][0]["crop_docx_path"] is None


def test_crop_signature_images_returns_bytes_docx(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    result_dict = DetectPdf(pdf_path, engineName="pymupdf")
    out_dir = tmp_path / "dict_docx_crops"
    crops = CropSignatureImages(
        pdf_path,
        result_dict,
        outputDirectory=out_dir,
        returnBytes=True,
        docx=True,
    )

    assert crops
    assert isinstance(crops[0], SignatureCrop)
    assert crops[0].image_bytes
    assert crops[0].docx_bytes
    assert result_dict["signatures"][0]["crop_docx_path"] is not None
    assert result_dict["signatures"][0]["crop_docx_path"].endswith(".docx")
    assert result_dict["signatures"][0]["crop_path"] is None


def test_crop_signature_images_can_skip_disk(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    result_dict = DetectPdf(pdf_path, engineName="pymupdf")
    out_dir = tmp_path / "dict_byte_crops_no_disk"
    crops = CropSignatureImages(
        pdf_path,
        result_dict,
        outputDirectory=out_dir,
        returnBytes=True,
        saveToDisk=False,
    )

    assert crops
    first_crop = crops[0]
    assert isinstance(first_crop, SignatureCrop)
    assert first_crop.image_bytes
    assert first_crop.docx_bytes is None
    assert first_crop.saved_to_disk is False
    assert not first_crop.path.exists()
    assert not first_crop.path.with_suffix(".docx").exists()
    assert result_dict["signatures"][0]["crop_path"] is None
    assert result_dict["signatures"][0]["crop_docx_path"] is None


def test_crop_signature_images_can_skip_disk_docx(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    result_dict = DetectPdf(pdf_path, engineName="pymupdf")
    out_dir = tmp_path / "dict_docx_crops_no_disk"
    crops = CropSignatureImages(
        pdf_path,
        result_dict,
        outputDirectory=out_dir,
        returnBytes=True,
        saveToDisk=False,
        docx=True,
    )

    assert crops
    first_crop = crops[0]
    assert isinstance(first_crop, SignatureCrop)
    assert first_crop.image_bytes
    assert first_crop.docx_bytes
    assert first_crop.saved_to_disk is False
    assert not first_crop.path.exists()
    assert first_crop.path.suffix == ".docx"
    assert not first_crop.path.with_suffix(".png").exists()
    assert result_dict["signatures"][0]["crop_path"] is None
    assert result_dict["signatures"][0]["crop_docx_path"] is None


def test_crop_signatures_returns_bytes(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    cfg = DetectConfiguration(pdf_root=tmp_path, out_dir=tmp_path, engine="pypdf2")
    result = PyPDF2Detector(cfg).Detect(pdf_path)

    out_dir = tmp_path / "byte_crops"
    crops = crop_signatures(
        pdf_path,
        result,
        output_dir=out_dir,
        dpi=120,
        return_bytes=True,
    )

    assert crops
    assert isinstance(crops[0], SignatureCrop)
    assert crops[0].path.exists()
    assert crops[0].path.suffix == ".png"
    assert not crops[0].path.with_suffix(".docx").exists()
    assert crops[0].image_bytes
    assert crops[0].docx_bytes is None


def test_crop_signatures_requires_save_or_bytes(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _pdf_with_signature(pdf_path)

    cfg = DetectConfiguration(pdf_root=tmp_path, out_dir=tmp_path, engine="pypdf2")
    result = PyPDF2Detector(cfg).Detect(pdf_path)

    with pytest.raises(ValueError):
        crop_signatures(
            pdf_path,
            result,
            output_dir=tmp_path / "unused",
            dpi=120,
            save_files=False,
            return_bytes=False,
        )
