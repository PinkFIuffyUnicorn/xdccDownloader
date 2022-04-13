import logging
from datetime import datetime

class Logger:
    """Class for custom logger"""

    def log(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler("../Logs/SystemOut.log")
        formatter = logging.Formatter("%(asctime)s | %(levelname)s : %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger