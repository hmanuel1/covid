"""
    Embed bokeh server session into a flask framework
    Adapted from bokeh-master/examples/howto/serve_embed/flask_gunicorn_embed.py
"""

import time
import asyncio
import logging

from threading import Thread
import requests
from flask import Flask, render_template, request, Response
from flask_cors import CORS, cross_origin

from bokeh import __version__ as ver
from bokeh.embed import server_document
from bokeh.resources import Resources
from tornado.wsgi import WSGIContainer
from tornado.web import (
    Application,
    FallbackHandler
)
from tornado.ioloop import IOLoop

from wsproxy import WebSocketProxy
from config import (
    FLASK_PORT,
    FLASK_PATH,
    FLASK_URL,

    get_bokeh_port,
    BOKEH_URL
)


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SECRET_KEY'] = 'secret!'


@app.route('/', methods=['GET'])
def index():
    """ bk blue app """
    _js_resources = Resources(mode="cdn", log_level='trace').render_js()
    _css_resources = Resources(mode="cdn", log_level='trace').render_css()
    blue_app = server_document(FLASK_URL + '/bkapp-blue', resources=None)
    red_app = server_document(FLASK_URL + '/bkapp-red', resources=None)
    return render_template("embed.html",
                           js_resources=_js_resources,
                           css_resources=_css_resources,
                           blue=blue_app,
                           red=red_app)


@app.route('/blue', methods=['GET'])
def blue():
    """ bk blue app """
    _js_resources = Resources(mode="cdn", log_level='trace').render_js()
    _css_resources = Resources(mode="cdn", log_level='trace').render_css()
    blue_app = server_document(FLASK_URL + '/bkapp-blue', resources=None)
    return render_template("embed.html",
                           js_resources=_js_resources,
                           css_resources=_css_resources,
                           blue=blue_app)


@app.route('/red', methods=['GET'])
def red():
    """ bk red app """
    _js_resources = Resources(mode="cdn", log_level='trace').render_js()
    _css_resources = Resources(mode="cdn", log_level='trace').render_css()
    red_app = server_document(FLASK_URL + '/bkapp-red', resources=None)
    return render_template("embed.html",
                           js_resources=_js_resources,
                           css_resources=_css_resources,
                           red=red_app)


@app.route('/table', methods=['GET'])
def table():
    """ bk table app """
    _js_resources = Resources(mode="cdn", log_level='trace').render_js()
    _css_resources = Resources(mode="cdn", log_level='trace').render_css()
    table_app = server_document(FLASK_URL + '/bkapp-table', resources=None)
    return render_template("embed.html",
                           js_resources=_js_resources,
                           css_resources=_css_resources,
                           table=table_app)


@app.route('/<path:path>', methods=['GET'])
@cross_origin(origins='*')
def proxy(path):
    """ HTTP Proxy """
    query = ''
    if request.query_string is not None:
        query = '?' + request.query_string.decode("utf-8")

    bokeh_url = BOKEH_URL.replace('$PORT', get_bokeh_port())
    request_url = f"{bokeh_url}/{path}{query}"
    resp = requests.get(request_url)
    excluded_headers = ['content-length', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response

def start_tornado():
    """Start Tornado server to run a flask app in a Tornado
       WSGI container.
    """
    asyncio.set_event_loop(asyncio.new_event_loop())
    container = WSGIContainer(app)

    server = Application([
        # bokeh server app websocket handlers
        (r'/bkapp-blue/ws', WebSocketProxy, dict(path='/bkapp-blue')),
        (r'/bkapp-red/ws', WebSocketProxy, dict(path='/bkapp-red')),
        (r'/bkapp-table/ws', WebSocketProxy, dict(path='/bkapp-table')),
        # flask app
        (r'.*', FallbackHandler, dict(fallback=container))
    ], **{'use_xheaders': True})
    server.listen(port=FLASK_PORT)
    IOLoop.instance().start()

if __name__ == '__main__':
    t = Thread(target=start_tornado, daemon=True)
    t.start()
    log.info("Flask + Bokeh Server App Running at %s", FLASK_URL + FLASK_PATH)
    while True:
        time.sleep(0.05)
