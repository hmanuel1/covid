
""" App Configuration Module

"""
# %%
import os
from functools import reduce
import yaml


class DotDict(dict):
    """ Map dictionary to use `dot` notation

    This is copy from stackoverflow.com at:
        https://stackoverflow.com/questions/39463936

    This is a read-only view of the dictionary

    If a key is missing, it returns None instead of KeyError

    """
    def __getattr__(self, key):
        try:
            value = self[key]
        except KeyError:
            return None
        if isinstance(value, dict):
            return DotDict(value)
        return value

    def __getitem__(self, key):
        if isinstance(key, str) and '.' in key:
            key = key.split('.')
        if isinstance(key, (list, tuple)):
            return reduce(lambda d, kk: d[kk], key, self)
        return super().__getitem__(key)

    def get(self, key, default=None):
        if isinstance(key, str) and '.' in key:
            try:
                return self[key]
            except KeyError:
                return default
        return super().get(key, default=default)


def cwd():
    """Return current working directory if running in a server,
       jupiter or python.

    Returns:
        String -- path to current working directory
    """
    try:
        __file__
    except NameError:
        cur_working_dir = os.getcwd()
    else:
        cur_working_dir = os.path.dirname(__file__)
    return cur_working_dir


def load_config():
    """Load application configuration from config.yaml

    Returns:
        dictionary -- dictionary with configuration values
    """
    config_file = open(os.path.join(cwd(), "config.yaml"))
    config = yaml.load(config_file, Loader=yaml.FullLoader)
    return config

# %%
# Application configuration using dot notation
# Read-only view of configuration parameters defined
# in config.yaml expected in this directory.
CONFIG = DotDict(load_config())

# TODO public facing url in heroku this will be something
# like `https//white-horse-58990.heroku.com`
# in heroku this port is extracted from the
# PORT environment variable
FLASK_APP = CONFIG.app.flask.path
FLASK_PORT = CONFIG.proxy.flask.port
FLASK_ADDR = CONFIG.proxy.flask.address
FLASK_PATH = CONFIG.app.flask.path
FLASK_URL = f"http://{FLASK_ADDR}:{FLASK_PORT}"


# TODO bokeh_port must be passed to FLASK
# in heroku. This can be set as a environment
# variable save port to file
def set_bokeh_port(port):
    """Set bokeh port number in file

    Arguments:
        port {int} -- bokeh port number
    """
    with open(os.path.join(cwd(), ".env"), 'w') as env_file:
        env_file.write(str(port))

# TODO internal bokeh url and port
# in heroku this port can be extracted
# from a custom environment variable
def get_bokeh_port():
    """Get port bokeh number from file

    Returns:
        int -- bokeh port number
    """
    with open(os.path.join(cwd(), ".env"), 'r') as env_file:
        port = int(env_file.read())
    return port

BOKEH_ADDR = CONFIG.proxy.bokeh.address
BOKEH_PATH = CONFIG.app.bokeh.path
BOKEH_WS_PATH = CONFIG.proxy.bokeh.path
BOKEH_URL = f"http://{BOKEH_ADDR}:$PORT"
BOKEH_URI = f"ws://{BOKEH_ADDR}:$PORT{BOKEH_WS_PATH}"

BOKEH_CDN = CONFIG.cdn.bokeh.url
