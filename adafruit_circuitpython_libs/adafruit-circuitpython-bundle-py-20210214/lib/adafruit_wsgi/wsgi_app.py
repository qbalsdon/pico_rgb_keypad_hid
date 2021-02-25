# SPDX-FileCopyrightText: 2019 Matthew Costi for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`wsgi_app`
================================================================================

CircuitPython framework for creating WSGI server compatible web applications.
This does *not* include server implementation, which is necessary in order
to create a web application with this library.

* Circuit Python implementation of an WSGI Server for ESP32 devices:
  https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI.git


* Author(s): Matthew Costi

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import re

from adafruit_wsgi.request import Request

__version__ = "1.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_WSGI.git"


class WSGIApp:
    """
    The base WSGI Application class.
    """

    def __init__(self):
        self._routes = []
        self._variable_re = re.compile("^<([a-zA-Z]+)>$")

    def __call__(self, environ, start_response):
        """
        Called whenever the server gets a request.
        The environ dict has details about the request per wsgi specification.
        Call start_response with the response status string and headers as a list of tuples.
        Return a single item list with the item being your response data string.
        """

        status = ""
        headers = []
        resp_data = []

        request = Request(environ)

        match = self._match_route(request.path, request.method.upper())

        if match:
            args, route = match
            status, headers, resp_data = route["func"](request, *args)

        start_response(status, headers)
        return resp_data

    def on_request(self, methods, rule, request_handler):
        """
        Register a Request Handler for a particular HTTP method and path.
        request_handler will be called whenever a matching HTTP request is received.

        request_handler should accept the following args:
            (Dict environ)
        request_handler should return a tuple in the shape of:
            (status, header_list, data_iterable)

        :param list methods: the methods of the HTTP request to handle
        :param str rule: the path rule of the HTTP request
        :param func request_handler: the function to call
        """
        regex = "^"
        rule_parts = rule.split("/")
        for part in rule_parts:
            var = self._variable_re.match(part)
            if var:
                # If named capture groups ever become a thing, use this regex instead
                # regex += "(?P<" + var.group("var") + r">[a-zA-Z0-9_-]*)\/"
                regex += r"([a-zA-Z0-9_-]+)\/"
            else:
                regex += part + r"\/"
        regex += "?$"  # make last slash optional and that we only allow full matches
        self._routes.append(
            (re.compile(regex), {"methods": methods, "func": request_handler})
        )

    def route(self, rule, methods=None):
        """
        A decorator to register a route rule with an endpoint function.
        if no methods are provided, default to GET
        """
        if not methods:
            methods = ["GET"]
        return lambda func: self.on_request(methods, rule, func)

    def _match_route(self, path, method):
        for matcher, route in self._routes:
            match = matcher.match(path)
            if match and method in route["methods"]:
                return (match.groups(), route)
        return None
