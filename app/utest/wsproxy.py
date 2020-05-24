"""
    Web Socket proxy between Browser and Bokeh Server
    using Tornado frame work.
"""

import logging

from tornado.ioloop import IOLoop
from tornado.websocket import (
    WebSocketHandler,
    websocket_connect
)

from config import (
    get_bokeh_port,
    BOKEH_URI
)


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class SocketConnection:
    """ Socket connection """
    def __init__(self, conn=None):
        self.conn = conn


class ProxyChannel:
    """ proxy channel """
    def __init__(self):
        self.client = SocketConnection()
        self.server = SocketConnection()


# pylint: disable=abstract-method, broad-except
# 1. data_received method does not need to be implemented for this application.
# 2. broad-excepts for coroutines are logged as errors.

class WebSocketProxy(WebSocketHandler):
    """ web socket proxy

    Establishes a web proxy socket channel for each
    websocket connection opened between Flask framework and
    Bokeh server using Tornado framework.

    """
    def __init__(self, application, *args, **kwargs):
        self.chan = ProxyChannel()
        self.uri = BOKEH_URI.replace('$PORT', get_bokeh_port())
        super().__init__(application, *args, **kwargs)

    def initialize(self):
        self.settings['websocket_ping_interval'] = 30
        self.settings['websocket_ping_timeout'] = 90

    def check_origin(self, origin):
        return True

    def select_subprotocol(self, subprotocols):
        if not len(subprotocols) == 2:
            return None
        return subprotocols[0]

    def open(self, *args, **kwargs):
        log.info("ws connection opened")
        self.chan.client.conn = self.ws_connection
        protocols = self.request.headers['Sec-Websocket-Protocol'].split(', ')
        IOLoop.current().spawn_callback(
            self._connect_to_server,
            self.uri,
            protocols
        )

    async def _connect_to_server(self, uri, protocols):
        try:
            connection = await websocket_connect(
                url=uri,
                subprotocols=protocols,
                on_message_callback=self._on_message_callback
            )
        except Exception as e:
            log.error("ws failed to connect to server %r", e, exc_info=True)
        else:
            self.chan.server.conn = connection
            log.info("ws proxy channel opened")
        return None

    # proxy to client (browser)
    def _on_message_callback(self, message):
        if message is not None:
            IOLoop.current().spawn_callback(
                self._send_to_client,
                message,
                not isinstance(message, str)
            )
        else:
            self.close()

    async def _send_to_client(self, message, binary):
        try:
            await self.write_message(message, binary)
        except Exception as e:
            log.error("ws error sending to browser %r", e, exc_info=True)
        return None

    # proxy to server (bokeh)
    def on_message(self, message):
        if message is not None:
            IOLoop.current().spawn_callback(
                self._send_to_server,
                message,
                not isinstance(message, str)
            )
        else:
            self.close()

    async def _send_to_server(self, message, binary):
        try:
            await self.chan.server.conn.write_message(message, binary)
        except Exception as e:
            log.error("ws error sending to server %r", e, exc_info=True)
        return None

    def on_close(self):
        log.info("ws connection closed.")
