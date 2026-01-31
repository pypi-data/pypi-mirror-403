"""
Utility functions, including logger config
"""

import logging
import os
import time
from logging import Logger

from totp.config import LOG_DIR, LOG_LEVEL


def get_logger(name: str) -> Logger:
    t = time.localtime()
    os.makedirs(LOG_DIR, exist_ok=True)
    file = os.path.join(LOG_DIR, f"totp_{t.tm_year}{t.tm_mon:02}{t.tm_mday:02}.txt")

    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    logging.basicConfig(
        format="%(levelname)s %(asctime)s %(filename)s:%(lineno)s - %(message)s",
        datefmt="%Y-%m-%d_%H-%M-%S",
        filename=file,
        encoding="utf-8",
    )

    return logger


def check_config_health() -> None:
    logger = get_logger(__name__)
    try:
        from totp.config import (
            CONFIG_DIR,
            HASH_FILE,
            SITES_TABLE,
            LOG_DIR,
            BLANK_DEF,
            NICK_DEF,
            SLIDER_DEF,
            SITE_DEF,
            DEFAULT_FG,
            FANCY_SLIDER,
            ENTRY_SCHEMA,
            STATUSLINE_SCHEMA,
        )

        assert CONFIG_DIR is not None
        assert HASH_FILE is not None
        assert SITES_TABLE is not None
        assert LOG_DIR is not None

        assert BLANK_DEF is not None and type(BLANK_DEF) is str and len(BLANK_DEF) > 0
        assert NICK_DEF is not None and type(NICK_DEF) is str and len(NICK_DEF) > 0
        assert (
            SLIDER_DEF is not None and type(SLIDER_DEF) is list and len(SLIDER_DEF) >= 3
        )
        assert SITE_DEF is not None and type(SITE_DEF) is str
        assert DEFAULT_FG is not None and type(DEFAULT_FG) is str
        assert FANCY_SLIDER is not None and type(FANCY_SLIDER) is bool
        assert ENTRY_SCHEMA is not None and type(ENTRY_SCHEMA) is dict
        assert STATUSLINE_SCHEMA is not None and type(STATUSLINE_SCHEMA) is dict
    except AssertionError as ex:
        logger.error("Value in config file has invalid type.")
        raise TypeError(ex)
    except ImportError as ex:
        logger.error("Config file is incomplete.")
        raise ex
