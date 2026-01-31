from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

from sigdetect.config import DetectConfiguration
from sigdetect.detector.pymupdf_engine import PyMuPDFDetector

fitz = pytest.importorskip("fitz")  # type: ignore


def _widget_pdf(path: Path) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(400, 400)

    field = DictionaryObject(
        {
            NameObject("/FT"): NameObject("/Sig"),
            NameObject("/T"): TextStringObject("sig_client"),
        }
    )
    field_ref = writer._add_object(field)

    widget = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/Rect"): ArrayObject(
                [NumberObject(10), NumberObject(10), NumberObject(150), NumberObject(40)]
            ),
            NameObject("/Parent"): field_ref,
        }
    )
    widget_ref = writer._add_object(widget)
    field.update({NameObject("/Kids"): ArrayObject([widget_ref])})

    page[NameObject("/Annots")] = ArrayObject([widget_ref])
    acro = DictionaryObject({NameObject("/Fields"): ArrayObject([field_ref])})
    writer._root_object.update({NameObject("/AcroForm"): acro})

    with open(path, "wb") as handle:
        writer.write(handle)


def _text_pdf(path: Path) -> None:
    doc = fitz.open()
    first = doc.new_page()
    first.insert_text((72, 720), "DocuSign Envelope ID 123")
    first.insert_text((72, 360), "Firm Signature")
    first.insert_text((72, 330), "By: Example LLP")

    second = doc.new_page()
    second.insert_text((72, 720), "DocuSign Envelope ID 123")
    second.insert_text((72, 360), "Client Signature")
    second.insert_text((72, 330), "Date: __________")
    doc.save(path)


def test_pymupdf_detector_reads_widget_bbox(tmp_path: Path) -> None:
    pdf_path = tmp_path / "widget.pdf"
    _widget_pdf(pdf_path)

    cfg = DetectConfiguration(pdf_root=tmp_path, out_dir=tmp_path, engine="pymupdf")
    detector = PyMuPDFDetector(cfg)
    result = detector.Detect(pdf_path)

    assert result.Signatures
    assert result.Signatures[0].BoundingBox == (10.0, 10.0, 150.0, 40.0)


def test_pymupdf_detector_infers_pseudo_bbox(tmp_path: Path) -> None:
    pdf_path = tmp_path / "pseudo.pdf"
    _text_pdf(pdf_path)

    cfg = DetectConfiguration(
        pdf_root=tmp_path, out_dir=tmp_path, engine="pymupdf", profile="retainer"
    )
    detector = PyMuPDFDetector(cfg)
    result = detector.Detect(pdf_path)

    assert result.Signatures
    pseudo_with_bbox = [
        sig for sig in result.Signatures if sig.FieldName == "vendor_or_acro_detected"
    ]
    assert pseudo_with_bbox, "expected pseudo signatures"
    assert all(sig.BoundingBox for sig in pseudo_with_bbox)
