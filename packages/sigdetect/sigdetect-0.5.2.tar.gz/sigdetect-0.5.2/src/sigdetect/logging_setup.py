"""Logging helpers configured for the CaseWorks standards."""

from __future__ import annotations

import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from rich.logging import RichHandler

_LEVEL_MAP = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET,
}


def _CoerceLevel(levelValue: str | int | None) -> int:
    """Translate the provided logging level into a numeric value."""

    if isinstance(levelValue, int):
        return levelValue
    if isinstance(levelValue, str):
        return _LEVEL_MAP.get(levelValue.upper(), logging.INFO)
    return logging.INFO


class JsonFormatter(logging.Formatter):
    """Minimal JSON formatter with deterministic keys."""

    default_time_format = "%Y-%m-%dT%H:%M:%S"
    default_msec_format = "%s.%03d"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401 (formatter contract)
        payload: dict[str, Any] = {
            "time": self.formatTime(record, self.default_time_format),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName,
        }

        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "process",
                "processName",
                "message",
            }:
                continue
            payload.setdefault(key, value)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def _CreateRichHandler(levelValue: int) -> RichHandler:
    """Instantiate the styled console handler."""

    return RichHandler(
        level=levelValue,
        markup=True,
        rich_tracebacks=True,
        show_time=True,
        show_path=False,
        log_time_format="[%Y-%m-%d %H:%M:%S]",
    )


def _CreateFileHandler(
    logfile: Path, levelValue: int, jsonFormat: bool, maxBytes: int, backupCount: int
) -> RotatingFileHandler:
    """Create a rotating file handler that optionally emits JSON."""

    logfile.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        filename=str(logfile),
        maxBytes=maxBytes,
        backupCount=backupCount,
        encoding="utf-8",
    )
    handler.setLevel(levelValue)
    if jsonFormat:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s:%(lineno)d | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    return handler


def ConfigureLogging(
    levelValue: str | int | None = None,
    *,
    logfile: str | Path | None = None,
    jsonLogs: bool | None = None,
    useRich: bool | None = None,
    maxBytes: int | None = None,
    backupCount: int | None = None,
    loggerName: str = "sigdetect",
) -> logging.Logger:
    """Initialise logging with precedence ``arguments > env vars > defaults``."""

    resolvedLevel = _CoerceLevel(levelValue or os.getenv("SIGDETECT_LOG_LEVEL"))
    resolvedLogfile = (
        Path(os.getenv("SIGDETECT_LOG_FILE"))
        if (logfile is None and os.getenv("SIGDETECT_LOG_FILE"))
        else Path(logfile) if logfile else None
    )
    resolvedJson = (
        jsonLogs
        if jsonLogs is not None
        else os.getenv("SIGDETECT_LOG_JSON", "false").lower() in {"1", "true", "yes"}
    )
    resolvedRich = (
        useRich
        if useRich is not None
        else os.getenv("SIGDETECT_LOG_RICH", "true").lower() in {"1", "true", "yes"}
    )
    resolvedMaxBytes = (
        maxBytes if maxBytes is not None else int(os.getenv("SIGDETECT_LOG_MAX_BYTES", "1048576"))
    )
    resolvedBackups = (
        backupCount if backupCount is not None else int(os.getenv("SIGDETECT_LOG_BACKUPS", "5"))
    )

    logger = logging.getLogger(loggerName)
    if getattr(logger, "_configured", False):
        return logger

    logger.setLevel(resolvedLevel)
    logger.propagate = False

    handlers: list[logging.Handler] = []

    if resolvedRich:
        handlers.append(_CreateRichHandler(resolvedLevel))
    else:
        streamHandler = logging.StreamHandler()
        streamHandler.setLevel(resolvedLevel)
        streamHandler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s:%(lineno)d | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        handlers.append(streamHandler)

    if resolvedLogfile:
        handlers.append(
            _CreateFileHandler(
                resolvedLogfile, resolvedLevel, resolvedJson, resolvedMaxBytes, resolvedBackups
            )
        )

    for handler in handlers:
        logger.addHandler(handler)

    logger._configured = True  # type: ignore[attr-defined]
    logger.debug(
        "Logging initialized",
        extra={
            "level": resolvedLevel,
            "logfile": str(resolvedLogfile) if resolvedLogfile else None,
            "json_logs": resolvedJson,
            "use_rich": resolvedRich,
        },
    )
    return logger


def SetVerbosity(logger: logging.Logger, *, verbose: bool = False, quiet: bool = False) -> None:
    """Adjust the console verbosity for ``logger``."""

    if quiet:
        newLevel = logging.WARNING
    elif verbose:
        newLevel = logging.DEBUG
    else:
        newLevel = logging.INFO

    logger.setLevel(newLevel)
    for handler in logger.handlers:
        handler.setLevel(newLevel)
