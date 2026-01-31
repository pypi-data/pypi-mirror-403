import logging
import sys

from github_action_utils import error

from secrets_safe_library import utils

# GitHub Actions error annotation positioning constants
ERROR_MESSAGE_COL = 1  # Starting column position for error annotation
ERROR_MESSAGE_END_COLUMN = 2  # Ending column position for error annotation
ERROR_MESSAGE_LINE = 4  # Starting line number for error annotation
ERROR_MESSAGE_END_LINE = 5  # Ending line number for error annotation


def show_error(error_message: str, logger: logging.Logger) -> None:
    """
    Displays an error message in the logs and prints an error message in the
    GitHub Actions shell.

    Arguments:
        error_message (str): The message to display as an error.
        logger (logging.Logger): Logger object for logging.

    Returns:
        None
    """

    error(
        error_message,
        title="Action Failed",
        col=ERROR_MESSAGE_COL,
        end_column=ERROR_MESSAGE_END_COLUMN,
        line=ERROR_MESSAGE_LINE,
        end_line=ERROR_MESSAGE_END_LINE,
    )
    utils.print_log(logger, error_message, logging.ERROR)
    sys.exit(1)


def create_file(file_name: str, content: str, logger: logging.Logger) -> None:
    """
    Creates a file at the specified path and writes the provided content.

    Arguments:
        file_name (str): Name or path of the file to be created.
        content (str): Text content to write into the file.
        logger (logging.Logger): Logger object for logging
        errors if file creation fails.

    Returns:
        None
    """
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        logger.error("Failed to create file '%s': %s", file_name, exc)
        raise
