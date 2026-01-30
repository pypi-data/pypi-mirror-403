import logging
import os
import sys
import time

from termcolor import colored
from typing_extensions import Union

from fovus.constants.cli_constants import LOGGER_NAME, PATH_TO_LOGS
from fovus.constants.util_constants import UTF8

_fovus_logger = logging.getLogger(LOGGER_NAME)  # pylint: disable=invalid-name


class AnsiColorFormatter(logging.Formatter):
    """A helper class to print colored messages to the console."""

    def format(self, record: logging.LogRecord) -> str:
        log_message = super().format(record)
        color = getattr(record, "color", None)
        if color:
            return colored(log_message, color)
        return log_message


def setup_fovus_logger(is_debug: bool = False, log_path: Union[str, None] = None) -> logging.Logger:
    """
    Set up a root logger for the Fovus CLI with the following handlers.

    1) A default file handler that logs all messages (including exceptions) to a hidden file for debugging purposes.
    2) A progress handler that stream INFO-level (and below) messages to the console stderr.
    3) A result_output handler that stream only CRITICAL-level messages to the console stdout.
    4) If log_path is provided, also print the messages to a file at the provided path.

    The setup of 2) and 3) separates the informative messages from the final result and allows end users to
    easily get the final output without any additional processing.
    """
    global _fovus_logger  # pylint: disable=global-variable-not-assigned,invalid-name

    if _fovus_logger.hasHandlers():
        return _fovus_logger

    # Default to DEBUG level and let the handlers decide the level to record
    _fovus_logger.setLevel(logging.DEBUG)

    # Setup the default file handler to send log to a hidden file for debugging purposes
    hidden_log_file_path = os.path.join(PATH_TO_LOGS, time.strftime("%Y-%m-%d_%H-%M-%S.log"))
    os.makedirs(os.path.dirname(hidden_log_file_path), exist_ok=True)

    file_handler = _create_file_handler(hidden_log_file_path, logging.DEBUG, "%(asctime)s %(levelname)s %(message)s")
    _fovus_logger.addHandler(file_handler)

    # Setup a handler for progress messages.
    progress_handler = _create_progress_handler(is_debug)
    _fovus_logger.addHandler(progress_handler)

    # Setup a handler for the final output
    result_output_handler = _create_result_output_handler()
    _fovus_logger.addHandler(result_output_handler)

    if log_path is not None:
        absolute_log_path = os.path.abspath(log_path)
        os.makedirs(os.path.dirname(absolute_log_path), exist_ok=True)
        log_level = logging.DEBUG if is_debug else logging.INFO
        file_handler = _create_file_handler(absolute_log_path, log_level, "%(message)s")
        _fovus_logger.addHandler(file_handler)

    return _fovus_logger


def _create_file_handler(log_path: str, log_level: int, format_string: str) -> logging.FileHandler:
    file_formatter = logging.Formatter(format_string)

    file_handler = logging.FileHandler(log_path, mode="a", encoding=UTF8)
    file_handler.setFormatter(file_formatter)

    file_handler.setLevel(log_level)

    return file_handler


def _create_progress_handler(is_debug: bool = False) -> logging.StreamHandler:
    progress_handler = logging.StreamHandler(sys.stderr)
    progress_handler.setFormatter(AnsiColorFormatter("%(message)s"))
    progress_handler.setLevel(logging.DEBUG if is_debug else logging.INFO)

    # We only want to show regular messages (INFO and below), and hide all error and stack trace messages.
    progress_handler.addFilter(lambda record: record.levelno <= logging.INFO)

    return progress_handler


def _create_result_output_handler() -> logging.StreamHandler:
    result_output_handler = logging.StreamHandler(sys.stdout)
    result_output_handler.setFormatter(AnsiColorFormatter("%(message)s"))
    result_output_handler.setLevel(logging.CRITICAL)

    return result_output_handler


def get_fovus_logger() -> logging.Logger:
    """Return the root logger for the Fovus CLI."""
    global _fovus_logger  # pylint: disable=global-variable-not-assigned,invalid-name

    if _fovus_logger is None:
        raise ValueError("Fovus logger not setup. Please call setup_fovus_logger() first.")

    return _fovus_logger
