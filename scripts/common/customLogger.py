import logging
import pathlib

class Logger:
    """Class for custom logger"""

    def log(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        dirPath = pathlib.Path(__file__).parent.parent.parent.resolve()
        handler = logging.FileHandler(f"{dirPath}/logs/SystemOut.log")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s : %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger