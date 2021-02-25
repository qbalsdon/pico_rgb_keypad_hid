# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_io_errors.py`
======================================================
CircuitPython Adafruit IO Error Classes
* Author(s): Brent Rubell
"""


class AdafruitIO_ThrottleError(Exception):
    """Adafruit IO request error class for rate-limiting."""


class AdafruitIO_RequestError(Exception):
    """Adafruit IO request error class"""

    def __init__(self, response):
        response_content = response.json()
        error = response_content["error"]
        super().__init__(
            "Adafruit IO Error {0}: {1}".format(response.status_code, error)
        )


class AdafruitIO_MQTTError(Exception):
    """Adafruit IO MQTT error class"""

    def __init__(self, response):
        super().__init__("MQTT Error: {0}".format(response))
