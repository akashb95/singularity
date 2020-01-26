import logging


def setup_logger(name: str, level: int):
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s]: %(funcName)s in %(filename)s \n %(message)s \n----------------')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger
