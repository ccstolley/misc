"""
Base class for HTTP-based clients.
"""

import httplib
import socket
import select
import logging
from common import config


class ClientError(Exception):
    """
    Base client exception.
    """
    pass


class ClientBase(object):
    """
    ClientBase is basically a thin wrapper around HTTPConnection.
    It handles things like timeouts and low level details of sending
    an HTTP payload to a server.
    """

    def __init__(self, host, port, headers={}, use_ssl=True, use_urllib=False):
        self.host = host
        self.port = port
        self.headers = headers
        self.use_ssl = use_ssl
        self.use_urllib = use_urllib
        self.log = logging.getLogger(__name__)
        FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
        logging.basicConfig(filename=config('DEBUG_LOGFILE'),
                            level=logging.DEBUG, format=FORMAT)

    def send_command_urllib(self, url, request, headers={}):
        """
        Due to some bug in python2.4, httplib doesn't work with
        certain http load balancers. I believe it has something to
        do with the port number being included with the request,
        but I'm really not sure. urllib seems to work ok, so this
        function attempts to replicate the same functionality.
        """
        import urllib
        port = ""
        if self.use_ssl:
            pfx = "https"
            if self.port != 443:
                port = ":%s" % self.port
        else:
            pfx = "http"
            if self.port != 80:
                port = ":%s" % self.port

        fullurl = "%s://%s%s%s" % (pfx, self.host, port, url)
        r = urllib.urlopen(fullurl, request)
        return r.read()

    def send_command_httplib(self, url, request, headers={}, method='POST'):
        """
        Open an HTTP connection, send request to url with headers.
        """
        if (self.use_ssl):
            self.log.debug("opening https://%s:%s%s", self.host,
                           self.port, url)
            connection = httplib.HTTPSConnection(self.host, self.port)
        else:
            self.log.debug("opening http://%s:%s%s", self.host,
                           self.port, url)
            connection = httplib.HTTPConnection(self.host, self.port)
        connection.set_debuglevel(0)
        try:
            connection.connect()
            connection.putrequest(method, url)
            connection.putheader("Content-length",
                                 len(request.encode('utf-8')))
            for header, value in headers.items():
                connection.putheader(header, value)
            connection.endheaders()
            readysocks = select.select((), (connection.sock,), (), 600.0)
            if (readysocks[1] == []):
                raise socket.timeout("Socket send() timed out")
            else:
                connection.send(request.encode('utf-8'))
        except httplib.socket.error, err:
            self.log.error("socket error %s:%d%s - %s", self.host, self.port,
                           url, err)
            raise socket.error("connect failed")
        # Since we're on python 2.4, we have to implement a socket read timeout
        # using select() rather than setting the timeout in the connection
        # constructor.
        readysocks = select.select((connection.sock, ), (), (), 600.0)
        if (readysocks[0] == []):
            raise socket.timeout("Socket read() timed out")
        response = connection.getresponse()
        try:
            resp = response.read()
        except socket.sslerror, e:
            self.log.error("read() failed due to sslerror \"%s\"", e)
            raise
        if (response.status != 200):
            self.log.error("HTTP %d: %s", response.status, resp)
            raise ClientError(resp)
        self.log.info("send_command(headers=%s...)", str(headers)[:54])
        self.log.debug("send_command(request=%s...)", str(request)[:54])
        return resp

    def send_command(self, url, request, headers={}):
        """
        Sends request to url with supplied headers.
        """
        if self.use_urllib:
            return self.send_command_urllib(url, request, headers)
        else:
            return self.send_command_httplib(url, request, headers)
