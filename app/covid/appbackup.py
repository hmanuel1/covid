"""Bokeh App with Flask

Returns:
    Bokeh Document -- Bokeh document
"""
import os
import asyncio
from os.path import join
from functools import partial
from threading import Thread

from flask import (
    Flask,
    render_template,
    request
)
from flask_cors import CORS

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import server_document
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets
from bokeh.themes import Theme
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature

from applayout import covid_app
from utilities import (
    cwd,
    BusySpinner
)
# from refresh import (
#     RefreshData,
#     Status
# )


HEROKU_APP_NAME = 'safe-scrubland-67589.herokuapp.com'


app = Flask(__name__)

app.config['CORS_HEADERS'] = 'Content-Type'
cors = CORS(app)

#refresh = RefreshData()

def parse_command(command):
    """Parse web maintenance commands

    Arguments:
        command {String} -- web maintenance commands
    """
    if command == 'refresh-data':
        pass
        #refresh.enable = True
    elif command == 'test-connection':
        print()
        print('<<<<<<< testing connection  >>>>>>>')
        print()


def update(doc, layout=None):
    """callback to load startup page or show task completion to user

    Arguments:
        doc {Document} -- bokeh Document object
        layout {bool} -- app startup document update [default {None}]
    """
    if layout is not None:
        doc.clear()
        doc.theme = Theme(filename=join(cwd(), "theme.yaml"))
        doc.add_root(layout)

    else:
        #duration = refresh.duration()
        #print(f'data refreshed in {duration} minutes')
        doc.clear()

        # show complete
        busy_spinner = BusySpinner()
        #busy_spinner.text(f'Data Refreshed in {duration} minutes')
        doc.add_root(busy_spinner.control())


def startup_worker(doc):
    """Application Startup
    """
    layout = covid_app()
    doc.add_next_tick_callback(partial(update, doc=doc, layout=layout))


def refresh_worker(doc):
    """Update COVID19 database

    """
    print('refresh working thread started.')
    #refresh.data()

    # update in next tick
    doc.add_next_tick_callback(partial(update, doc=doc))


def bkapp_func(doc):
    """Bokeh application function handler COVID-19 App

    Arguments:
        doc {Bokeh Document} -- DOM document
    """
    pass
    # database refresh
    # if refresh.status != Status.busy and refresh.enable:
    #     _tread = Thread(target=refresh_worker, args=[doc], daemon=True)
    #     _tread.start()

    #     # show busy spinner
    #     busy_spinner = BusySpinner()
    #     busy_spinner.show()
    #     doc.add_root(busy_spinner.control())

    # # application startup
    # else:
    #     # show busy spinner until application is ready
    #     _tread = Thread(target=startup_worker, args=[doc], daemon=True)
    #     _tread.start()

    #     doc.clear()
    #     busy_spinner = BusySpinner()
    #     busy_spinner.show()
    #     doc.add_root(busy_spinner.control())


def graph_func(doc):
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
bkapp = Application(FunctionHandler(graph_func))

# each process will listen on its own port
sockets, port = bind_sockets('localhost', 0)

@app.route('/hello', methods=['GET'])
def bkapp_route():
    """Embed Bokeh app into flask html page

    Returns:
        flask rendered html -- flask rendered html
    """
    command = request.args.get('command')
    parse_command(command)

    script = server_document(f"http://localhost:{port}/bkapp_private")

    return render_template("embed.html", script=script, title="COVID-19")

def bk_worker():
    """Worker thread
    """
    asyncio.set_event_loop(asyncio.new_event_loop())

    env_port = os.environ.get('PORT', default='8000')

    websocket_origins = [f"0.0.0.0:{env_port}",
                         f"0.0.0.0:{port}",
                         f"{HEROKU_APP_NAME}:{env_port}",
                         f"localhost:{port}",
                         '127.0.0.1:8000',
                         'localhost:8000']

    bokeh_tornado = BokehTornado({'/bkapp_private': bkapp},
                                 extra_websocket_origins=websocket_origins,
                                 session_token_expiration=660)

    bokeh_http = HTTPServer(bokeh_tornado)
    bokeh_http.add_sockets(sockets)

    server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
    server.start()
    server.io_loop.start()

t = Thread(target=bk_worker)
t.daemon = True
t.start()