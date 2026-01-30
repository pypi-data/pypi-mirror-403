import yaml


class Client:

    def __init__(self, config_location):
        self.config_location = config_location
        self._config = self._load_config()

    @property
    def config(self):
        return self._config

    def _load_config(self):
        with open(self.config_location, 'rt') as file:
            file_content = file.read()

        return yaml.load(file_content, Loader=yaml.SafeLoader)
