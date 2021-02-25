# SPDX-FileCopyrightText: 2019 Google Inc.
# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: Apache-2.0

"""
`adafruit_gc_iot_core`
================================================================================

CircuitPython Google Cloud IoT Module

* Author(s): Brent Rubell, Google Inc.

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit CircuitPython JWT Module:
  https://github.com/adafruit/Adafruit_CircuitPython_JWT

* Adafruit CircuitPython Logging Module:
  https://github.com/adafruit/Adafruit_CircuitPython_Logging

"""
import time

import adafruit_logging as logging
from adafruit_jwt import JWT
import adafruit_ntp as NTP

__version__ = "3.0.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_GC_IOT_Core.git"


class MQTT_API_ERROR(Exception):
    """Exception raised on MQTT API return-code errors."""

    # pylint: disable=unnecessary-pass
    pass


class MQTT_API:
    """Client for interacting with Google's Cloud Core MQTT API.

    :param MiniMQTT mqtt_client: MiniMQTT Client object.

    """

    def __init__(self, mqtt_client):
        # Check that provided object is a MiniMQTT client object
        mqtt_client_type = str(type(mqtt_client))
        if "MQTT" in mqtt_client_type:
            self._client = mqtt_client
        else:
            raise TypeError(
                "This class requires a MiniMQTT client object, please create one."
            )
        # Verify that the MiniMQTT client was setup correctly.
        try:
            self.user = self._client.user
        except Exception as err:
            raise TypeError(
                "Google Cloud Core IoT MQTT API requires a username."
            ) from err
        # Validate provided JWT before connecting
        try:
            JWT.validate(self._client.password)
        except Exception as err:
            raise TypeError("Invalid JWT provided.") from err
        # If client has KeepAlive =0 or if KeepAlive > 20min,
        # set KeepAlive to 19 minutes to avoid disconnection
        # due to Idle Time (https://cloud.google.com/iot/quotas).
        if self._client.keep_alive == 0 or self._client.keep_alive >= 1200:
            self._client.keep_alive = 1140
        # User-defined MQTT callback methods must be init'd to None
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.on_subscribe = None
        self.on_unsubscribe = None
        # MQTT event callbacks
        self._client.on_connect = self._on_connect_mqtt
        self._client.on_disconnect = self._on_disconnect_mqtt
        self._client.on_message = self._on_message_mqtt
        self._client.on_subscribe = self._on_subscribe_mqtt
        self._client.on_unsubscribe = self._on_unsubscribe_mqtt
        self.logger = False
        if self._client.logger is not None:
            # Allow MQTT_API to utilize MiniMQTT Client's logger
            self.logger = True
            self._client.set_logger_level("DEBUG")
        self._connected = False
        # Set up a device identifier by splitting out the full CID
        self.device_id = self._client.client_id.split("/")[7]

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.disconnect()

    def disconnect(self):
        """Disconnects from the Google MQTT Broker."""
        try:
            self._client.disconnect()
        except Exception as err:
            raise ValueError("Unable to disconnect from Google's MQTT broker.") from err
        self._connected = False
        # Reset all user-defined callbacks
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.on_subscribe = None
        self.on_unsubscribe = None
        # De-initialize MiniMQTT Client
        self._client.deinit()

    def reconnect(self):
        """Reconnects to the Google MQTT Broker."""
        try:
            self._client.reconnect()
        except Exception as err:
            raise MQTT_API_ERROR("Error reconnecting to Google MQTT.") from err

    def connect(self):
        """Connects to the Google MQTT Broker."""
        self._client.connect()
        self._connected = True

    @property
    def is_connected(self):
        """Returns if client is connected to Google's MQTT broker."""
        return self._connected

    # pylint: disable=not-callable, unused-argument
    def _on_connect_mqtt(self, client, userdata, flags, return_code):
        """Runs when the mqtt client calls on_connect."""
        if self.logger:
            self._client.logger.debug("Client called on_connect.")
        if return_code == 0:
            self._connected = True
        else:
            raise MQTT_API_ERROR(return_code)
        # Call the user-defined on_connect callback if defined
        if self.on_connect is not None:
            self.on_connect(self, userdata, flags, return_code)

    # pylint: disable=not-callable, unused-argument
    def _on_disconnect_mqtt(self, client, userdata, return_code):
        """Runs when the client calls on_disconnect."""
        if self.logger:
            self._client.logger.debug("Client called on_disconnect")
        self._connected = False
        # Call the user-defined on_disconnect callblack if defined
        if self.on_disconnect is not None:
            self.on_disconnect(self)

    # pylint: disable=not-callable
    def _on_message_mqtt(self, client, topic, payload):
        """Runs when the client calls on_message."""
        if self.logger:
            self._client.logger.debug("Client called on_message")
        if self.on_message is not None:
            self.on_message(self, topic, payload)

    # pylint: disable=not-callable
    def _on_subscribe_mqtt(self, client, user_data, topic, qos):
        """Runs when the client calls on_subscribe."""
        if self.logger:
            self._client.logger.debug("Client called on_subscribe")
        if self.on_subscribe is not None:
            self.on_subscribe(self, user_data, topic, qos)

    # pylint: disable=not-callable
    def _on_unsubscribe_mqtt(self, client, user_data, topic, pid):
        """Runs when the client calls on_unsubscribe."""
        if self.logger:
            self._client.logger.debug("Client called on_unsubscribe")
        if self.on_unsubscribe is not None:
            self.on_unsubscribe(self, user_data, topic, pid)

    def loop(self):
        """Maintains a connection with Google Cloud IoT Core's MQTT broker. You will
        need to manually call this method within a loop to retain connection.

        Example of "pumping" a Google Core IoT loop.
        ..code-block:: python

            while True:
                google_iot.loop()

        """
        if self._connected:
            self._client.loop()

    def unsubscribe(self, topic, subfolder=None):
        """Unsubscribes from a Google Cloud IoT device topic.
        :param str topic: Required MQTT topic. Defaults to events.
        :param str subfolder: Optional MQTT topic subfolder. Defaults to None.

        """
        if subfolder is not None:
            mqtt_topic = "/devices/{}/{}/{}".format(self.device_id, topic, subfolder)
        else:
            mqtt_topic = "/devices/{}/{}".format(self.device_id, topic)
        self._client.unsubscribe(mqtt_topic)

    def unsubscribe_from_all_commands(self):
        """Unsubscribes from a device's "commands/#" topic.
        :param int qos: Quality of Service level for the message.

        """
        self.unsubscribe("commands/#")

    def subscribe(self, topic, subfolder=None, qos=1):
        """Subscribes to a Google Cloud IoT device topic.
        :param str topic: Required MQTT topic. Defaults to events.
        :param str subfolder: Optional MQTT topic subfolder. Defaults to None.
        :param int qos: Quality of Service level for the message.

        """
        if subfolder is not None:
            mqtt_topic = "/devices/{}/{}/{}".format(self.device_id, topic, subfolder)
        else:
            mqtt_topic = "/devices/{}/{}".format(self.device_id, topic)
        self._client.subscribe(mqtt_topic, qos)

    def subscribe_to_subfolder(self, topic, subfolder, qos=1):
        """Subscribes to a Google Cloud IoT device's topic subfolder
        :param str topic: Required MQTT topic.
        :param str subfolder: Optional MQTT topic subfolder. Defaults to None.
        :param int qos: Quality of Service level for the message.

        """
        self.subscribe(topic, subfolder, qos)

    def subscribe_to_config(self, qos=1):
        """Subscribes to a Google Cloud IoT device's configuration
        topic.
        :param int qos: Quality of Service level for the message.

        """
        self.subscribe("config", qos=qos)

    def subscribe_to_all_commands(self, qos=1):
        """Subscribes to a device's "commands/#" topic.
        :param int qos: Quality of Service level for the message.

        """
        self.subscribe("commands/#", qos=qos)

    def publish(self, payload, topic="events", subfolder=None, qos=0):
        """Publishes a payload from the device to its Google Cloud IoT
        device topic, defaults to "events" topic. To send state, use the
        publish_state method.

        :param int payload: Data to publish to Google Cloud IoT
        :param str payload: Data to publish to Google Cloud IoT
        :param float payload: Data to publish to Google Cloud IoT
        :param str topic: Required MQTT topic. Defaults to events.
        :param str subfolder: Optional MQTT topic subfolder. Defaults to None.
        :param int qos: Quality of Service level for the message.

        """
        if subfolder is not None:
            mqtt_topic = "/devices/{}/{}/{}".format(self.device_id, topic, subfolder)
        elif topic is not None:
            mqtt_topic = "/devices/{}/{}".format(self.device_id, topic)
        elif topic == "state" and subfolder is not None:
            raise ValueError("Subfolders are not supported for state messages.")
        else:
            raise TypeError("A topic string must be specified.")
        self._client.publish(mqtt_topic, payload, qos=qos)

    def publish_state(self, payload):
        """Publishes a device state message to the Cloud IoT MQTT API. Data
        sent by this method should be information about the device itself (such as number of
        crashes, battery level, or device health). This method is unidirectional,
        it communicates Device-to-Cloud only.

        """
        self._client.publish(payload, "state")


# pylint: disable=too-many-instance-attributes
class Cloud_Core:
    """CircuitPython Google Cloud IoT Core module.

    :param ESP_SPIcontrol esp: ESP32SPI object.
    :param dict secrets: Secrets.py file.
    :param bool log: Enable Cloud_Core logging, defaults to False.

    """

    def __init__(self, esp, secrets, log=False):
        self._esp = esp
        # Validate Secrets
        if hasattr(secrets, "keys"):
            self._secrets = secrets
        else:
            raise AttributeError(
                "Project settings are kept in secrets.py, please add them there!"
            )
        self.logger = None
        if log is True:
            self.logger = logging.getLogger("log")
            self.logger.setLevel(logging.DEBUG)
        # Configuration, from secrets file
        self._proj_id = secrets["project_id"]
        self._region = secrets["cloud_region"]
        self._reg_id = secrets["registry_id"]
        self._device_id = secrets["device_id"]
        self._private_key = secrets["private_key"]
        self.broker = "mqtt.googleapis.com"
        self.username = b"unused"
        self.cid = self.client_id

    @property
    def client_id(self):
        """Returns a Google Cloud IOT Core Client ID."""
        client_id = "projects/{0}/locations/{1}/registries/{2}/devices/{3}".format(
            self._proj_id, self._region, self._reg_id, self._device_id
        )
        if self.logger:
            self.logger.debug("Client ID: {}".format(client_id))
        return client_id

    def generate_jwt(self, ttl=43200, algo="RS256"):
        """Generates a JSON Web Token (https://jwt.io/) using network time.
        :param int jwt_ttl: When the JWT token expires, defaults to 43200 minutes (or 12 hours).
        :param str algo: Algorithm used to create a JSON Web Token.

        Example usage of generating and setting a JSON-Web-Token:
        ..code-block:: python

            jwt = CloudCore.generate_jwt()
            print("Generated JWT: ", jwt)

        """
        if self.logger:
            self.logger.debug("Generating JWT...")
        ntp = NTP.NTP(self._esp)
        ntp.set_time()
        claims = {
            # The time that the token was issued at
            "iat": time.time(),
            # The time the token expires.
            "exp": time.time() + ttl,
            # The audience field should always be set to the GCP project id.
            "aud": self._proj_id,
        }
        jwt = JWT.generate(claims, self._private_key, algo)
        return jwt
