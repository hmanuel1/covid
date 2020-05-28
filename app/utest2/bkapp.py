"""
    Embed bokeh server session into a flask framework
    Adapted from bokeh-master/examples/howto/serve_embed/flask_gunicorn_embed.py
"""

import os
import time
import asyncio
import logging
from threading import Thread

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh import __version__ as bokeh_release_ver
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets
from bokeh.themes import Theme
from bokeh.layouts import column
from bokeh.resources import get_sri_hashes_for_version
from bokeh.models.widgets import DateFormatter, TableColumn, DataTable
from bokeh.models import (
    ColumnDataSource,
    Slider
)


from config import (
    cwd,
    set_bokeh_port,
    FLASK_PORT,
    FLASK_ADDR,

    BOKEH_ADDR,
    BOKEH_URL,
    BOKEH_CDN
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


BOKEH_BROWSER_LOGGING = """
    <script type="text/javascript">
      Bokeh.set_log_level("debug");
    </script>
"""

def bkapp_blue(doc):
    """ Bokeh App

    Arguments:
        doc {Bokeh Document} -- bokeh document

    Returns:
        Bokeh Document --bokeh document with plot and slider
    """
    dataframe = sea_surface_temperature.copy()
    source = ColumnDataSource(data=dataframe)

    plot = figure(x_axis_type='datetime', y_range=(0, 25),
                  y_axis_label='Temperature (Celsius)',
                  title="Blue App - Sea Surface Temperature at 43.18, -70.43")
    plot.line(x='time', y='temperature', source=source)

    def callback(_attr, _old, new):
        if new == 0:
            data = dataframe
        else:
            data = dataframe.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource.from_df(data)

    slider = Slider(start=0, end=30, value=0, step=1, title="Application Blue")
    slider.on_change('value', callback)

    doc.theme = Theme(filename=os.path.join(cwd(), 'theme.yaml'))
    return doc.add_root(column(slider, plot))

def bkapp_red(doc):
    """ Bokeh App

    Arguments:
        doc {Bokeh Document} -- bokeh document

    Returns:
        Bokeh Document --bokeh document with plot and slider
    """
    dataframe = sea_surface_temperature.copy()
    source = ColumnDataSource(data=dataframe)

    plot = figure(x_axis_type='datetime', y_range=(0, 25),
                  y_axis_label='Temperature (Celsius)',
                  title="Red App - Sea Surface Temperature at 43.18, -70.43")
    plot.line(x='time', y='temperature', source=source, line_color='red')

    def callback(_attr, _old, new):
        if new == 0:
            data = dataframe
        else:
            data = dataframe.rolling('{0}D'.format(new)).mean()
        source.data = ColumnDataSource.from_df(data)

    slider = Slider(start=0, end=30, value=0, step=1, title="Application Red")
    slider.on_change('value', callback)

    doc.theme = Theme(filename=os.path.join(cwd(), 'theme.yaml'))
    return doc.add_root(column(slider, plot))


def bkapp_table(doc):
    """Create a Table App

    Arguments:
        doc {Document} -- bokeh document

    Returns:
        Document -- updated bokeh document
    """
    data = sea_surface_temperature.copy()
    data.reset_index(inplace=True)
    source = ColumnDataSource(data=data)

    columns = [
        TableColumn(field='time', title='Time', formatter=DateFormatter(format='yy-mm-dd')),
        TableColumn(field='temperature', title='Temperature')
    ]

    data_table = DataTable(source=source, columns=columns, width=400,
                           selectable='checkbox', index_position=None)

    doc.theme = Theme(filename=os.path.join(cwd(), 'theme.yaml'))
    return doc.add_root(data_table)


def bokeh_cdn_resources():
    """Create script to load Bokeh resources from CDN based on
       installed bokeh version.

    Returns:
        script -- script to load resources from CDN
    """
    included_resources = [
        f'bokeh-{bokeh_release_ver}.min.js',
        f'bokeh-api-{bokeh_release_ver}.min.js',
        f'bokeh-tables-{bokeh_release_ver}.min.js',
        f'bokeh-widgets-{bokeh_release_ver}.min.js'
    ]

    resources = '\n    '
    for key, value in get_sri_hashes_for_version(bokeh_release_ver).items():
        if key in included_resources:
            resources += '<script type="text/javascript" '
            resources += f'src="{BOKEH_CDN}/{key}" '
            resources += f'integrity="sha384-{value}" '
            resources += 'crossorigin="anonymous"></script>\n    '

    resources += BOKEH_BROWSER_LOGGING
    return resources


def  get_sockets():
    """bind to available socket in this system

    Returns:
        sockets, port -- sockets and port bind to
    """
    _sockets, _port = bind_sockets('0.0.0.0', 0)
    set_bokeh_port(_port)
    return _sockets, _port


# two applications running in a bokeh server
_bkapp_blue = Application(FunctionHandler(bkapp_blue))
_bkapp_red = Application(FunctionHandler(bkapp_red))
_bkapp_table = Application(FunctionHandler(bkapp_table))


def bk_worker(sockets, port):
    """ Worker thread to  run Bokeh Server """

    asyncio.set_event_loop(asyncio.new_event_loop())

    websocket_origins = [f"{BOKEH_ADDR}:{port}", f"{FLASK_ADDR}:{FLASK_PORT}"]
    bokeh_tornado = BokehTornado({"/bkapp-blue": _bkapp_blue,
                                  "/bkapp-red": _bkapp_red,
                                  "/bkapp-table": _bkapp_table},
                                 extra_websocket_origins=websocket_origins,
                                 **{'use_xheaders': True})

    bokeh_http = HTTPServer(bokeh_tornado, xheaders=True)
    bokeh_http.add_sockets(sockets)
    server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
    server.start()
    server.io_loop.start()


if __name__ == '__main__':
    bk_sockets, bk_port = get_sockets()
    t = Thread(target=bk_worker, args=[bk_sockets, bk_port], daemon=True)
    t.start()
    bokeh_url = BOKEH_URL.replace('$PORT', str(bk_port))
    log.info("Bokeh Server App Running at: %s", bokeh_url)
    while True:
        time.sleep(0.05)
