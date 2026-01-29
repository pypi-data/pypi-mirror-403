import sys

from loguru import logger


def configure_logger():
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{file}</cyan>:<cyan>{line}</cyan> | {message}")
    logger.add("logs/app.log", rotation="10 MB", retention="10 days", compression="zip", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | {file}:{line}")
    return logger
