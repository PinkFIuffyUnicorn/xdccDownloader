import logging
import pathlib

class Logger:
    """Class for custom logger"""

    def __init__(self, logging_level: int):
        self.logging_level = logging_level

    def log(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(self.logging_level)
        dirPath = pathlib.Path(__file__).parent.parent.parent.resolve()
        handler = logging.FileHandler(f"{dirPath}/logs/SystemOut.log")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s : %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger