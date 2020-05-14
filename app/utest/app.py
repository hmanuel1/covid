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

from waitress import serve

from flask import Flask, render_template
from flask_cors import CORS

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import server_document
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets


LOCAL_TESTING = False


app = Flask(__name__)


app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)


def get_host():
    host = 'safe-scrubland-67589.herokuapp.com'
    sockets, port = bind_sockets('0.0.0.0', 0)
    if LOCAL_TESTING:
        host = '127.0.0.1'
        sockets, port = bind_sockets(host, 0)
    return host


def get_port():
    return int(os.environ.get('PORT', default='8000'))


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


# can't use shortcuts here, since we are passing to low level BokehTornado
bkapp = Application(FunctionHandler(bkapp))


@app.route('/')
def index():
    return "Add /graph or /env to base URL"


@app.route('/graph', methods=['GET'])
def graph_route():
    script = server_document(f"http://{get_host()}:{port}/bkapp")
    return render_template("embed.html", script=script, framework="Flask")


@app.route('/port', methods=['GET'])
def port_route():
    return str(sockets) + str(port)


@app.route('/env', methods=['GET'])
def env_route():
    env = '<p>'
    for  key, value in os.environ.items():
        env += f"<br>{key}: {value}"

    print('printing to browser', file=sys.stderr)
    return env + '</p>'


def bk_worker():
    """ Worker thread to run the bokeh server once, so Bokeh document can be
        extracted for every http request.
    """
    print(f'bokeh server listening at port={port}', file=sys.stderr)

    asyncio.set_event_loop(asyncio.new_event_loop())

    websocket_origins = [f"{get_host()}:{port}",
                         f"{get_host()}:{get_port()}",
                         f"localhost:{port}",
                         f"localhost:{get_port()}"
                         f"127.0.0.1:{port}",
                         f"127.0.0.1:{get_port()}"]

    conf = {'use_xheaders': True}
    bokeh_tornado = BokehTornado({'/bkapp': bkapp},
                                 extra_websocket_origins=websocket_origins,
                                 **conf)

    bokeh_http = HTTPServer(bokeh_tornado, xheaders=True, protocol='https')
    bokeh_http.add_sockets(sockets)

    server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
    server.start()
    server.io_loop.start()


t = Thread(target=bk_worker)
t.daemon = True
t.start()

if __name__ == '__main__':
    print(f"main server listening at {get_host()}:{get_port()}", file=sys.stderr)
    serve(app,
          threads=4,
          host='*',
          port=get_port(),
          channel_timeout=660,
          trusted_proxy=get_host(),
          trusted_proxy_headers="x-forwarded-for x-forwarded-host x-forwarded-proto x-forwarded-port",
          log_untrusted_proxy_headers=True)
