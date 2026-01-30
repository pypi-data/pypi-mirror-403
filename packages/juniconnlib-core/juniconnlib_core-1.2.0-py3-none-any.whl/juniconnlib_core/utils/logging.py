import logging
import time
from datetime import datetime
from typing import Union

from agentlib import BaseModule


class CustomFormatter(logging.Formatter):
    """A custom logging formatter that adds color and a good timestamp
    and message format"""

    blue = "\x1b[34;20m"
    grey = "\x1b[37;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s "
        "(%(filename)s:%(funcName)s:%(lineno)d) (%(threadName)s)"
    )
    date_format = "%Y-%m-%dT%H:%M:%S%z"  # ISO 8601

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def formatTime(self, record, datefmt=None):
        dt = datetime.utcfromtimestamp(record.created)
        gmtime = time.gmtime(record.created)
        return dt.strftime(self.date_format) + f" ({gmtime.tm_zone})"

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt=self.date_format)
        return formatter.format(record)


def add_logging_handler(logger: logging.Logger, level: Union[str, int]):
    """Apply a specific formatting and coloring to a specified logger.

    Args:
        logger: The logger to which the format should be applied
        level: Either an int or string of the level to apply to the logger.
            See the official documentation for more details
            https://docs.python.org/3/library/logging.html#levels
    """
    ch = logging.StreamHandler()
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    # Make logging.INFO not the default to keep compatibility with the
    # agentlib BaseModuleConfig.log_level which defaults to None
    logger.setLevel(level)


def create_logger_for_module(module: BaseModule) -> logging.Logger:
    """Creates a logger.

    Creates a logger to be used for a module, since usually the standard
    formatter is overwritten by agent lib. It uses the module's 'log_level'
    defined in its config (which inherits from BaseModelConfig) if different
    log levels for different modules are necessary/wanted.

    Args:
        module(BaseModule): The module from which the logger should be derived

    Examples:
        >>> class Module(BaseModule):
        >>>     config: BaseModuleConfig
        >>>     def __init__(self, config, agent):
        >>>         super().__init__(config, agent)
        >>>         self.logger = create_logger_for_module(self)
    """
    logger = logging.getLogger(
        f"{module.__module__}.{module.__class__.__name__} "
        f"[{module.agent.id}/{module.id}]"
    )
    if module.config.log_level is not None:
        logger.setLevel(module.config.log_level)
    return logger
