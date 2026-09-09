import logging

logging.basicConfig(
    level=logging.DEBUG, # Capture DEBUG level and higher
    format="{levelname:<10}{message}", # Set structure
    style="{", # Allows curly brace formatting
)

logger = logging.getLogger(__name__)
