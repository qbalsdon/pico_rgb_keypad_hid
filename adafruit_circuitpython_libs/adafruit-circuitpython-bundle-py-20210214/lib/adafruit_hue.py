# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_hue`
================================================================================

CircuitPython helper library for the Philips Hue

* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit ESP32SPI or ESP_ATcontrol library:
    https://github.com/adafruit/Adafruit_CircuitPython_ESP32SPI
    https://github.com/adafruit/Adafruit_CircuitPython_ESP_ATcontrol

* SimpleIO library:
    https://github.com/adafruit/Adafruit_CircuitPython_SimpleIO
"""
import time
from random import randint
from simpleio import map_range

__version__ = "1.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Hue.git"


class Bridge:
    """
    HTTP Interface for interacting with a Philips Hue Bridge.
    """

    def __init__(self, wifi_manager, bridge_ip=None, username=None):
        """
        Creates an instance of the Philips Hue Bridge Interface.
        :param wifi_manager wifi_manager: WiFiManager from ESPSPI_WiFiManager/ESPAT_WiFiManager
        """
        wifi_type = str(type(wifi_manager))
        if "ESPSPI_WiFiManager" in wifi_type or "ESPAT_WiFiManager" in wifi_type:
            self._wifi = wifi_manager
        else:
            raise TypeError("This library requires a WiFiManager object.")
        self._ip = bridge_ip
        self._username = username
        if bridge_ip and username is not None:
            self._bridge_url = "http://{}/api".format(self._ip)
            self._username_url = self._bridge_url + "/" + self._username

    @staticmethod
    def rgb_to_hsb(rgb):
        """Returns RGB values as a HSL tuple.
        :param list rgb: RGB Values
        """
        r = rgb[0] / 255
        g = rgb[1] / 255
        b = rgb[2] / 255
        c_max = max(r, g, b)
        c_min = min(r, g, b)
        delta = c_max - c_min
        light = (c_max + c_min) / 2
        if delta == 0.0:
            hue = 0
            sat = 0
        else:
            if light < 0.5:
                sat = (c_max - c_min) / (c_max + c_min)
            else:
                sat = (c_max - c_min) / (2.0 - c_max - c_min)
            if c_max == r:
                hue = (g - b) / (c_max - c_min)
            elif c_max == g:
                hue = 2.0 + (b - r) / (c_max - c_min)
            else:
                hue = 4.0 + (r - g) / (c_max - c_min)
            hue *= 60
            if hue < 0:
                hue += 360
        hue = map_range(hue, 0, 360, 0, 65535)
        sat = map_range(sat * 100, 0, 100, 0, 254)
        light = map_range(light * 100, 0, 100, 0, 254)
        return round(hue), round(sat, 3), round(light, 2)

    # Hue Core API
    def discover_bridge(self):
        """Discovers Philips Hue Bridge IP from the hosted broker discovery service.
        Returns the bridge's IP address.
        """
        try:
            resp = self._wifi.get("https://discovery.meethue.com")
            json_data = resp.json()
            bridge_ip = json_data[0]["internalipaddress"]
            resp.close()
        except Exception as err:
            raise TypeError(
                "Ensure the Philips Bridge and CircuitPython device\
                             are both on the same WiFi network."
            ) from err
        self._ip = bridge_ip
        # set up hue bridge address path
        self._bridge_url = "http://{}/api".format(self._ip)
        return self._ip

    def register_username(self):
        """Attempts to register a Hue application username for use with your bridge.
        Provides a 30 second delay to press the link button on the bridge.
        Returns username or None.
        """
        self._bridge_url = "http://{}/api".format(self._ip)
        data = {"devicetype": "CircuitPython#pyportal{0}".format(randint(0, 100))}
        resp = self._wifi.post(self._bridge_url, json=data)
        connection_attempts = 1
        username = None
        while username is None and connection_attempts > 0:
            resp = self._wifi.post(self._bridge_url, json=data)
            json = resp.json()[0]
            if json.get("success"):
                username = str(json["success"]["username"])
                self._username_url = self._bridge_url + "/" + username
            connection_attempts -= 1
            time.sleep(1)
        resp.close()
        return username

    # Lights API
    def show_light_info(self, light_id):
        """Gets the attributes and state of a given light.
        :param int light_id: Light identifier.
        """
        resp = self._get("{0}/lights/{1}".format(self._username_url, light_id))
        return resp

    def set_light(self, light_id, **kwargs):
        """Allows the user to turn the light on and off, modify the hue and effects.
        You can pass the following as valid kwargs into this method:
        :param bool on: On/Off state of the light
        :param int bri: Brightness value of the light, 0-100% (1 to 254)
        :param int hue: Hue value to set the light, in degrees (0 to 360) (0 to 65535)
        :param int sat: Saturation of the light, 0-100% (0 to 254)
        (more settings at:
        https://developers.meethue.com/develop/hue-api/lights-api/#set-light-state )
        """
        resp = self._put(
            "{0}/lights/{1}/state".format(self._username_url, light_id), kwargs
        )
        return resp

    def toggle_light(self, light_id):
        """Gets and toggles the current state of a specified light.
        :param int light_id: Light identifier.
        """
        light_state = self.get_light(light_id)
        light_state = not light_state["state"]["on"]
        resp = self.set_light(light_id, on=light_state)
        return resp

    def get_light(self, light_id):
        """Gets the attributes and state of a provided light.
        :param int light_id: Light identifier.
        """
        resp = self._get("{0}/lights/{1}".format(self._username_url, light_id))
        return resp

    def get_lights(self):
        """Returns all the light resources available for a bridge."""
        resp = self._get(self._username_url + "/lights")
        return resp

    # Groups API
    def create_group(self, lights, group_id):
        """Creates a new group containing the lights specified and optional name.
        :param list lights: List of light identifiers.
        :param str group_id: Optional group name.
        """
        data = {"lights": lights, "name": group_id, "type": group_id}
        resp = self._post(self._username_url + "/groups", data)
        return resp

    def set_group(self, group_id, **kwargs):
        """Allows the user to turn the light on and off, modify the hue and effects.
        :param int group_id: Group identifier.
        You can pass the following as (optional) valid kwargs into this method:
        :param bool on: On/Off state of the light
        :param int bri: Brightness value of the light (1 to 254)
        :param int hue: Hue value to set the light to (0 to 65535)
        :param int sat: Saturation of the light (0 to 254)
        (more settings at
        https://developers.meethue.com/develop/hue-api/lights-api/#set-light-state )
        """
        resp = self._put(
            "{0}/groups/{1}/action".format(self._username_url, group_id), kwargs
        )
        return resp

    def get_groups(self):
        """Returns all the light groups available for a bridge."""
        resp = self._get(self._username_url + "/groups")
        return resp

    # Scene API
    def set_scene(self, group_id, scene_id):
        """Sets a group scene.
        :param str scene: The scene identifier
        """
        # To recall an existing scene, use the Groups API.
        self.set_group(group_id, scene=scene_id)

    def get_scenes(self):
        """Returns a list of all scenes currently stored in the bridge."""
        resp = self._get(self._username_url + "/scenes")
        return resp

    # HTTP Helpers for the Hue API
    def _post(self, path, data):
        """POST data
        :param str path: Formatted Hue API URL
        :param json data: JSON data to POST to the Hue API.
        """
        resp = self._wifi.post(path, json=data)
        resp_json = resp.json()
        resp.close()
        return resp_json

    def _put(self, path, data):
        """PUT data
        :param str path: Formatted Hue API URL
        :param json data: JSON data to PUT to the Hue API.
        """
        resp = self._wifi.put(path, json=data)
        resp_json = resp.json()
        resp.close()
        return resp_json

    def _get(self, path, data=None):
        """GET data
        :param str path: Formatted Hue API URL
        :param json data: JSON data to GET from the Hue API.
        """
        resp = self._wifi.get(path, json=data)
        resp_json = resp.json()
        resp.close()
        return resp_json
