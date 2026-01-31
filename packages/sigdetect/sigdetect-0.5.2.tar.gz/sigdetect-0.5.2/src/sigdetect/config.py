"""Configuration loading utilities for the signature detection service."""

from __future__ import annotations

import os
from contextlib import suppress
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

EngineName = Literal["pypdf2", "pypdf", "pymupdf", "auto"]
ProfileName = Literal["hipaa", "retainer"]


class DetectConfiguration(BaseModel):
    """Runtime settings governing signature detection.

    The fields use PascalCase to comply with the CaseWorks standards while aliases keep
    compatibility with the existing YAML configuration keys and environment variables.
    """

    model_config = ConfigDict(populate_by_name=True, frozen=True)

    PdfRoot: Path = Field(default=Path("hipaa_results"), alias="pdf_root")
    OutputDirectory: Path | None = Field(default=Path("out"), alias="out_dir")
    WriteResults: bool = Field(default=False, alias="write_results")
    Engine: EngineName = Field(default="auto", alias="engine")
    Profile: ProfileName = Field(default="hipaa", alias="profile")
    PseudoSignatures: bool = Field(default=True, alias="pseudo_signatures")
    RecurseXObjects: bool = Field(default=True, alias="recurse_xobjects")
    CropSignatures: bool = Field(default=True, alias="crop_signatures")
    CropDocx: bool = Field(default=False, alias="crop_docx")
    CropOutputDirectory: Path | None = Field(default=None, alias="crop_output_dir")
    CropImageDpi: int = Field(default=200, alias="crop_image_dpi", ge=72, le=600)
    DetectWetSignatures: bool = Field(default=True, alias="detect_wet_signatures")
    WetOcrDpi: int = Field(default=200, alias="wet_ocr_dpi", ge=72, le=600)
    WetOcrLanguages: str = Field(default="eng", alias="wet_ocr_languages")
    WetPrecisionThreshold: float = Field(
        default=0.82, alias="wet_precision_threshold", ge=0.0, le=1.0
    )

    @field_validator("PdfRoot", "OutputDirectory", "CropOutputDirectory", mode="before")
    @classmethod
    def _CoercePath(cls, value: str | Path | None) -> Path | None:
        """Allow configuration values to be provided as ``str`` or ``Path``.

        :param value: The candidate value from YAML or environment variables.
        :returns: ``Path`` instances (or ``None`` for optional directories).
        """

        if value is None:
            return None
        if isinstance(value, Path):
            return value.expanduser()
        return Path(value).expanduser()

    # Expose legacy snake_case property names for gradual migration
    @property
    def pdf_root(self) -> Path:  # pragma: no cover - simple passthrough
        return self.PdfRoot

    @property
    def out_dir(self) -> Path | None:  # pragma: no cover - simple passthrough
        return self.OutputDirectory

    @property
    def write_results(self) -> bool:  # pragma: no cover - simple passthrough
        return self.WriteResults

    @property
    def engine(self) -> EngineName:  # pragma: no cover - simple passthrough
        return self.Engine

    @property
    def profile(self) -> ProfileName:  # pragma: no cover - simple passthrough
        return self.Profile

    @property
    def pseudo_signatures(self) -> bool:  # pragma: no cover - simple passthrough
        return self.PseudoSignatures

    @property
    def recurse_xobjects(self) -> bool:  # pragma: no cover - simple passthrough
        return self.RecurseXObjects

    @property
    def crop_signatures(self) -> bool:  # pragma: no cover - simple passthrough
        return self.CropSignatures

    @property
    def crop_docx(self) -> bool:  # pragma: no cover - simple passthrough
        return self.CropDocx

    @property
    def crop_output_dir(self) -> Path | None:  # pragma: no cover - simple passthrough
        return self.CropOutputDirectory

    @property
    def crop_image_dpi(self) -> int:  # pragma: no cover - simple passthrough
        return self.CropImageDpi

    @property
    def detect_wet_signatures(self) -> bool:  # pragma: no cover - simple passthrough
        return self.DetectWetSignatures

    @property
    def wet_ocr_dpi(self) -> int:  # pragma: no cover - simple passthrough
        return self.WetOcrDpi

    @property
    def wet_ocr_languages(self) -> str:  # pragma: no cover - simple passthrough
        return self.WetOcrLanguages

    @property
    def wet_precision_threshold(self) -> float:  # pragma: no cover - simple passthrough
        return self.WetPrecisionThreshold


def LoadConfiguration(path: Path | None) -> DetectConfiguration:
    """Load configuration from ``path`` while applying environment overrides.

    Environment variables provide the final say and follow the existing naming:

    ``SIGDETECT_ENGINE``
        Override the PDF parsing engine.
    ``SIGDETECT_PDF_ROOT``
        Directory that will be scanned for PDF files.
    ``SIGDETECT_OUT_DIR``
        Output directory for generated artefacts. Use ``"none"`` to disable writes.
    ``SIGDETECT_PROFILE``
        Runtime profile that controls which heuristics are applied.
    """

    env_engine = os.getenv("SIGDETECT_ENGINE")
    env_pdf_root = os.getenv("SIGDETECT_PDF_ROOT")
    env_out_dir = os.getenv("SIGDETECT_OUT_DIR")
    env_profile = os.getenv("SIGDETECT_PROFILE")
    env_crop = os.getenv("SIGDETECT_CROP_SIGNATURES")
    env_crop_docx = os.getenv("SIGDETECT_CROP_DOCX")
    env_crop_dir = os.getenv("SIGDETECT_CROP_DIR")
    env_crop_dpi = os.getenv("SIGDETECT_CROP_DPI")
    env_detect_wet = os.getenv("SIGDETECT_DETECT_WET")
    env_wet_dpi = os.getenv("SIGDETECT_WET_OCR_DPI")
    env_wet_lang = os.getenv("SIGDETECT_WET_LANGUAGES")
    env_wet_precision = os.getenv("SIGDETECT_WET_PRECISION")

    raw_data: dict[str, object] = {}
    if path and Path(path).exists():
        with open(path, encoding="utf-8") as handle:
            raw_data = yaml.safe_load(handle) or {}

    if env_engine:
        raw_data["engine"] = env_engine
    if env_pdf_root:
        raw_data["pdf_root"] = env_pdf_root
    if env_out_dir:
        raw_data["out_dir"] = None if env_out_dir.lower() == "none" else env_out_dir
    if env_profile in {"hipaa", "retainer"}:
        raw_data["profile"] = env_profile
    if env_crop is not None:
        lowered = env_crop.lower()
        if lowered in {"1", "true", "yes", "on"}:
            raw_data["crop_signatures"] = True
        elif lowered in {"0", "false", "no", "off"}:
            raw_data["crop_signatures"] = False
    if env_crop_docx is not None:
        lowered = env_crop_docx.lower()
        if lowered in {"1", "true", "yes", "on"}:
            raw_data["crop_docx"] = True
        elif lowered in {"0", "false", "no", "off"}:
            raw_data["crop_docx"] = False
    if env_crop_dir:
        raw_data["crop_output_dir"] = env_crop_dir
    if env_crop_dpi:
        with suppress(ValueError):
            raw_data["crop_image_dpi"] = int(env_crop_dpi)
    if env_detect_wet is not None:
        lowered = env_detect_wet.lower()
        if lowered in {"1", "true", "yes", "on"}:
            raw_data["detect_wet_signatures"] = True
        elif lowered in {"0", "false", "no", "off"}:
            raw_data["detect_wet_signatures"] = False
    if env_wet_dpi:
        with suppress(ValueError):
            raw_data["wet_ocr_dpi"] = int(env_wet_dpi)
    if env_wet_lang:
        raw_data["wet_ocr_languages"] = env_wet_lang
    if env_wet_precision:
        with suppress(ValueError):
            raw_data["wet_precision_threshold"] = float(env_wet_precision)

    configuration = DetectConfiguration(**raw_data)
    return FinalizeConfiguration(configuration)


def FinalizeConfiguration(configuration: DetectConfiguration) -> DetectConfiguration:
    """Ensure derived directories exist and defaults are populated."""

    updates: dict[str, object] = {}

    if configuration.OutputDirectory is not None:
        configuration.OutputDirectory.mkdir(parents=True, exist_ok=True)

    if configuration.CropSignatures:
        crop_dir = configuration.CropOutputDirectory
        if crop_dir is None:
            base_dir = configuration.OutputDirectory or configuration.PdfRoot
            crop_dir = base_dir / "signature_crops"
        crop_dir.mkdir(parents=True, exist_ok=True)
        updates["CropOutputDirectory"] = crop_dir

    return configuration if not updates else configuration.model_copy(update=updates)
