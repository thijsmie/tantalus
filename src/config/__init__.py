import json
import os


class ConfigurationException(Exception):
    pass


class Config:
    def __init__(self, filename=None, file=None, config=None):
        if config is not None:
            self.config = config
        elif file is not None:
            self.config = json.load(file)
        elif filename is not None:
            with open(filename) as f:
                self.config = json.load(f)
        else:
            raise ConfigurationException("No configuration specified")

    def __getattr__(self, key):
        config = self.config[key]
        if type(config) is str and config.startswith("ENV{") and config.endswith("}"):
            config = os.environ[config[len("ENV{"):-1]]
        if type(config) == dict or type(config) == list:
            return Config(config=config)
        return config

    def __getitem__(self, key):
        return self.__getattr__(key)

    def get(self, key, default=None):
        if type(self.config) == dict and key in self.config:
            return self[key]
        elif type(self.config) == list and type(key) == int and key < len(self.config) and key >= 0:
            return self[key]
        else:
            return default

    @property
    def dict(self):
        a = {}
        for key in self.config:
            a[key] = self[key]
        return a

    def keys(self):
        return self.config.keys()

    def values(self):
        return self.config.values()

    def items(self):
        return self.config.items()

    def __contains__(self, item):
        return item in self.config