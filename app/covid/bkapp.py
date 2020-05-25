"""
    Analyze COVID-19 cases and deaths in the US.
"""

import os
import time
import asyncio
import logging
from threading import Thread

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

from bokeh import __version__
from bokeh.palettes import Greens
from bokeh.models import Div
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.server.server import BaseServer
from bokeh.server.tornado import BokehTornado
from bokeh.server.util import bind_sockets
from bokeh.themes import Theme
from bokeh.layouts import (
    column,
    row
)

from distros import age_gender_histograms
from maps import Map
from trends import Trends
from fits import models_result
from database import DataBase
from utilities import cwd
from sql import FLDEM_VIEW_TABLE
from clf import (
    IMPORTANCE_TABLE,
    MODELS_ROC_TABLE
)
from config import (
    set_bokeh_port,
    FLASK_PORT,
    FLASK_ADDR,

    BOKEH_ADDR,
    BOKEH_PATH,
    BOKEH_URL
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)



class BokehApp:
    """
        Create Production Server Application
    """
    def __init__(self, doc):
        self.doc = doc

        _db = DataBase()
        self.data = _db.get_table(FLDEM_VIEW_TABLE)
        self.roc = _db.get_table(MODELS_ROC_TABLE)
        self.importance = _db.get_table(IMPORTANCE_TABLE)
        _db.close()
        log.info('data loaded')

        self.palette = dict()
        self.palette['theme'] = list(reversed(Greens[8]))
        self.palette['color'] = self.palette['theme'][2]
        self.palette['hover'] = self.palette['theme'][4]
        self.palette['trends'] = Greens[3]

    def add_heading(self, text, doc=None):
        """Add heading to current document

        Arguments:
            doc {Document} -- current bokeh document
            text {String} -- heading text

        Returns:
            Document -- updated bokeh document
        """
        if doc is None:
            doc = self.doc

        attributes = dict(height=30, width=800, align=None,
                          style={'width': '800px',
                                 'font-size': '125%',
                                 'color': self.palette['hover'],
                                 'text-align': 'center'})
        doc.add_root(Div(text=f"<b>{text}</b>", **attributes))
        return doc

    def add_footer(self, text, doc=None):
        """Add footer to current document

        Arguments:
            doc {Document} -- bokeh current document
            text {String} -- footer text

        Returns:
            Document -- updated bokeh document
        """
        if doc is None:
            doc = self.doc

        attributes = dict(height=15, width=800, align=None,
                          style={'width': '800px',
                                 'font-size': '100%',
                                 'font-style': 'italic',
                                 'font-weight': 'lighter',
                                 'color': 'darkgrey',
                                 'text-align': 'center'})
        doc.add_root(Div(text=f"<b>{text}</b>", **attributes))
        return doc

    def add_link(self, text, link, doc=None):
        """Add a link to current document

        Arguments:
            doc {Document} -- current bokeh document
            text {String} -- link text
            link {url} -- url to attached to text

        Returns:
            Document -- updated bokeh document
        """
        if doc is None:
            doc = self.doc

        attributes = dict(height=15, width=800, align=None,
                          style={'width': '800px',
                                 'font-size': '100%',
                                 'font-style': 'italic',
                                 'font-weight': 'lighter',
                                 'color': self.palette['hover'],
                                 'text-align': 'center'})

        color = self.palette['hover']
        style = f"style=\"text-decoration: none; color: {color};\""

        doc.add_root(Div(text=f"<a href=\"{link}\" {style}>{text}</a>",
                         **attributes))
        return doc

    def add_histograms(self, doc=None):
        """Add Histograms to current document

        Arguments:
            doc {Document} -- current bokeh document

        Returns:
            Document -- updated bokeh document
        """
        if doc is None:
            doc = self.doc

        doc.add_root(age_gender_histograms(
            self.data,
            self.palette['color'],
            self.palette['hover']
        ))
        log.info('histograms added')
        return doc

    def add_map(self, doc=None):
        """Add interactive map to current document

        Arguments:
            doc {Document} -- current bokeh document

        Returns:
            Document -- updated bokeh document
        """
        if doc is None:
            doc = self.doc

        plot = Map(plot_width=800,
                   plot_height=400,
                   palette=self.palette['theme'])
        layout = column(plot.controls['select'],
                        plot.plot,
                        row(plot.controls['slider'],
                            plot.controls['button']))
        doc.add_root(layout)
        log.info('us_map added')
        return doc

    def add_modeling(self, doc=None):
        """Add covid-19 models to current document

        Arguments:
            doc {Document} -- current bokeh document

        Returns:
            Document -- updated bokeh document
        """
        if doc is None:
            doc = self.doc

        doc.add_root(models_result(
            self.roc,
            self.importance,
            self.palette['theme'][2:],
            self.palette['color'],
            self.palette['hover']
        ))
        log.info('modeling added')
        return doc

    def add_trends(self, doc=None):
        """Add covid-19 trends to current document

        Arguments:
            doc {Document} -- current bokeh document

        Returns:
            Document -- updated bokeh document
        """
        if doc is None:
            doc = self.doc

        trend = Trends(self.palette['trends'])
        doc.add_root(trend.layout())
        log.info('trends added')
        return doc


def bkapp(doc):
    """Generate Landing Page

    Arguments:
        doc {Document} -- bokeh document

    Returns:
        Document -- updated bokeh document
    """
    app = BokehApp(doc)
    app.add_heading('US COVID-19 Cases in Last 15 Days')
    app.add_map()
    app.add_footer('Data Source: New York Times')
    app.add_footer('Technology Stack: HTML, CSS, JavaScript, '\
                   'Python, AJAX, Flask, Tornado, Bokeh, '\
                   'GeoPandas, SQLite')

    doc = app.add_link('Source Code at GitHub',
                       'https://github.com/hmanuel1/covid')

    doc.theme = Theme(filename=os.path.join(cwd(), "theme.yaml"))
    return doc


def bkapp_histograms(doc):
    """Generate histogram Page

    Arguments:
        doc {Document} -- bokeh document

    Returns:
        Document -- updated bokeh document
    """
    app = BokehApp(doc)
    app.add_heading('FL COVID-19 Distribution by Age and Gender')
    app.add_histograms()
    app.add_footer('Data Source: New York Times')
    app.add_footer('Technology Stack: HTML, CSS, JavaScript, '\
                   'Python, AJAX, Flask, Tornado, Bokeh, '\
                   'GeoPandas, SQLite')

    doc = app.add_link('Source Code at GitHub',
                       'https://github.com/hmanuel1/covid')

    doc.theme = Theme(filename=os.path.join(cwd(), "theme.yaml"))
    return doc


bkapp = Application(FunctionHandler(bkapp))


def  get_sockets():
    """bind to available socket in this system

    Returns:
        sockets, port -- sockets and port bind to
    """
    _sockets, _port = bind_sockets('0.0.0.0', 0)
    set_bokeh_port(_port)
    return _sockets, _port


def bk_worker(sockets, port):
    """ Worker thread to  run Bokeh Server """
    asyncio.set_event_loop(asyncio.new_event_loop())

    websocket_origins = [f"{BOKEH_ADDR}:{port}", f"{FLASK_ADDR}:{FLASK_PORT}"]
    bokeh_tornado = BokehTornado({BOKEH_PATH: bkapp},
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
