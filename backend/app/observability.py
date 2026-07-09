import logging
import os

logger = logging.getLogger("app")


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    # httpx's own per-request INFO logs are redundant with our own
    # event=request logging and just add noise.
    logging.getLogger("httpx").setLevel(logging.WARNING)
