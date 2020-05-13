"""
    Embed bokeh server session into flask framework
    Adapted from bokeh-master/examples/howto/serve_embed/flask_gunicorn_embed.py
"""

import os
from os.path import join

try:
    import asyncio
except ImportError:
    raise RuntimeError("This example requires Python3 / asyncio")

from threading import Thread

from flask import Flask, render_template
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import server_document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets
from bokeh.themes import Theme


app = Flask(__name__)


def cwd():
    """Return current working directory if running from bokeh server,
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


def bkapp(doc):
    """Bokeh test app

    Arguments:
        doc {Bokeh Document} -- document object with a plot and a slider
    """
    dataframe = sea_surface_temperature.copy()
    source = ColumnDataSource(data=dataframe)

    plot = figure(x_axis_type='datetime', y_range=(0, 25),
                  y_axis_label='Temperature (Celsius)',
                  title="Sea Surface Temperature at 43.18, -70.43")
    plot.line(x='time', y='temperature', source=source)

    def callback(_attr, _old, new):
        if new == 0:
            data = dataframe
        else:
            data = dataframe.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource.from_df(data)

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change('value', callback)

    doc.add_root(column(slider, plot))

    doc.theme = Theme(filename=join(cwd(), "theme.yaml"))

# can't use shortcuts here, since we are passing to low level BokehTornado
bkapp = Application(FunctionHandler(bkapp))

# This is so that if this app is run using something like "gunicorn -w 4" then
# each process will listen on its own port
sockets, port = bind_sockets("localhost", 0)

@app.route('/', methods=['GET'])
def bkapp_page():
    """Flask index route
        it takes the bokeh document from a tornado server and embeds its content
        into a jinja2 template.

    Returns:
        html document -- html render to the user browser
    """
    #script = server_document('http://localhost:%d/bkapp' % port)
    script = server_document(f"https://safe-scrubland-67589.herokuapp.com:{port}/bkapp")
    return render_template("embed.html", script=script, template="Flask")

def bk_worker():
    """ Worker thread to run the bokeh server once, so Bokeh document can be
        extracted for every http request.
    """
    asyncio.set_event_loop(asyncio.new_event_loop())

    env_port = os.environ.get('PORT', default='8000')

    websocket_origins = [f"0.0.0.0:{env_port}",
                         'localhost:{env_port}',
                         '127.0.0.1:8000',
                         f"safe-scrubland-67589.herokuapp.com:{env_port}"]

    bokeh_tornado = BokehTornado({'/bkapp': bkapp},
                                 extra_websocket_origins=websocket_origins)
    bokeh_http = HTTPServer(bokeh_tornado)
    bokeh_http.add_sockets(sockets)

    server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
    server.start()
    server.io_loop.start()

t = Thread(target=bk_worker)
t.daemon = True
t.start()
