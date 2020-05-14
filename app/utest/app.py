"""
    Embed bokeh server session into a flask framework
    Adapted from bokeh-master/examples/howto/serve_embed/flask_gunicorn_embed.py
"""

import os
import re
import sys
from os.path import join


try:
    import asyncio
except ImportError:
    raise RuntimeError("This example requires Python3 / asyncio")

from threading import Thread

from flask import Flask, render_template
from flask_cors import CORS

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh import __version__
from bokeh.resources import get_sri_hashes_for_version
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import server_document, components
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets


app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

# get get_sri_hashes_for_version(__version__)

def cwd():
    """Return current working directory if running from bokeh server,
       jupiter or python.

    Returns:
        String -- path to current working directory
    """
    try:
        __file__
    except NameError:
        working_dir = os.getcwd()
    else:
        working_dir = os.path.dirname(__file__)
    return working_dir


# get heroku app name in .env file
with open(join(cwd() + '/.env'), 'r') as env_file:
    app_name = env_file.read()

if not re.match(r'HEROKU_APP_NAME', app_name):
    sys.exit('ERROR: add HEROKU_APP_NAME to .env file')
else:
    app_name = re.sub(r'HEROKU_APP_NAME\s{0,}=', '', app_name).strip()


def bkapp(doc):
    """ Test plot with slider, callback

    Arguments:
        doc {Bokeh Document} -- bokeh document

    Returns:
        Bokeh Document --bokeh document with plot and slider added
    """
    dataframe = sea_surface_temperature.copy()
    source = ColumnDataSource(data=dataframe)

    plot = figure(x_axis_type='datetime', y_range=(0, 25),
                  y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line(x='time', y='temperature', source=source)
    return doc.add_root(plot)


def graph_plot():
    """ Test plot with no callbacks, no controls

    Returns:
        [type] -- [description]
    """
    dataframe = sea_surface_temperature.copy()
    source = ColumnDataSource(data=dataframe)

    plot = figure(x_axis_type='datetime', y_range=(0, 25),
                  y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line(x='time', y='temperature', source=source)
    return plot


# can't use shortcuts here, since we are passing to low level BokehTornado
bkapp = Application(FunctionHandler(bkapp))


# each process will listen on its own port
sockets, port = bind_sockets('0.0.0.0', 0)


@app.route('/')
def index():
    return "Add /graph or /plot or /env to base URL"


@app.route('/graph', methods=['GET'])
def graph_route():
    script = server_document(f"https://{app_name}:{port}/bkapp",
                             resources=None)
    return render_template("embed.html", script=script, framework="Flask")


@app.route('/plot', methods=['GET'])
def plot_route():
    script, div = components(graph_plot())
    return render_template("embed.html", div=div, script=script, framework="Flask")


@app.route('/env', methods=['GET'])
def env_route():
    env = '<p>'
    for  key, value in os.environ.items():
        env += f"<br>{key}: {value}"
    return env + '</p>'


def bk_worker():
    """ Worker thread to run the bokeh server once, so Bokeh document can be
        extracted for every http request.
    """
    asyncio.set_event_loop(asyncio.new_event_loop())

    env_port = os.environ.get('PORT', default='8000')

    websocket_origins = ["0.0.0.0", app_name, 'localhost']

    conf = {'use_xheaders': True}
    bokeh_tornado = BokehTornado({'/bkapp': bkapp},
                                 extra_websocket_origins=websocket_origins,
                                 **conf)


    bokeh_http = HTTPServer(bokeh_tornado, xheaders=True)
    bokeh_http.add_sockets(sockets)

    server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
    server.start()
    server.io_loop.start()

t = Thread(target=bk_worker)
t.daemon = True
t.start()
