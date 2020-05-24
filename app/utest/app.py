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
from tornado.wsgi import WSGIContainer
from tornado.web import (
    Application,
    FallbackHandler
)
from tornado.ioloop import IOLoop

from wsproxy import WebSocketProxy
from bkapp import bokeh_cdn_resources
from config import (
    FLASK_PORT,
    FLASK_PATH,
    FLASK_URL,

    get_bokeh_port,
    BOKEH_PATH,
    BOKEH_WS_PATH,
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
    """ Index """
    resources = bokeh_cdn_resources()
    script = server_document(FLASK_URL + BOKEH_PATH, resources=None)
    return render_template("embed.html", script=script, resources=resources)


@app.route('/<path:path>', methods=['GET'])
@cross_origin(origins='*')
def proxy(path):
    """ HTTP Proxy """
    query = ''
    if request.query_string is not None:
        query = '?' + request.query_string.decode("utf-8")

    bokeh_url = BOKEH_URL.replace('$PORT', str(get_bokeh_port()))
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
    server = Application([(BOKEH_WS_PATH, WebSocketProxy),
                          (r'.*', FallbackHandler, dict(fallback=container))],
                         **{'use_xheaders': True})
    server.listen(port=FLASK_PORT)
    IOLoop.instance().start()

if __name__ == '__main__':
    t = Thread(target=start_tornado, daemon=True)
    t.start()
    log.info("Flask + Bokeh Server App Running at %s", FLASK_URL + FLASK_PATH)
    while True:
        time.sleep(0.05)
