"""sigdetect – PDF e-sign detection & role attribution."""

from importlib.metadata import PackageNotFoundError, version

try:
    import warnings

    from pypdf.errors import PdfReadWarning

    warnings.filterwarnings(
        "ignore",
        message=r"Multiple definitions in dictionary.*key /Subtype",
        category=PdfReadWarning,
    )
except Exception:
    # Never fail imports because of warnings setup
    pass

try:
    __version__ = version("sigdetect")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

DEFAULT_ENGINE = "auto"
