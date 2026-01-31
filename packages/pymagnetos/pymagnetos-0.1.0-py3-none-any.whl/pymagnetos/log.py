"""Logging utilities."""

import logging
import sys
import warnings
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import TracebackType
from typing import Literal

from rich.logging import RichHandler

__all__ = ["configure_logger"]

# Setup logging directory
APP_DIR = Path.home() / ".pymagnetos"
APP_DIR.mkdir(parents=True, exist_ok=True)

APP_NAME = "pymagnetos"
LOGGING_FORMAT = "{asctime}.{msecs:3g} [{levelname}] : {message}"
CONSOLE_HANDLER = RichHandler(log_time_format="%H:%m:%S.%f")
FILE_FORMATTER = logging.Formatter(
    LOGGING_FORMAT, style="{", datefmt="%Y-%m-%d %H:%M:%S"
)


def configure_logger(
    logger: logging.Logger, filename: str, log_level: str = "INFO"
) -> None:
    """
    Configure logger handlers.

    Parameters
    ----------
    filename : str
        Name of the file in which log will be written to. The file will be created under
        $HOME/.pymagnetos/.
    log_level : str, optional
        Logging level to choose from ("DEBUG", "INFO", "WARNING", "ERROR"). Default is
        "INFO".
    """
    # Define the file handler
    log_file = APP_DIR / filename
    file_handler = RotatingFileHandler(
        log_file, mode="a", encoding="utf-8", maxBytes=int(1e6), backupCount=1
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(FILE_FORMATTER)

    # Add handlers and set log levels
    remove_file_handlers(logger, log_file, mode="same")
    CONSOLE_HANDLER.setLevel(log_level)
    logger.addHandler(CONSOLE_HANDLER)
    logger.addHandler(file_handler)
    logger.setLevel(log_level)

    # Get the core logger and add the same handlers
    core_logger = logging.getLogger(APP_NAME + ".core")
    remove_file_handlers(core_logger, str(log_file), mode="all")
    core_logger.addHandler(CONSOLE_HANDLER)
    core_logger.addHandler(file_handler)
    core_logger.setLevel(log_level)

    # Set the logger to log exceptions
    log_uncaugth_exceptions(logger)

    logger.info(f"Logging to {log_file}")


def remove_file_handlers(
    logger: logging.Logger,
    file: str | Path,
    mode: Literal["same", "all"] = "same",
    warn: bool = True,
) -> None:
    """
    Remove file handlers from a logger.

    In mode "same", only handlers that log to the same file will be removed, in mode
    "all", all file handlers are removed.

    Parameters
    ----------
    logger : logging.Logger
        Logger instance.
    file : str or Path
        Path to the log file.
    mode : {"same", "all"}, optional
        "same" : remove the handler only if it logs to the same file (default).
        "all": remove all file handlers.
    warn : bool, optional
        Issue a warning when removing a handler set to a different file. Default is
        True.
    """
    file = str(file)
    for idx in range(len(logger.handlers)):
        handler = logger.handlers[idx]
        if isinstance(handler, logging.FileHandler):
            if handler.baseFilename == file:
                logger.removeHandler(handler)
            else:
                if mode == "all":
                    if warn:
                        warnings.warn(
                            f"The logger was writing to {handler.baseFilename}, "
                            "it will stop"
                        )
                    logger.removeHandler(handler)


def log_uncaugth_exceptions(logger: logging.Logger) -> None:
    """Make uncaugth exceptions to be logged by the logger."""

    def handle_exception(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        if not issubclass(exc_type, KeyboardInterrupt):
            logger.critical(
                "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
            )

        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception
