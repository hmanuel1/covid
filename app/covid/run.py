"""
    Start Application Sequence:
    1) bind sockets for flask to bokeh communications
    2) start bokeh server (Tornado) running bokeh bkapp
    3) start flask server (Tornado) running flask app
"""
import time
import logging

from threading import Thread

from app import start_tornado
from bkapp import (
    bk_worker,
    get_sockets
)
from config import (
    BOKEH_URL,
    FLASK_URL
)

logging.basicConfig(level=logging.INFO)

def run():
    """Run flask application

    """
    log = logging.getLogger(__name__)

    # get sockets, so bkapp and app can talk
    bk_sockets, bk_port = get_sockets()

    # start bokeh sever
    thread_bokeh = Thread(target=bk_worker, args=[bk_sockets, bk_port], daemon=True)
    thread_bokeh.start()

    bokeh_url = BOKEH_URL.replace('$PORT', str(bk_port))
    log.info("Bokeh Server App Running at: %s", bokeh_url)

    # start flask server
    thread_flask = Thread(target=start_tornado, daemon=True)
    thread_flask.start()

    log.info("Flask + Bokeh Server App Running at: %s", FLASK_URL)

    # loop for ever
    while True:
        time.sleep(0.01)

run()
