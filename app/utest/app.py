
import os
import asyncio

from threading import Thread

import requests
from flask import Flask, render_template, request, Response
from flask_cors import CORS, cross_origin

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh import __version__ as ver
from bokeh.embed import server_document
from bokeh.resources import get_sri_hashes_for_version
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


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# port assigned by heroku and passed in the env variable `PORT`
# default port = 8000 for running app locally
PORT = int(os.environ.get('PORT', default='8000'))

# sockets for bokeh server
sockets, bokeh_app_port = bind_sockets('localhost', 0)


# public facing url in heroku these two lines will be something
# like `https//white-horse-58990.herokuapp.com`
# and  `white-horse-58990.heroku.com`
# FLASK_URL = f"http://127.0.0.1:{PORT}"
# FLASK_ADDR = f"127.0.0.1:{PORT}"
FLASK_URL = f"https://safe-scrubland-67589.herokuapp.com"
FLASK_ADDR = f"safe-scrubland-67589.herokuapp.com:{PORT}"


# internal bokeh url
# these two lines will stay the same at heroku
BOKEH_URL = f"http://localhost:{bokeh_app_port}"
BOKEH_ADDR = f"localhost:{bokeh_app_port}"


def bokeh_cdn_resources():
    included_resources = [f'bokeh-{ver}.min.js',
                          f'bokeh-api-{ver}.min.js',
                          f'bokeh-tables-{ver}.min.js',
                          f'bokeh-widgets-{ver}.min.js']

    resources = '  '
    for key, value in get_sri_hashes_for_version(ver).items():
        if key in included_resources:
            resources += '<script type="text/javascript" '
            resources += f'src="https://cdn.bokeh.org/bokeh/release/{key}" '
            resources += f'integrity="sha384-{value}" '
            resources += 'crossorigin="anonymous"></script>\n    '

    resources += '<script type="text/javascript">\n    '
    resources += '  Bokeh.set_log_level("info");\n    '
    resources += '</script>'
    return resources


@app.route('/', methods=['GET'])
def bkapp_route():
    resources = bokeh_cdn_resources()
    script = server_document(f"{FLASK_URL}/bkapp", resources=None)
    return render_template("embed.html", resources=resources, script=script,
                           template="Flask")


@app.route('/<path:path>', methods=['GET', 'POST', 'DELETE'])
@cross_origin(origins='*')
def proxy(path):
    query = request.query_string.decode("utf-8")
    if query != '':
        query = '?' + query

    # TODO one last puzzle to solve
    # there seems to be a handshake that Bokeh Server requires
    query = query.replace(FLASK_URL, BOKEH_URL)

    if request.method == 'GET':
        resp = requests.get(f'{BOKEH_URL}/{path}{query}')
        excluded_headers = ['content-encoding', 'content-length',
                            'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)

    elif request.method == 'POST':
        resp = requests.post(f'{BOKEH_URL}/{path}{query}', json=request.get_json())
        excluded_headers = ['content-encoding', 'content-length',
                            'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)

    elif request.method == 'DELETE':
        resp = requests.delete(f'{BOKEH_URL}/{path}{query}').content
        response = Response(resp.content, resp.status_code, headers)
    return response


def bkapp(doc):
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

    slider = Slider(start=0, end=30, value=0, step=1, title='Smoothing by N Days')
    slider.on_change('value', callback)

    doc.theme = Theme(filename=os.path.join(os.path.dirname(__file__), 'theme.yaml'))
    return doc.add_root(column(slider, plot))


def bk_worker(arg):
    asyncio.set_event_loop(asyncio.new_event_loop())

    conf = {'use_xheaders': True}
    bokeh_tornado = BokehTornado({'/bkapp': arg},
                                 extra_websocket_origins=[FLASK_ADDR, BOKEH_ADDR],
                                 **conf)

    bokeh_http = HTTPServer(bokeh_tornado, xheaders=True)
    bokeh_http.add_sockets(sockets)

    server = BaseServer(IOLoop.current(), bokeh_tornado, bokeh_http)
    server.start()
    server.io_loop.start()

# can't use shortcuts here, since we are passing to low level BokehTornado
bkapp = Application(FunctionHandler(bkapp))
thread = Thread(target=bk_worker, args=[bkapp], daemon=True)
thread.start()

# if __name__ == "__main__":
#     # in heroku this part will be done with gunicorn
#     # content of Procfile should look like "web: gunicorn -w 4 app:app"
#     app.run(port=PORT, debug=True)
