from pathlib import Path

from PIL import Image

from pypdf import PdfWriter

from sigdetect.config import DetectConfiguration
from sigdetect.detector.file_result_model import FileResult
from sigdetect.detector.signature_model import Signature
from sigdetect.wet_detection import (
    OcrLine,
    WetCandidate,
    _dedupe_wet_signatures,
    _filter_candidates_for_page,
    _image_candidates,
    _build_candidates,
    _refresh_metadata,
    apply_wet_detection,
    should_run_wet_pipeline,
)


def _blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(200, 200)
    with open(path, "wb") as handle:
        writer.write(handle)


def _empty_file_result(filename: str) -> FileResult:
    return FileResult(
        File=filename,
        SizeKilobytes=None,
        PageCount=0,
        ElectronicSignatureFound=False,
        ScannedPdf=True,
        MixedContent=False,
        SignatureCount=0,
        SignaturePages="",
        Roles="unknown",
        Hints="",
        Signatures=[],
    )


def test_should_run_wet_pipeline_flagged_when_no_esignatures() -> None:
    result = _empty_file_result("doc.pdf")
    assert should_run_wet_pipeline(result) is True

    result.ElectronicSignatureFound = True
    result.SignatureCount = 1
    assert should_run_wet_pipeline(result) is False


def test_apply_wet_detection_marks_manual_review_when_unavailable(
    monkeypatch, tmp_path: Path
) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _blank_pdf(pdf_path)
    configuration = DetectConfiguration(
        pdf_root=tmp_path,
        out_dir=tmp_path,
        engine="pypdf2",
        detect_wet_signatures=True,
    )
    file_result = _empty_file_result("doc.pdf")

    # Force dependency check to fail without requiring actual Tesseract install.
    monkeypatch.setattr("sigdetect.wet_detection.fitz", None)
    applied = apply_wet_detection(pdf_path, configuration, file_result)

    assert applied is False
    assert "ManualReview" in file_result.Hints


def test_apply_wet_detection_skips_when_esign_found(tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _blank_pdf(pdf_path)
    configuration = DetectConfiguration(
        pdf_root=tmp_path,
        out_dir=tmp_path,
        engine="pypdf2",
        detect_wet_signatures=False,
    )
    file_result = _empty_file_result("doc.pdf")
    file_result.ElectronicSignatureFound = True
    file_result.SignatureCount = 1

    applied = apply_wet_detection(pdf_path, configuration, file_result)

    assert applied is False
    assert file_result.Signatures == []
    assert "ManualReview" not in file_result.Hints


def test_apply_wet_detection_preserves_esign_flags(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _blank_pdf(pdf_path)
    configuration = DetectConfiguration(
        pdf_root=tmp_path,
        out_dir=tmp_path,
        engine="pypdf2",
        detect_wet_signatures=False,
    )
    file_result = _empty_file_result("doc.pdf")
    file_result.ElectronicSignatureFound = False
    file_result.MixedContent = False

    monkeypatch.setattr("sigdetect.wet_detection._ensure_dependencies", lambda: None)

    def fake_detect(pdf_path, configuration, file_result, logger=None):
        file_result.Signatures.append(
            Signature(
                Page=1,
                FieldName="wet_signature_detected",
                Role="client",
                Score=88,
                Scores={"client": 88},
                Evidence=["wet:true"],
                Hint="WetSignatureOCR",
                RenderType="wet",
                BoundingBox=(10.0, 10.0, 100.0, 40.0),
            )
        )
        _refresh_metadata(file_result)
        return True

    monkeypatch.setattr("sigdetect.wet_detection._detect", fake_detect)

    applied = apply_wet_detection(pdf_path, configuration, file_result)

    assert applied is True
    assert file_result.ElectronicSignatureFound is False
    assert file_result.MixedContent is False


def test_apply_wet_detection_defaults_unknown_to_patient(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "doc.pdf"
    _blank_pdf(pdf_path)
    configuration = DetectConfiguration(
        pdf_root=tmp_path,
        out_dir=tmp_path,
        engine="pypdf2",
        profile="hipaa",
    )
    file_result = _empty_file_result("doc.pdf")

    monkeypatch.setattr("sigdetect.wet_detection._ensure_dependencies", lambda: None)

    def fake_detect(pdf_path, configuration, file_result, logger=None):
        file_result.Signatures.append(
            Signature(
                Page=1,
                FieldName="wet_signature_detected",
                Role="unknown",
                Score=88,
                Scores={"unknown": 88},
                Evidence=["wet:true"],
                Hint="WetSignatureOCR",
                RenderType="wet",
                BoundingBox=(10.0, 10.0, 100.0, 40.0),
            )
        )
        _refresh_metadata(file_result)
        return True

    monkeypatch.setattr("sigdetect.wet_detection._detect", fake_detect)

    applied = apply_wet_detection(pdf_path, configuration, file_result)

    assert applied is True
    assert file_result.Signatures
    assert file_result.Signatures[0].Role == "patient"
    assert "role_default:patient" in (file_result.Signatures[0].Evidence or [])


def test_image_candidate_detection_infers_role_from_nearby_text() -> None:
    class Rect:
        def __init__(self, x0, y0, x1, y1):
            self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1
            self.width = x1 - x0
            self.height = y1 - y0

    class DummyPage:
        def __init__(self):
            self.rect = Rect(0, 0, 612, 792)

        def get_image_info(self, xrefs=True):
            return [{"bbox": Rect(360.0, 600.0, 440.0, 640.0)}]

        def get_text(self, mode):
            assert mode == "words"
            # Token near the image with client keyword to drive role inference
            return [
                (350.0, 595.0, 420.0, 605.0, "Client", 0, 0, 0, 0),
                (100.0, 100.0, 150.0, 110.0, "Unrelated", 0, 0, 0, 0),
            ]

    candidates = _image_candidates(DummyPage())

    assert candidates, "Expected image-based wet signature candidate"
    candidate = candidates[0]
    assert candidate.Role == "client"
    assert candidate.Score >= 0.84
    assert "image_signature:true" in candidate.Evidence


def test_filter_candidates_prefers_image_and_stroke_when_present() -> None:
    label_candidate = WetCandidate(
        bbox=(0.0, 0.0, 10.0, 10.0),
        Role="patient",
        Score=0.95,
        Evidence=["ocr_line:signature of patient", "stroke:no"],
    )
    stroke_candidate = WetCandidate(
        bbox=(0.0, 0.0, 10.0, 10.0),
        Role="patient",
        Score=0.9,
        Evidence=["ocr_line:signature of patient", "stroke:yes"],
    )
    image_candidate = WetCandidate(
        bbox=(0.0, 0.0, 10.0, 10.0),
        Role="patient",
        Score=0.85,
        Evidence=["image_signature:true"],
    )

    filtered = _filter_candidates_for_page([label_candidate, stroke_candidate, image_candidate])

    assert label_candidate not in filtered
    assert stroke_candidate in filtered
    assert image_candidate in filtered


def test_dedupe_wet_signatures_keeps_best_per_role() -> None:
    def make_signature(page: int, role: str, score: int, evidence: list[str]) -> Signature:
        return Signature(
            Page=page,
            FieldName="wet_signature_detected",
            Role=role,
            Score=score,
            Scores={role: score},
            Evidence=evidence,
            Hint="WetSignatureOCR",
            RenderType="wet",
            BoundingBox=(0.0, 0.0, 10.0, 10.0),
        )

    label = make_signature(1, "patient", 100, ["ocr_line:signature of patient", "stroke:no"])
    image_page1 = make_signature(1, "patient", 90, ["image_signature:true"])
    image_page2 = make_signature(2, "patient", 90, ["image_signature:true"])
    unknown = make_signature(1, "unknown", 99, ["image_signature:true"])

    filtered = _dedupe_wet_signatures([label, image_page1, image_page2, unknown])

    assert len(filtered) == 1
    assert filtered[0].Role == "patient"
    assert filtered[0].Page == 2
    assert "image_signature:true" in filtered[0].Evidence


def test_dedupe_wet_signatures_keeps_unknown_when_only() -> None:
    def make_signature(page: int, role: str, score: int, evidence: list[str]) -> Signature:
        return Signature(
            Page=page,
            FieldName="wet_signature_detected",
            Role=role,
            Score=score,
            Scores={role: score},
            Evidence=evidence,
            Hint="WetSignatureOCR",
            RenderType="wet",
            BoundingBox=(0.0, 0.0, 10.0, 10.0),
        )

    unknown = make_signature(1, "unknown", 90, ["ocr_line:signature", "stroke:no"])
    filtered = _dedupe_wet_signatures([unknown])

    assert len(filtered) == 1
    assert filtered[0].Role == "unknown"


def test_build_candidates_respects_min_y_ratio() -> None:
    class DummyPageRect:
        x0, y0, x1, y1 = 0.0, 0.0, 600.0, 800.0

    image = Image.new("RGB", (100, 100), "white")
    line = OcrLine(text="Signature", confidence=0.9, left=10, top=10, right=90, bottom=30)

    candidates_default = list(
        _build_candidates(
            [line],
            image=image,
            page_rect=DummyPageRect(),
            pix_width=100,
            pix_height=100,
            scale=1.0,
        )
    )
    candidates_relaxed = list(
        _build_candidates(
            [line],
            image=image,
            page_rect=DummyPageRect(),
            pix_width=100,
            pix_height=100,
            scale=1.0,
            min_y_ratio=0.2,
        )
    )

    assert not candidates_default
    assert candidates_relaxed
