"""
    Embed bokeh server session into a flask framework
    Adapted from bokeh-master/examples/howto/serve_embed/flask_gunicorn_embed.py
"""

import sys
import time

try:
    import asyncio
except ImportError:
    raise RuntimeError("This example requires Python3 / asyncio")

from threading import Thread

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh import __version__
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets
from bokeh.themes import Theme
from bokeh.layouts import column


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

    def callback(_attr, _old, new):
        if new == 0:
            data = dataframe
        else:
            data = dataframe.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource.from_df(data)

    slider = Slider(start=0, end=30, value=0, step=1, title="Smoothing by N Days")
    slider.on_change('value', callback)

    doc.theme = Theme(filename="theme.yaml")
    return doc.add_root(column(slider, plot))


def bk_worker():
    """ Worker thread to run the bokeh server once, so Bokeh document can be
        extracted for every http request.
    """
    print(f'bokeh server listening at http://localhost:{port}/', file=sys.stderr)

    asyncio.set_event_loop(asyncio.new_event_loop())

    websocket_origins = [f"localhost:{port}",
                         "localhost:8000",
                         f"127.0.0.1:{port}",
                         "127.0.0.1:8000"]

    conf = {'use_xheaders': True, 'stats_log_frequency_milliseconds': 2000}
    bokeh_tornado = BokehTornado({'/bkapp': bkapp},
                                 extra_websocket_origins=websocket_origins,
                                 **conf)

    bokeh_http = HTTPServer(bokeh_tornado, xheaders=True)
    bokeh_http.add_sockets(sockets)

    server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
    server.start()
    server.io_loop.start()

if __name__ == '__main__':
    sockets, port = bind_sockets('localhost', 0)

    # save port to file
    with open('.env', 'w') as env_file:
        env_file.write(str(port))

    # can't use shortcuts here, since we are passing to low level BokehTornado
    bkapp = Application(FunctionHandler(bkapp))

    t = Thread(target=bk_worker)
    t.daemon = True
    t.start()

    # loop for ever
    while True:
        time.sleep(2)
