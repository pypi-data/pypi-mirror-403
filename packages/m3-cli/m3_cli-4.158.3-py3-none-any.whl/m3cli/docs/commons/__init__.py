import logging
import logging.handlers
from m3cli.docs.commons.last_page import add_cli_last_page, add_last_page_to_docx
from m3cli.docs.commons.last_page import (
    add_last_page_to_docx,
    add_cli_last_page,
    get_cli_version,
)
from m3cli.docs.commons.page_numbers import add_page_numbers, PAGE_NUMBER_FORMATS, ALIGNMENT_MAP
from m3cli.docs.commons.page_header import add_page_header

__all__ = [
    'add_last_page_to_docx',
    'add_cli_last_page',
    'get_cli_version',
    'add_page_numbers',
    'PAGE_NUMBER_FORMATS',
    'ALIGNMENT_MAP',
    'add_page_header',
]

# Singleton pattern implementation
_logger_instance = None


def create_logger(level=logging.DEBUG) -> logging.Logger:
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    logger = logging.getLogger('root')
    # Create handlers
    stream_handler = logging.StreamHandler()
    file_handler = logging.handlers.RotatingFileHandler(
        'generate_docs.log',
        maxBytes=1048576,  # 1 MB
        backupCount=30,
    )
    # Create formatter and add it to handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    # Set logger level
    logger.setLevel(level)

    _logger_instance = logger
    return logger
