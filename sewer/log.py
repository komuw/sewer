import logging

_logger = None


def _default_logger():
    logger = logging.getLogger("sewer")
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


def set_logger(logger):
    global _logger
    _logger = logger


def get_logger():
    return _logger


set_logger(_default_logger())
