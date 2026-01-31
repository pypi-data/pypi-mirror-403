import logging
from os import getenv
from rich.logging import RichHandler

LEVEL_NAMES = logging.getLevelNamesMapping()
LOG_LEVEL = LEVEL_NAMES.get(getenv('LOG_LEVEL', 'WARNING').upper())

logging.basicConfig(
    level=logging.INFO,
)

# logging.basicConfig(
#     #level="ERROR",
#     level="INFO",
#     format="%(message)s",
#     datefmt="[%X]",
#     handlers=[RichHandler()],
# )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
