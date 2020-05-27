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
log = logging.getLogger(__name__)

# get sockets, so bkapp and app can talk
bk_sockets, bk_port = get_sockets()

# start bokeh sever
t1 = Thread(target=bk_worker, args=[bk_sockets, bk_port], daemon=True)
t1.start()

bokeh_url = BOKEH_URL.replace('$PORT', str(bk_port))
log.info("Bokeh Server App Running at: %s", bokeh_url)

# start flask server
t2 = Thread(target=start_tornado, daemon=True)
t2.start()

log.info("Flask + Bokeh Server App Running at: %s", FLASK_URL)

# loop for ever
while True:
    time.sleep(0.01)
