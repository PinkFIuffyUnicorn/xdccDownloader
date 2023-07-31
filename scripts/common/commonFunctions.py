from scripts.config import config
from time import sleep

class CommonFunctions():
    def __init__(self):
        self.logger = config.logger

    def retryOnException(self, func, args=(), retries=15, delay=5):
        for i in range(retries):
            try:
                return func(*args)
            except Exception as e:
                if i < retries - 1:
                    self.logger.warn(f"Function {func.__name__} has encountered an error, sleeping for {delay} seconds")
                    self.logger.error(f"Error: {str(e)}")
                    sleep(delay)
                else:
                    raise