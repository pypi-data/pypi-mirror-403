import abc
import os

from tmg_etl_pipeline import conf
from tmg_etl_pipeline import logs

class TMGETLPipeline(metaclass=abc.ABCMeta):

    def __init__(self, app_name, config_path):

        self.app_name = app_name

        self.config = conf.Client(config_path).config
        self.logger = logs.Client(app_name).logger

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        pass

    def cleanup(self, *args, **kwargs):
        pass

    def execute(self, *args, **kwargs):

        try:
            self.run(*args, **kwargs)
        finally:
            self.cleanup()

