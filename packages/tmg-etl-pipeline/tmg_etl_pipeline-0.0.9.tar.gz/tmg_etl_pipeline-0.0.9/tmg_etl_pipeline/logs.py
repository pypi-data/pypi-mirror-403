import logging
import logging.config


class Client:

    def __init__(self, app_name):
        self._logger = self._load_logger(app_name)

    @property
    def logger(self):
        return self._logger

    @staticmethod
    def _load_logger(app_name):

        logger = logging.getLogger(app_name)
        logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(name)s - %(asctime)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger

