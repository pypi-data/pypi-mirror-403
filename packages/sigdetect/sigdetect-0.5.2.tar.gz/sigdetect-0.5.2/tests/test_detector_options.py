from pathlib import Path

import pytest
from pydantic import ValidationError
from pypdf import PdfWriter

from sigdetect.api import DetectPdf
from sigdetect.config import DetectConfiguration
from sigdetect.detector import ENGINE_REGISTRY, BuildDetector, Detector
from sigdetect.detector.pypdf2_engine import PyPDF2Detector


def _write_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(144, 144)
    with open(path, "wb") as handle:
        writer.write(handle)


def test_detector_skips_xobject_recursion_when_disabled(tmp_path, monkeypatch):
    pdf = tmp_path / "doc.pdf"
    _write_blank_pdf(pdf)

    cfg = DetectConfiguration(
        pdf_root=tmp_path,
        out_dir=tmp_path,
        engine="pypdf2",
        recurse_xobjects=False,
    )
    detector = PyPDF2Detector(cfg)

    calls: list[int] = []

    def fake_collect(self, page):  # pragma: no cover - executed when recursion mistakenly enabled
        calls.append(1)
        return set(), ""

    monkeypatch.setattr(PyPDF2Detector, "_CollectXObjectVendorAndText", fake_collect)

    detector.Detect(pdf)

    assert not calls, "_CollectXObjectVendorAndText should not run when recurse_xobjects is False"


def test_detect_pdf_unsupported_engine(tmp_path):
    pdf = tmp_path / "doc.pdf"
    _write_blank_pdf(pdf)

    with pytest.raises(
        ValidationError, match="Input should be 'pypdf2', 'pypdf', 'pymupdf' or 'auto'"
    ):
        DetectPdf(pdf, engineName="unknown_engine")


def test_build_detector_auto_prefers_pymupdf(monkeypatch, tmp_path):
    class DummyDetector(Detector):
        Name = "pymupdf"

        def __init__(self, configuration):
            self.configuration = configuration

        def Detect(self, pdfPath):  # pragma: no cover - not called in this test
            raise NotImplementedError

    monkeypatch.setattr("sigdetect.detector.PyMuPDFDetector", DummyDetector)
    monkeypatch.setitem(ENGINE_REGISTRY, DummyDetector.Name, DummyDetector)

    cfg = DetectConfiguration(pdf_root=tmp_path, out_dir=tmp_path, engine="auto")
    detector = BuildDetector(cfg)

    assert isinstance(detector, DummyDetector)


def test_build_detector_auto_falls_back_without_pymupdf(monkeypatch, tmp_path):
    monkeypatch.setattr("sigdetect.detector.PyMuPDFDetector", None)
    monkeypatch.delitem(ENGINE_REGISTRY, "pymupdf", raising=False)

    cfg = DetectConfiguration(pdf_root=tmp_path, out_dir=tmp_path, engine="auto")
    with pytest.warns(RuntimeWarning, match="Engine 'auto' falling back to 'pypdf2'"):
        detector = BuildDetector(cfg)

    assert isinstance(detector, PyPDF2Detector)
