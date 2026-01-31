from pathlib import Path

from pypdf import PdfWriter

from sigdetect.api import DetectMany, DetectPdf, ScanDirectory, detector_context, get_detector


def _write_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(100, 100)
    with open(path, "wb") as handle:
        writer.write(handle)


def test_get_detector_reuses_instance(tmp_path: Path) -> None:
    pdf_one = tmp_path / "one.pdf"
    pdf_two = tmp_path / "two.pdf"
    _write_blank_pdf(pdf_one)
    _write_blank_pdf(pdf_two)

    detector = get_detector(pdfRoot=tmp_path)
    results = list(DetectMany([pdf_one, pdf_two], detector=detector))

    assert len(results) == 2
    assert {row["file"] for row in results} == {"one.pdf", "two.pdf"}


def test_scan_directory_accepts_detector(tmp_path: Path) -> None:
    target_dir = tmp_path / "docs"
    target_dir.mkdir()
    nested = target_dir / "nested"
    nested.mkdir()
    pdf_path = nested / "sample.pdf"
    _write_blank_pdf(pdf_path)

    with detector_context(pdfRoot=target_dir) as detector:
        results = list(ScanDirectory(target_dir, detector=detector))

    assert len(results) == 1
    assert results[0]["file"] == "sample.pdf"


def test_scan_directory_nested_integration(tmp_path: Path) -> None:
    root = tmp_path / "batch"
    (root / "levelA").mkdir(parents=True)
    (root / "levelB" / "deeper").mkdir(parents=True)

    targets = [
        root / "top.pdf",
        root / "levelA" / "first.pdf",
        root / "levelB" / "deeper" / "second.PDF",
    ]
    for pdf in targets:
        _write_blank_pdf(pdf)

    with detector_context(pdfRoot=root) as detector:
        results = list(ScanDirectory(root, detector=detector))

    assert len(results) == len(targets)
    assert {item["file"] for item in results} == {pdf.name for pdf in targets}


def test_detect_pdf_runs_wet_detection_by_default(tmp_path: Path, monkeypatch) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _write_blank_pdf(pdf_path)

    calls: list[tuple[Path, object, object]] = []

    def fake_apply(pdf, config, file_result, logger=None):
        calls.append((Path(pdf), config, file_result))
        return True

    monkeypatch.setattr("sigdetect.api.apply_wet_detection", fake_apply)

    DetectPdf(pdf_path, engineName="pypdf2")

    assert calls
    assert calls[0][0] == pdf_path


def test_detect_pdf_allows_disabling_wet_detection(tmp_path: Path, monkeypatch) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _write_blank_pdf(pdf_path)

    calls: list[tuple[Path, object, object]] = []

    def fake_apply(pdf, config, file_result, logger=None):
        calls.append((Path(pdf), config, file_result))
        return True

    monkeypatch.setattr("sigdetect.api.apply_wet_detection", fake_apply)

    DetectPdf(pdf_path, engineName="pypdf2", runWetDetection=False)

    assert not calls
