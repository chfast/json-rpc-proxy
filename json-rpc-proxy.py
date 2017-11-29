#!/usr/bin/env python3

from http.server import HTTPServer, BaseHTTPRequestHandler
from os import path
from urllib.parse import urlparse
import socket


VERSION = '0.0.0'
BUFSIZE = 32
DELIMITER = ord('\n')
INFO = """JSON-RPC Proxy

Version: {}
Client: {}
Server: {}
"""


class HTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        client_url = 'unix:' + self.server.client_address
        server_url = '{}:{}'.format(self.server.server_name,
                                    self.server.server_port)
        info = INFO.format(VERSION, client_url, server_url)
        self.wfile.write(info.encode('utf-8'))

    def do_POST(self):
        request_length = int(self.headers['Content-Length'])
        request_content = self.rfile.read(request_length)
        self.log_message("Request:  {}".format(request_content))

        response_content = self.server.process(request_content)
        self.log_message("Response: {}".format(response_content))

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(response_content)


class Proxy(HTTPServer):

    def __init__(self, server_address, client_url):
        super(Proxy, self).__init__(server_address, HTTPRequestHandler)

        url = urlparse(client_url)
        assert url.scheme == 'unix'

        self.client_address = path.expanduser(url.path)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.client_address)

    def process(self, request):
        self.sock.sendall(request)

        response = b''
        while True:
            r = self.sock.recv(BUFSIZE)
            response += r
            if not r or r[-1] == DELIMITER:
                break

        return response


def run():
    server_address = ('127.0.0.1', 8545)
    client_url = 'unix:~/.ethereum/geth.ipc'
    proxy = Proxy(server_address, client_url)
    proxy.serve_forever()


if __name__ == '__main__':
    run()
