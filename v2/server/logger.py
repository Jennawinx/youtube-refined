import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="{levelname:<10}{message}",
    style="{",
)

# Global logger, not worth the overhead to inject
logger = logging.getLogger(__name__)
