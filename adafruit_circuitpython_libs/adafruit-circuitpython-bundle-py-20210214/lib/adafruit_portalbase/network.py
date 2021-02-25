# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_portalbase.network`
================================================================================

Base Library for the Portal-style libraries.


* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import os
import time
import gc
from micropython import const
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
from adafruit_fakerequests import Fake_Requests

try:
    import supervisor
except ImportError:
    supervisor = None

try:
    import rtc
except ImportError:
    rtc = None

try:
    from secrets import secrets
except ImportError:
    print(
        """WiFi settings are kept in secrets.py, please add them there!
the secrets dictionary must contain 'ssid' and 'password' at a minimum"""
    )

__version__ = "1.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PortalBase.git"

# pylint: disable=line-too-long, too-many-lines
# you'll need to pass in an io username and key
TIME_SERVICE = (
    "https://io.adafruit.com/api/v2/%s/integrations/time/strftime?x-aio-key=%s"
)
# our strftime is %Y-%m-%d %H:%M:%S.%L %j %u %z %Z see http://strftime.net/ for decoding details
# See https://apidock.com/ruby/DateTime/strftime for full options
TIME_SERVICE_STRFTIME = (
    "&fmt=%25Y-%25m-%25d+%25H%3A%25M%3A%25S.%25L+%25j+%25u+%25z+%25Z"
)
LOCALFILE = "local.txt"
# pylint: enable=line-too-long

STATUS_NO_CONNECTION = (100, 0, 0)
STATUS_CONNECTING = (0, 0, 100)
STATUS_FETCHING = (200, 100, 0)
STATUS_DOWNLOADING = (0, 100, 100)
STATUS_CONNECTED = (0, 100, 0)
STATUS_DATA_RECEIVED = (0, 0, 100)
STATUS_OFF = (0, 0, 0)

CONTENT_TEXT = const(1)
CONTENT_JSON = const(2)
CONTENT_IMAGE = const(3)


class HttpError(Exception):
    """HTTP Specific Error"""


class NetworkBase:
    """Network Base Class for the Portal-style libraries.

    :param wifi_module: An initialized WiFi Module that encapsulates the WiFi communications
    :param bool extract_values: If true, single-length fetched values are automatically extracted
                                from lists and tuples. Defaults to ``True``.
    :param debug: Turn on debug print outs. Defaults to False.
    :param list secrets_data: An optional list in place of the data contained in the secrets.py file

    """

    # pylint: disable=too-many-instance-attributes, too-many-locals, too-many-branches, too-many-statements
    def __init__(
        self, wifi_module, *, extract_values=True, debug=False, secrets_data=None
    ):
        self._wifi = wifi_module
        self._debug = debug
        self.json_transform = []
        self._extract_values = extract_values
        self._json_types = [
            "application/json",
            "application/javascript",
            "application/geo+json",
        ]

        if secrets_data is not None:
            self._secrets = secrets_data
        else:
            self._secrets = secrets

        # This may be removed. Using for testing
        self.requests = None

        try:
            os.stat(LOCALFILE)
            self.uselocal = True
        except OSError:
            self.uselocal = False

        gc.collect()

    def neo_status(self, value):
        """The status NeoPixel.

        :param value: The color to change the NeoPixel.

        """
        self._wifi.neo_status(value)

    @staticmethod
    def json_traverse(json, path):
        """
        Traverse down the specified JSON path and return the value or values

        :param json: JSON data to traverse
        :param list path: The path that we want to follow

        """
        value = json
        if not isinstance(path, (list, tuple)):
            raise ValueError(
                "The json_path parameter should be enclosed in a list or tuple."
            )
        for x in path:
            try:
                value = value[x]
            except (TypeError, KeyError, IndexError) as error:
                raise ValueError(
                    "The specified json_path was not found in the results."
                ) from error
            gc.collect()
        return value

    def add_json_transform(self, json_transform):
        """Add a function that is applied to JSON data when data is fetched

        :param json_transform: A function or a list of functions to call with the parsed JSON.
                               Changes and additions are permitted for the ``dict`` object.
        """
        if callable(json_transform):
            self.json_transform.append(json_transform)
        else:
            self.json_transform.extend(filter(callable, json_transform))

    def get_local_time(self, location=None):
        # pylint: disable=line-too-long
        """
        Fetch and "set" the local time of this microcontroller to the local time at the location, using an internet time API.

        :param str location: Your city and country, e.g. ``"New York, US"``.

        """
        # pylint: enable=line-too-long
        self.connect()
        api_url = None
        try:
            aio_username = self._secrets["aio_username"]
            aio_key = self._secrets["aio_key"]
        except KeyError:
            raise KeyError(
                "\n\nOur time service requires a login/password to rate-limit. Please register for a free adafruit.io account and place the user/key in your secrets file under 'aio_username' and 'aio_key'"  # pylint: disable=line-too-long
            ) from KeyError

        if location is None:
            location = self._secrets.get("timezone", location)
        if location:
            print("Getting time for timezone", location)
            api_url = (TIME_SERVICE + "&tz=%s") % (aio_username, aio_key, location)
        else:  # we'll try to figure it out from the IP address
            print("Getting time from IP address")
            api_url = TIME_SERVICE % (aio_username, aio_key)
        api_url += TIME_SERVICE_STRFTIME
        try:
            response = self._wifi.requests.get(api_url, timeout=10)
            if response.status_code != 200:
                error_message = (
                    "Error connection to Adafruit IO. The response was: "
                    + response.text
                )
                raise RuntimeError(error_message)
            if self._debug:
                print("Time request: ", api_url)
                print("Time reply: ", response.text)
            times = response.text.split(" ")
            the_date = times[0]
            the_time = times[1]
            year_day = int(times[2])
            week_day = int(times[3])
            is_dst = None  # no way to know yet
        except KeyError:
            raise KeyError(
                "Was unable to lookup the time, try setting secrets['timezone'] according to http://worldtimeapi.org/timezones"  # pylint: disable=line-too-long
            ) from KeyError
        year, month, mday = [int(x) for x in the_date.split("-")]
        the_time = the_time.split(".")[0]
        hours, minutes, seconds = [int(x) for x in the_time.split(":")]
        now = time.struct_time(
            (year, month, mday, hours, minutes, seconds, week_day, year_day, is_dst)
        )
        if rtc is not None:
            rtc.RTC().datetime = now

        # now clean up
        response.close()
        response = None
        gc.collect()

    def wget(self, url, filename, *, chunk_size=12000):
        """Download a url and save to filename location, like the command wget.

        :param url: The URL from which to obtain the data.
        :param filename: The name of the file to save the data to.
        :param chunk_size: how much data to read/write at a time.

        """
        print("Fetching stream from", url)

        self.neo_status(STATUS_FETCHING)
        response = self._wifi.requests.get(url, stream=True)

        headers = {}
        for title, content in response.headers.items():
            headers[title.lower()] = content

        if response.status_code == 200:
            print("Reply is OK!")
            self.neo_status((0, 0, 100))  # green = got data
        else:
            if self._debug:
                if "content-length" in headers:
                    print("Content-Length: {}".format(int(headers["content-length"])))
                if "date" in headers:
                    print("Date: {}".format(headers["date"]))
            self.neo_status((100, 0, 0))  # red = http error
            raise HttpError(
                "Code {}: {}".format(
                    response.status_code, response.reason.decode("utf-8")
                )
            )

        if self._debug:
            print(response.headers)
        if "content-length" in headers:
            content_length = int(headers["content-length"])
        else:
            raise RuntimeError("Content-Length missing from headers")
        remaining = content_length
        print("Saving data to ", filename)
        stamp = time.monotonic()
        file = open(filename, "wb")
        for i in response.iter_content(min(remaining, chunk_size)):  # huge chunks!
            self.neo_status(STATUS_DOWNLOADING)
            remaining -= len(i)
            file.write(i)
            if self._debug:
                print(
                    "Read %d bytes, %d remaining"
                    % (content_length - remaining, remaining)
                )
            else:
                print(".", end="")
            if not remaining:
                break
            self.neo_status(STATUS_FETCHING)
        file.close()

        response.close()
        stamp = time.monotonic() - stamp
        print(
            "Created file of %d bytes in %0.1f seconds" % (os.stat(filename)[6], stamp)
        )
        self.neo_status(STATUS_OFF)
        if not content_length == os.stat(filename)[6]:
            raise RuntimeError

    def connect(self):
        """
        Connect to WiFi using the settings found in secrets.py
        """
        self._wifi.neo_status(STATUS_CONNECTING)
        while not self._wifi.is_connected:
            # secrets dictionary must contain 'ssid' and 'password' at a minimum
            print("Connecting to AP", self._secrets["ssid"])
            if (
                self._secrets["ssid"] == "CHANGE ME"
                or self._secrets["password"] == "CHANGE ME"
            ):
                change_me = "\n" + "*" * 45
                change_me += "\nPlease update the 'secrets.py' file on your\n"
                change_me += "CIRCUITPY drive to include your local WiFi\n"
                change_me += "access point SSID name in 'ssid' and SSID\n"
                change_me += "password in 'password'. Then save to reload!\n"
                change_me += "*" * 45
                raise OSError(change_me)
            self._wifi.neo_status(STATUS_NO_CONNECTION)  # red = not connected
            try:
                self._wifi.connect(self._secrets["ssid"], self._secrets["password"])
                self.requests = self._wifi.requests
            except RuntimeError as error:
                print("Could not connect to internet", error)
                print("Retrying in 3 seconds...")
                time.sleep(3)

    def _get_io_client(self):
        self.connect()

        try:
            aio_username = self._secrets["aio_username"]
            aio_key = self._secrets["aio_key"]
        except KeyError:
            raise KeyError(
                "Adafruit IO secrets are kept in secrets.py, please add them there!\n\n"
            ) from KeyError

        return IO_HTTP(aio_username, aio_key, self._wifi.requests)

    def push_to_io(self, feed_key, data):
        """Push data to an adafruit.io feed

        :param str feed_key: Name of feed key to push data to.
        :param data: data to send to feed

        """

        io_client = self._get_io_client()

        while True:
            try:
                feed_id = io_client.get_feed(feed_key)
            except AdafruitIO_RequestError:
                # If no feed exists, create one
                feed_id = io_client.create_new_feed(feed_key)
            except RuntimeError as exception:
                print("An error occured, retrying! 1 -", exception)
                continue
            break

        while True:
            try:
                io_client.send_data(feed_id["key"], data)
            except RuntimeError as exception:
                print("An error occured, retrying! 2 -", exception)
                continue
            except NameError as exception:
                print(feed_id["key"], data, exception)
                continue
            break

    def get_io_feed(self, feed_key, detailed=False):
        """Return the Adafruit IO Feed that matches the feed key

        :param str feed_key: Name of feed key to match.
        :param bool detailed: Whether to return additional detailed information

        """
        io_client = self._get_io_client()

        while True:
            try:
                return io_client.get_feed(feed_key, detailed=detailed)
            except RuntimeError as exception:
                print("An error occured, retrying! 1 -", exception)
                continue
            break

    def get_io_group(self, group_key):
        """Return the Adafruit IO Group that matches the group key

        :param str group_key: Name of group key to match.

        """
        io_client = self._get_io_client()

        while True:
            try:
                return io_client.get_group(group_key)
            except RuntimeError as exception:
                print("An error occured, retrying! 1 -", exception)
                continue
            break

    def get_io_data(self, feed_key):
        """Return all values from Adafruit IO Feed Data that matches the feed key

        :param str feed_key: Name of feed key to receive data from.

        """
        io_client = self._get_io_client()

        while True:
            try:
                return io_client.receive_all_data(feed_key)
            except RuntimeError as exception:
                print("An error occured, retrying! 1 -", exception)
                continue
            break

    def fetch(self, url, *, headers=None, timeout=10):
        """Fetch data from the specified url and return a response object

        :param str url: The URL to fetch from.
        :param list headers: Extra headers to include in the request.
        :param int timeout: The timeout period in seconds.

        """
        gc.collect()

        response = None
        if self.uselocal:
            print("*** USING LOCALFILE FOR DATA - NOT INTERNET!!! ***")
            response = Fake_Requests(LOCALFILE)

        if not response:
            self.connect()
            # great, lets get the data
            print("Retrieving data...", end="")
            self.neo_status(STATUS_FETCHING)  # yellow = fetching data
            gc.collect()
            response = self._wifi.requests.get(url, headers=headers, timeout=timeout)
            gc.collect()

        return response

    def add_json_content_type(self, content_type):
        """
        Add a JSON content type

        :param str type: The content JSON type like 'application/json'

        """
        if isinstance(content_type, str):
            self._json_types.append(content_type)

    def _detect_content_type(self, headers):
        if "content-type" in headers:
            if "image/" in headers["content-type"]:
                return CONTENT_IMAGE
            for json_type in self._json_types:
                if json_type in headers["content-type"]:
                    return CONTENT_JSON
        return CONTENT_TEXT

    def check_response(self, response):
        """
        Check the response object status code, change the lights, and return content type

        :param response: The response object from a network call

        """
        headers = self._get_headers(response)

        if self._debug:
            print("Headers:", headers)
        if response.status_code == 200:
            print("Reply is OK!")
            self.neo_status(STATUS_DATA_RECEIVED)  # green = got data
            content_type = self._detect_content_type(headers)
        else:
            if self._debug:
                if "content-length" in headers:
                    print("Content-Length: {}".format(int(headers["content-length"])))
                if "date" in headers:
                    print("Date: {}".format(headers["date"]))
            self.neo_status((100, 0, 0))  # red = http error
            raise HttpError(
                "Code {}: {}".format(
                    response.status_code, response.reason.decode("utf-8")
                )
            )

        return content_type

    @staticmethod
    def _get_headers(response):
        headers = {}
        for title, content in response.headers.items():
            headers[title.lower()] = content
        gc.collect()
        return headers

    def fetch_data(
        self,
        url,
        *,
        headers=None,
        json_path=None,
        regexp_path=None,
        timeout=10,
    ):
        """Fetch data from the specified url and perfom any parsing

        :param str url: The URL to fetch from.
        :param list headers: Extra headers to include in the request.
        :param json_path: The path to drill down into the JSON data.
        :param regexp_path: The path formatted as a regular expression to search
                            the text data.
        :param int timeout: The timeout period in seconds.

        """
        response = self.fetch(url, headers=headers, timeout=timeout)
        return self._parse_data(response, json_path=json_path, regexp_path=regexp_path)

    def _parse_data(
        self,
        response,
        *,
        json_path=None,
        regexp_path=None,
    ):

        json_out = None
        content_type = self.check_response(response)

        if content_type == CONTENT_JSON:
            if json_path is not None:
                # Drill down to the json path and set json_out as that node
                if isinstance(json_path, (list, tuple)) and (
                    not json_path or not isinstance(json_path[0], (list, tuple))
                ):
                    json_path = (json_path,)
            try:
                gc.collect()
                json_out = response.json()
                if self._debug:
                    print(json_out)
                gc.collect()
            except ValueError:  # failed to parse?
                print("Couldn't parse json: ", response.text)
                raise
            except MemoryError:
                if supervisor is not None:
                    supervisor.reload()
                raise

        if content_type == CONTENT_JSON:
            values = self.process_json(json_out, json_path)
        elif content_type == CONTENT_TEXT:
            values = self.process_text(response.text, regexp_path)

        # Clean up
        json_out = None
        response = None
        if self._extract_values and len(values) == 1:
            values = values[0]

        gc.collect()

        return values

    @staticmethod
    def process_text(text, regexp_path):
        """
        Process text content

        :param str text: The entire text content
        :param regexp_path: The path formatted as a regular expression to search
                            the text data.

        """
        values = []
        if regexp_path:
            import re  # pylint: disable=import-outside-toplevel

            for regexp in regexp_path:
                values.append(re.search(regexp, text).group(1))
        else:
            values = text
        return values

    def process_json(self, json_data, json_path):
        """
        Process JSON content

        :param dict json_data: The JSON data as a dict
        :param json_path: The path to drill down into the JSON data.

        """
        values = []

        # optional JSON post processing, apply any transformations
        # these MAY change/add element
        for idx, json_transform in enumerate(self.json_transform):
            try:
                json_transform(json_data)
            except Exception as error:
                print("Exception from json_transform: ", idx, error)
                raise

        # extract desired text/values from json
        if json_data is not None and json_path:
            for path in json_path:
                try:
                    values.append(self.json_traverse(json_data, path))
                except KeyError:
                    print(json_data)
                    raise
        else:
            # No path given, so return JSON as string for compatibility
            import json  # pylint: disable=import-outside-toplevel

            values = json.dumps(json_data)
        return values
