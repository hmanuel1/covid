
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

FLASK_PATH = CONFIG.app.flask.path

if CONFIG.environment == 'local':
    # when running locally, this listening port
    # number is set to a constant in the config.yaml file.
    # normally, it is set to 8000.
    FLASK_PORT = CONFIG.proxy.flask.local.port
    FLASK_ADDR = CONFIG.proxy.flask.local.address
    FLASK_URL = f"http://{FLASK_ADDR}:{FLASK_PORT}"
elif CONFIG.environment == 'heroku':
    # when running at heroku,
    # heroku assigns a listening port number dynamically,
    # at starts up. Then, it passes this value in
    # the environment variable PORT to the application.
    # Only one public facing listening port is available
    # per heroku app.
    FLASK_PORT = os.environ.get('PORT')
    FLASK_DN = CONFIG.proxy.flask.heroku.domain
    FLASK_ADDR = CONFIG.proxy.flask.heroku.address
    FLASK_URL = f"https://{FLASK_DN}"


def set_bokeh_port(port):
    """ Set bokeh port number

    When running locally, it sets internal bokeh port
    number in .env file expected in this directory.

    When running at heroku, it sets the environment
    variable BOKEH_PORT.

    This value is set only once at startup by bkapp.py
    and used solely for communication between flask app
    and bokeh app.

    Arguments:
        port {int} -- bokeh port number
    """
    if CONFIG.environment == 'local':
        with open(os.path.join(cwd(), ".env"), 'w') as env_file:
            env_file.write(str(port))
    elif CONFIG.environment == 'heroku':
        os.environ['BOKEH_PORT'] = str(port)


def get_bokeh_port():
    """Get bokeh server port

    When running locally, it returns internal bokeh
    port number stored in the .env file.

    When running at heroku, it returns port number
    store in the environment variable BOKEH_PORT

    This value is set only once at startup by bkapp.py
    and used solely for communication between flask app
    and bokeh app.

    Returns:
        str -- bokeh port number
    """
    if CONFIG.environment == 'local':
        with open(os.path.join(cwd(), ".env"), 'r') as env_file:
            port = env_file.read()
    elif CONFIG.environment == 'heroku':
        port = os.environ.get('BOKEH_PORT')
    return port

BOKEH_PATH = CONFIG.app.bokeh.path
BOKEH_CDN = CONFIG.cdn.bokeh.url

BOKEH_ADDR = CONFIG.proxy.bokeh.local.address
BOKEH_WS_PATH = CONFIG.proxy.bokeh.local.path
BOKEH_URL = f"http://{BOKEH_ADDR}:$PORT"
BOKEH_URI = f"ws://{BOKEH_ADDR}:$PORT{BOKEH_WS_PATH}"
