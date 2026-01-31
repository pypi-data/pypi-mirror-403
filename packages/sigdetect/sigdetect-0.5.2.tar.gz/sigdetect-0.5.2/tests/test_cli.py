# tests/test_cli.py

import base64
import json
from pathlib import Path
from textwrap import dedent

from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, NumberObject, TextStringObject

# Prefer Typer's test utility, but fall back to Click's if unavailable.
try:
    from typer.testing import CliRunner  # Typer re-exports click.testing.CliRunner
except Exception:  # pragma: no cover - robust to environments lacking typer.testing
    from click.testing import CliRunner

from sigdetect.cli import app
from sigdetect.cropping import SignatureCrop


def _write_blank_pdf(path: Path) -> None:
    writer = PdfWriter()
    writer.add_blank_page(200, 200)
    with open(path, "wb") as handle:
        writer.write(handle)


def _pdf_with_signature(path: Path) -> None:
    writer = PdfWriter()
    page = writer.add_blank_page(200, 200)

    field = DictionaryObject()
    field.update({NameObject("/FT"): NameObject("/Sig"), NameObject("/T"): TextStringObject("sig")})
    field_ref = writer._add_object(field)

    widget = DictionaryObject()
    widget.update(
        {
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/Rect"): ArrayObject(
                [NumberObject(40), NumberObject(40), NumberObject(160), NumberObject(90)]
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


def test_version():
    r = CliRunner().invoke(app, ["version"])
    assert r.exit_code == 0
    assert r.stdout.strip()


def test_detect_respects_out_dir_none(tmp_path: Path):
    pdf_root = tmp_path / "pdfs"
    pdf_root.mkdir()

    sample_pdf = pdf_root / "example.pdf"
    _write_blank_pdf(sample_pdf)

    config_path = tmp_path / "config.yml"
    config_path.write_text(
        dedent(
            f"""
            pdf_root: {pdf_root}
            out_dir: null
            write_results: true
            engine: pypdf2
            profile: hipaa
            pseudo_signatures: true
            recurse_xobjects: true
            """
        ).strip()
    )

    runner = CliRunner()
    result = runner.invoke(app, ["detect", "--config", str(config_path)])

    assert result.exit_code == 0
    assert "Detection completed with output disabled" in result.stdout
    assert not (pdf_root / "results.json").exists()


def test_detect_recurses_by_default(tmp_path: Path):
    pdf_root = tmp_path / "pdfs"
    nested = pdf_root / "nested"
    nested.mkdir(parents=True)

    sample_pdf = nested / "example.PDF"
    _write_blank_pdf(sample_pdf)

    config_path = tmp_path / "config.yml"
    out_dir = tmp_path / "out"
    config_path.write_text(
        dedent(
            f"""
            pdf_root: {pdf_root}
            out_dir: {out_dir}
            write_results: true
            engine: pypdf2
            profile: hipaa
            pseudo_signatures: true
            recurse_xobjects: true
            """
        ).strip()
    )

    runner = CliRunner()
    result = runner.invoke(app, ["detect", "--config", str(config_path)])

    assert result.exit_code == 0
    payload = (out_dir / "results.json").read_text()
    assert "example.PDF" in payload


def test_detect_write_results_disabled_by_default(tmp_path: Path):
    pdf_root = tmp_path / "pdfs"
    pdf_root.mkdir()

    sample_pdf = pdf_root / "example.pdf"
    _write_blank_pdf(sample_pdf)

    config_path = tmp_path / "config.yml"
    out_dir = tmp_path / "out"
    config_path.write_text(
        dedent(
            f"""
            pdf_root: {pdf_root}
            out_dir: {out_dir}
            engine: pypdf2
            profile: hipaa
            pseudo_signatures: true
            recurse_xobjects: true
            crop_signatures: false
            """
        ).strip()
    )

    runner = CliRunner()
    result = runner.invoke(app, ["detect", "--config", str(config_path)])

    assert result.exit_code == 0
    assert not (out_dir / "results.json").exists()


def test_detect_supports_non_recursive_scan(tmp_path: Path):
    pdf_root = tmp_path / "pdfs"
    nested = pdf_root / "nested"
    nested.mkdir(parents=True)

    sample_pdf = nested / "example.pdf"
    _write_blank_pdf(sample_pdf)

    config_path = tmp_path / "config.yml"
    out_dir = tmp_path / "out"
    config_path.write_text(
        dedent(
            f"""
            pdf_root: {pdf_root}
            out_dir: {out_dir}
            engine: pypdf2
            profile: hipaa
            pseudo_signatures: true
            recurse_xobjects: true
            """
        ).strip()
    )

    runner = CliRunner()
    result = runner.invoke(app, ["detect", "--config", str(config_path), "--no-recursive"])

    assert result.exit_code != 0
    combined_output = result.stdout + getattr(result, "stderr", "")
    assert "No PDFs found" in combined_output


def test_detect_unknown_engine_errors(tmp_path: Path):
    pdf_root = tmp_path / "pdfs"
    pdf_root.mkdir()

    sample_pdf = pdf_root / "example.pdf"
    _write_blank_pdf(sample_pdf)

    config_path = tmp_path / "config.yml"
    config_path.write_text(
        dedent(
            f"""
            pdf_root: {pdf_root}
            out_dir: {tmp_path}
            engine: unknown_engine
            profile: hipaa
            pseudo_signatures: true
            recurse_xobjects: true
            """
        ).strip()
    )

    runner = CliRunner()
    result = runner.invoke(app, ["detect", "--config", str(config_path)])

    assert result.exit_code != 0
    assert result.exception is not None
    assert "Input should be 'pypdf2', 'pypdf', 'pymupdf' or 'auto'" in str(result.exception)


def test_detect_crop_bytes_embeds_base64(tmp_path: Path, monkeypatch) -> None:
    pdf_root = tmp_path / "pdfs"
    pdf_root.mkdir()

    sample_pdf = pdf_root / "example.pdf"
    _pdf_with_signature(sample_pdf)

    config_path = tmp_path / "config.yml"
    out_dir = tmp_path / "out"
    config_path.write_text(
        dedent(
            f"""
            pdf_root: {pdf_root}
            out_dir: {out_dir}
            write_results: true
            engine: pypdf2
            profile: hipaa
            pseudo_signatures: true
            recurse_xobjects: true
            crop_signatures: false
            """
        ).strip()
    )

    fake_bytes = b"fakepngbytes"

    def fake_crop_signatures(
        pdf_path,
        file_result,
        *,
        output_dir,
        dpi,
        logger=None,
        return_bytes=False,
        save_files=True,
        docx=False,
    ):
        assert return_bytes is True
        assert save_files is False
        assert docx is False
        return [
            SignatureCrop(
                path=Path(output_dir) / "sig_01.png",
                image_bytes=fake_bytes,
                signature=file_result.Signatures[0],
                saved_to_disk=save_files,
            )
        ]

    monkeypatch.setattr("sigdetect.cli.crop_signatures", fake_crop_signatures)

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["detect", "--config", str(config_path), "--crop-bytes", "--no-crop-signatures"],
    )

    assert result.exit_code == 0
    payload = json.loads((out_dir / "results.json").read_text())
    crop_bytes = payload[0]["signatures"][0]["crop_bytes"]
    assert crop_bytes == base64.b64encode(fake_bytes).decode("ascii")
