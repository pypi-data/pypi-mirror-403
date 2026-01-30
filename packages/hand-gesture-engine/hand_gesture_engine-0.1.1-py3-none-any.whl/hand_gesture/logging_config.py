# logging_config.py

import logging
import sys


def setup_logging(
    level=logging.INFO,
    log_to_file=False,
    filename="gesture_engine.log"
):
    """
    Sets up global logging configuration.
    """

    handlers = []

    # Console logging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter(
            "[%(levelname)s] %(name)s :: %(message)s"
        )
    )
    handlers.append(console_handler)

    # Optional file logging
    if log_to_file:
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s :: %(message)s"
            )
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        handlers=handlers
    )
