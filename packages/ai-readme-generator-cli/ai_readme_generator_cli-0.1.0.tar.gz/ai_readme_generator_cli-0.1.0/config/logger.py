from logging import Formatter, Logger, StreamHandler

from config.settings import  settings

from typing import TextIO


import logging

logger_settings = settings.logger

# Create a logger
logger: Logger = logging.getLogger(name=settings.app_name)
logger.setLevel(level=logger_settings.level)

# Console handler
console_handler: StreamHandler[TextIO] = logging.StreamHandler()
console_handler.setLevel(level=logger_settings.level)

# Formatter
formatter: Formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
console_handler.setFormatter(fmt=formatter)

# Add the handler to the logger
logger.addHandler(hdlr=console_handler)