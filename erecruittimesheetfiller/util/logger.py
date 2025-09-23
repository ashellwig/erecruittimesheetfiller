# Copyright (C) 2025 Ash Hellwig <ahellwig.dev@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""A logger to be used by other modules contained within the package."""

import logging


class LoggingColors:
    grey = "\x1b[0;37m"
    green = "\x1b[1;32m"
    yellow = "\x1b[1;33m"
    red = "\x1b[1;31m"
    purple = "\x1b[1;35m"
    blue = "\x1b[1;34m"
    light_blue = "\x1b[1;36m"
    reset = "\x1b[0m"
    white_bg = "\x1b[5m\x1b[1;31m"


class CustomFormatter(logging.Formatter):
    """Logging Formatter to add colors and count warning / errors"""

    def __init__(self, auto_colorized=True, color_output=True):
        super(CustomFormatter, self).__init__()
        self.auto_colorized = auto_colorized
        self.color_output = color_output
        self.formats = self.define_format()

    def define_format(self):
        # Levels
        # CRITICAL = 50
        # FATAL = CRITICAL
        # ERROR = 40
        # WARNING = 30
        # WARN = WARNING
        # INFO = 20
        # DEBUG = 10
        # NOTSET = 0

        if self.auto_colorized and self.color_output:
            format_prefix = f"{LoggingColors.purple}%(asctime)s" \
                            f"{LoggingColors.reset} " \
                            f"{LoggingColors.blue}%(name)s" \
                            f"{LoggingColors.reset} " \
                            f"{LoggingColors.light_blue}" \
                            "(%(filename)s:%(lineno)d)" \
                            f"{LoggingColors.reset} "

            format_suffix = "%(levelname)s - %(message)s"

            return {
                    logging.DEBUG:
                            format_prefix + LoggingColors.green + format_suffix
                            + LoggingColors.reset,
                    logging.INFO:
                            format_prefix + LoggingColors.grey + format_suffix
                            + LoggingColors.reset,
                    logging.WARNING:
                            format_prefix + LoggingColors.yellow + format_suffix
                            + LoggingColors.reset,
                    logging.ERROR:
                            format_prefix + LoggingColors.red + format_suffix
                            + LoggingColors.reset,
                    logging.CRITICAL:
                            format_prefix + LoggingColors.white_bg
                            + LoggingColors.red + format_suffix
                            + LoggingColors.reset
            }
        else:
            format_prefix = "%(asctime)s %(name)s (%(filename)s:%(lineno)d) "

            format_suffix = "%(levelname)s - %(message)s"

            return {
                    logging.DEBUG: format_prefix + format_suffix,
                    logging.INFO: format_prefix + format_suffix,
                    logging.WARNING: format_prefix + format_suffix,
                    logging.ERROR: format_prefix + format_suffix,
                    logging.CRITICAL: format_prefix + format_suffix,
            }

    def format(self, record):
        log_fmt = self.formats.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(log_file: str | None):
    """Configures the logger.

    Args:
        log_file (str, optional): Log file path. Defaults to "jobappfiller.log".

    Returns:
        Logger: Logger instance for the current module.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    if log_file is not None:
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Formatter
    formatter_console = CustomFormatter()
    if log_file is not None:
        formatter_file = CustomFormatter(
                auto_colorized=False,
                color_output=False
        )
        file_handler.setFormatter(formatter_file)
    console_handler.setFormatter(formatter_console)

    # Add handlers
    if log_file is not None:
        logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
