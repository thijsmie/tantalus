import platform


class Config:
    base_url = ""
    username = None

    @classmethod
    def url(cls, path):
        return cls.base_url + path


class TestConfig(Config):
    base_url = "http://localhost:8000/poscl/"
    username = "pos_user"
    password = "pospass"
    endpoint = 1


class ProdConfig(Config):
    base_url = "https://new-tantalus.appspot.com/poscl/"


class ZuidConfig(ProdConfig):
    username = "Zuidkantine"


class NoordConfig(ProdConfig):
    username = "Noordkantine"


def get_config():
    hostname = platform.node().lower()
    if 'zuid' in hostname:
        print("Running configuration for Zuid.")
        return ZuidConfig
    elif 'noord' in hostname:
        print("Running configuration for Noord.")
        return NoordConfig
    else:
        print("Running configuration for Test.")
        return TestConfig
