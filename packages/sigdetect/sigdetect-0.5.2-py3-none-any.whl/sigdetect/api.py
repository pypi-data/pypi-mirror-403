"""Public helpers for programmatic use of the signature detection engine."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterable, Iterator, Literal, overload

from sigdetect.config import DetectConfiguration
from sigdetect.cropping import SignatureCrop
from sigdetect.detector import BuildDetector, Detector, FileResult, Signature
from sigdetect.wet_detection import apply_wet_detection

EngineName = Literal["pypdf2", "pypdf", "pymupdf", "auto"]
ProfileName = Literal["hipaa", "retainer"]


def DetectPdf(
    pdfPath: str | Path,
    *,
    profileName: ProfileName = "hipaa",
    engineName: EngineName = "auto",
    includePseudoSignatures: bool = True,
    recurseXObjects: bool = True,
    runWetDetection: bool = True,
    detector: Detector | None = None,
) -> dict[str, Any]:
    """Detect signature evidence and assign roles for a single PDF.

    Wet detection runs by default for non-e-sign PDFs; pass ``runWetDetection=False`` to skip OCR.
    """

    resolvedPath = Path(pdfPath)
    activeDetector = detector or get_detector(
        pdfRoot=resolvedPath.parent,
        profileName=profileName,
        engineName=engineName,
        includePseudoSignatures=includePseudoSignatures,
        recurseXObjects=recurseXObjects,
        outputDirectory=None,
    )

    result = activeDetector.Detect(resolvedPath)
    if runWetDetection:
        configuration = _ResolveConfiguration(activeDetector)
        if configuration is not None:
            apply_wet_detection(resolvedPath, configuration, result)
    return _ToPlainDictionary(result)


def get_detector(
    *,
    pdfRoot: str | Path | None = None,
    profileName: ProfileName = "hipaa",
    engineName: EngineName = "auto",
    includePseudoSignatures: bool = True,
    recurseXObjects: bool = True,
    outputDirectory: str | Path | None = None,
) -> Detector:
    """Return a reusable detector instance configured with the supplied options.

    Engine selection is forced to ``auto`` (prefers PyMuPDF when available).
    """

    configuration = DetectConfiguration(
        PdfRoot=Path(pdfRoot) if pdfRoot is not None else Path.cwd(),
        OutputDirectory=Path(outputDirectory) if outputDirectory is not None else None,
        Engine=engineName,
        PseudoSignatures=includePseudoSignatures,
        RecurseXObjects=recurseXObjects,
        Profile=profileName,
    )
    return BuildDetector(configuration)


def _ToPlainDictionary(candidate: Any) -> dict[str, Any]:
    """Convert pydantic/dataclass instances to plain dictionaries."""

    if hasattr(candidate, "to_dict"):
        return candidate.to_dict()
    if hasattr(candidate, "model_dump"):
        return candidate.model_dump()  # type: ignore[attr-defined]
    if hasattr(candidate, "dict"):
        return candidate.dict()  # type: ignore[attr-defined]
    try:
        from dataclasses import asdict, is_dataclass

        if is_dataclass(candidate):
            return asdict(candidate)
    except Exception:
        pass
    if isinstance(candidate, dict):
        return {key: _ToPlainValue(candidate[key]) for key in candidate}
    raise TypeError(f"Unsupported result type: {type(candidate)!r}")


def _ToPlainValue(value: Any) -> Any:
    """Best effort conversion for nested structures."""

    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "model_dump") or hasattr(value, "dict"):
        return _ToPlainDictionary(value)
    try:
        from dataclasses import asdict, is_dataclass

        if is_dataclass(value):
            return asdict(value)
    except Exception:
        pass
    if isinstance(value, list):
        return [_ToPlainValue(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_ToPlainValue(item) for item in value)
    if isinstance(value, dict):
        return {key: _ToPlainValue(result) for key, result in value.items()}
    return value


def DetectMany(
    pdfPaths: Iterable[str | Path],
    *,
    runWetDetection: bool = True,
    detector: Detector | None = None,
    **kwargs: Any,
) -> Iterator[dict[str, Any]]:
    """Yield :func:`DetectPdf` results for each path in ``pdfPaths``."""

    if detector is not None:
        for pdfPath in pdfPaths:
            yield _DetectWithDetector(detector, pdfPath, runWetDetection=runWetDetection)
        return

    for pdfPath in pdfPaths:
        yield DetectPdf(pdfPath, runWetDetection=runWetDetection, **kwargs)


def ScanDirectory(
    pdfRoot: str | Path,
    *,
    globPattern: str = "**/*.pdf",
    runWetDetection: bool = True,
    detector: Detector | None = None,
    **kwargs: Any,
) -> Iterator[dict[str, Any]]:
    """Walk ``pdfRoot`` and yield detection output for every matching PDF."""

    rootDirectory = Path(pdfRoot)
    if globPattern == "**/*.pdf":
        iterator = (path for path in rootDirectory.rglob("*") if path.is_file())
    else:
        iterator = (
            rootDirectory.rglob(globPattern.replace("**/", "", 1))
            if globPattern.startswith("**/")
            else rootDirectory.glob(globPattern)
        )

    for pdfPath in iterator:
        if pdfPath.is_file() and pdfPath.suffix.lower() == ".pdf":
            yield DetectPdf(pdfPath, detector=detector, runWetDetection=runWetDetection, **kwargs)


def ToCsvRow(result: dict[str, Any]) -> dict[str, Any]:
    """Return a curated subset of keys suitable for CSV export."""

    return {
        "file": result.get("file"),
        "size_kb": result.get("size_kb"),
        "pages": result.get("pages"),
        "esign_found": result.get("esign_found"),
        "scanned_pdf": result.get("scanned_pdf"),
        "mixed": result.get("mixed"),
        "sig_count": result.get("sig_count"),
        "sig_pages": result.get("sig_pages"),
        "roles": result.get("roles"),
        "hints": result.get("hints"),
    }


def Version() -> str:
    """Expose the installed package version without importing the CLI stack."""

    try:
        from importlib.metadata import version as resolveVersion

        return resolveVersion("sigdetect")
    except Exception:
        return "0.0.0-dev"


def _DetectWithDetector(
    detector: Detector, pdfPath: str | Path, *, runWetDetection: bool
) -> dict[str, Any]:
    """Helper that runs ``detector`` and returns the plain dictionary result."""

    resolvedPath = Path(pdfPath)
    result = detector.Detect(resolvedPath)
    if runWetDetection:
        configuration = _ResolveConfiguration(detector)
        if configuration is not None:
            apply_wet_detection(resolvedPath, configuration, result)
    return _ToPlainDictionary(result)


def _ResolveConfiguration(detector: Detector) -> DetectConfiguration | None:
    configuration = getattr(detector, "Configuration", None)
    if isinstance(configuration, DetectConfiguration):
        return configuration
    return None


@contextmanager
def detector_context(**kwargs: Any) -> Generator[Detector, None, None]:
    """Context manager wrapper around :func:`get_detector`."""

    detector = get_detector(**kwargs)
    try:
        yield detector
    finally:
        pass


@overload
def CropSignatureImages(
    pdfPath: str | Path,
    fileResult: FileResult | dict[str, Any],
    *,
    outputDirectory: str | Path,
    dpi: int = 200,
    returnBytes: Literal[False] = False,
    saveToDisk: bool = True,
    docx: bool = False,
) -> list[Path]: ...


@overload
def CropSignatureImages(
    pdfPath: str | Path,
    fileResult: FileResult | dict[str, Any],
    *,
    outputDirectory: str | Path,
    dpi: int,
    returnBytes: Literal[True],
    saveToDisk: bool,
    docx: bool = False,
) -> list[SignatureCrop]: ...


def CropSignatureImages(
    pdfPath: str | Path,
    fileResult: FileResult | dict[str, Any],
    *,
    outputDirectory: str | Path,
    dpi: int = 200,
    returnBytes: bool = False,
    saveToDisk: bool = True,
    docx: bool = False,
) -> list[Path] | list[SignatureCrop]:
    """Create PNG files containing cropped signature images (or DOCX when enabled).

    Accepts either a :class:`FileResult` instance or the ``dict`` returned by
    :func:`DetectPdf`. Requires the optional ``pymupdf`` dependency.
    Set ``returnBytes=True`` to also receive in-memory PNG bytes for each crop. Set
    ``saveToDisk=False`` to skip writing PNG files while still returning in-memory data.
    When ``docx`` is True, DOCX files are written instead of PNG files. When ``returnBytes`` is
    True and ``docx`` is enabled, the returned :class:`SignatureCrop` objects include
    ``docx_bytes``.
    """

    from sigdetect.cropping import crop_signatures

    file_result_obj, original_dict = _CoerceFileResult(fileResult)
    paths = crop_signatures(
        pdf_path=Path(pdfPath),
        file_result=file_result_obj,
        output_dir=Path(outputDirectory),
        dpi=dpi,
        return_bytes=returnBytes,
        save_files=saveToDisk,
        docx=docx,
    )
    if original_dict is not None:
        original_dict.clear()
        original_dict.update(file_result_obj.to_dict())
    return paths


def _CoerceFileResult(
    candidate: FileResult | dict[str, Any]
) -> tuple[FileResult, dict[str, Any] | None]:
    if isinstance(candidate, FileResult):
        return candidate, None
    if not isinstance(candidate, dict):
        raise TypeError("fileResult must be FileResult or dict")

    signatures: list[Signature] = []
    for entry in candidate.get("signatures") or []:
        bbox = entry.get("bounding_box")
        signatures.append(
            Signature(
                Page=entry.get("page"),
                FieldName=str(entry.get("field_name") or ""),
                Role=str(entry.get("role") or "unknown"),
                Score=int(entry.get("score") or 0),
                Scores=dict(entry.get("scores") or {}),
                Evidence=list(entry.get("evidence") or []),
                Hint=str(entry.get("hint") or ""),
                RenderType=str(entry.get("render_type") or "unknown"),
                BoundingBox=tuple(bbox) if bbox else None,
                CropPath=entry.get("crop_path"),
                CropBytes=entry.get("crop_bytes"),
                CropDocxPath=entry.get("crop_docx_path"),
                CropDocxBytes=entry.get("crop_docx_bytes"),
            )
        )

    file_result = FileResult(
        File=str(candidate.get("file") or ""),
        SizeKilobytes=candidate.get("size_kb"),
        PageCount=int(candidate.get("pages") or 0),
        ElectronicSignatureFound=bool(candidate.get("esign_found")),
        ScannedPdf=candidate.get("scanned_pdf"),
        MixedContent=candidate.get("mixed"),
        SignatureCount=int(candidate.get("sig_count") or len(signatures)),
        SignaturePages=str(candidate.get("sig_pages") or ""),
        Roles=str(candidate.get("roles") or "unknown"),
        Hints=str(candidate.get("hints") or ""),
        Signatures=signatures,
    )
    return file_result, candidate
