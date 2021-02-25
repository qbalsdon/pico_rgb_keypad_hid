# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_lifx`
================================================================================

A CircuitPython/Python library for communicating with the LIFX HTTP Remote API.

* Author(s): Brent Rubell for Adafruit Industries

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit ESP32SPI or ESP_ATcontrol library:
    https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI
    https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol
"""

__version__ = "1.9.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_lifx.git"

LIFX_URL = "https://api.lifx.com/v1/lights/"


class LIFX:
    """
    HTTP Interface for interacting with the LIFX API
    """

    def __init__(self, wifi_manager, lifx_token):
        """
        Creates an instance of the LIFX HTTP API client.
        :param wifi_manager wifi_manager: WiFiManager from ESPSPI_WiFiManager/ESPAT_WiFiManager
        :param str lifx_token: LIFX API token (https://api.developer.lifx.com/docs/authentication)
        """
        wifi_type = str(type(wifi_manager))
        if "ESPSPI_WiFiManager" in wifi_type or "ESPAT_WiFiManager" in wifi_type:
            self._wifi = wifi_manager
        else:
            raise TypeError("This library requires a WiFiManager object.")
        self._lifx_token = lifx_token
        self._auth_header = {
            "Authorization": "Bearer %s" % self._lifx_token,
        }

    @staticmethod
    def _parse_resp(response):
        """Parses and returns the JSON response returned
        from the LIFX HTTP API.
        """
        if response.status_code == 422:
            raise Exception(
                "Error: light(s) could not be toggled: " + response["error"]
            )
        try:
            for res in response.json()["results"]:
                return res["status"]
        except KeyError as err:
            raise KeyError(response.json()["error"]) from err

    # HTTP Requests
    def _post(self, path, data):
        """POST data to the LIFX API.
        :param str path: Formatted LIFX API URL
        :param json data: JSON data to POST to the LIFX API.
        """
        response = self._wifi.post(path, json=data, headers=self._auth_header)
        response = self._parse_resp(response)
        return response

    def _put(self, path, data):
        """PUT data to the LIFX API.
        :param str path: Formatted LIFX API URL
        :param json data: JSON data to PUT to the LIFX API.
        """
        response = self._wifi.put(path, json=data, headers=self._auth_header)
        response = self._parse_resp(response)
        return response

    def _get(self, path, data):
        """GET data from the LIFX API.
        :param str path: Formatted LIFX API URL
        :param json data: JSON data to GET from the LIFX API.
        """
        response = self._wifi.get(path, json=data, headers=self._auth_header)
        return response.json()

    def toggle_light(self, selector, all_lights=False, duration=0):
        """Toggles current state of LIFX light(s).
        :param dict selector: Selector to control which lights are requested.
        :param bool all: Toggle all lights at once. Defaults to false.
        :param double duration: Time (in seconds) to spend performing a toggle. Defaults to 0.
        """
        if all_lights:
            selector = "all"
        data = {"duration": duration}
        return self._post(LIFX_URL + selector + "/toggle", data)

    def move_effect(self, selector, move_direction, period, power_on):
        """Performs a linear move effect on a light, or lights.
        :param str move_direction: Move direction, forward or backward.
        :param double period: Time in second per effect cycle.
        :param bool power_on: Turn on a light before performing the move.
        """
        data = {"direction": move_direction, "period": period, "power_on": power_on}
        return self._post(LIFX_URL + selector + "/effects/move", data)

    def effects_off(self, selector, power_off=False):
        """Turns off any running effects on the selected device.
        :param dict selector: Selector to control which lights are requested.
        :param bool power_off: If true, the devices will also be turned off.
        """
        data = {"power_off", power_off}
        return self._post(LIFX_URL + selector + "/effects/off", data)

    def set_brightness(self, selector, brightness):
        """Sets the state of the lights within the selector.
        :param dict selector: Selector to control which lights are requested.
        :param double brightness: Brightness level of the light, from 0.0 to 1.0.
        """
        data = {"brightness": brightness}
        return self._put(LIFX_URL + selector + "/state", data)

    def set_color(self, selector, **kwargs):
        """Sets the state of the light's color within the selector.
        Valid arguments: https://api.developer.lifx.com/docs/set-state
        """
        return self._put(LIFX_URL + selector + "/state", kwargs)

    def list_lights(self):
        """Enumerates all the lights associated with the LIFX Cloud Account"""
        response = self._wifi.get(url=LIFX_URL + "all", headers=self._auth_header)
        resp = response.json()
        response.close()
        return resp
