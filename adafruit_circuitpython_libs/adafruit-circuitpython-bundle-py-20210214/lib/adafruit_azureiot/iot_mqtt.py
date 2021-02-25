# SPDX-FileCopyrightText: 2020 Jim Bennet for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Elena Horton for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`iot_mqtt`
=====================

An MQTT client for Azure IoT

* Author(s): Jim Bennett, Elena Horton
"""

import gc
import json
import time
import adafruit_minimqtt.adafruit_minimqtt as minimqtt
from adafruit_minimqtt.adafruit_minimqtt import MQTT
import adafruit_logging as logging
from .iot_error import IoTError
from .keys import compute_derived_symmetric_key
from .quote import quote
from . import constants

# pylint: disable=R0903
class IoTResponse:
    """A response from a direct method call"""

    def __init__(self, code: int, message: str):
        """Creates an IoT Response object
        :param int code: The HTTP response code for this method call, for example 200 if the method was handled successfully
        :param str message: The HTTP response message for this method call
        """
        self.response_code = code
        self.response_message = message


class IoTMQTTCallback:
    """An interface for classes that can be called by MQTT events"""

    def message_sent(self, data: str) -> None:
        """Called when a message is sent to the cloud
        :param str data: The data send with the message
        """

    def connection_status_change(self, connected: bool) -> None:
        """Called when the connection status changes
        :param bool connected: True if the device is connected, otherwise false
        """

    # pylint: disable=W0613, R0201
    def direct_method_invoked(self, method_name: str, payload: str) -> IoTResponse:
        """Called when a direct method is invoked
        :param str method_name: The name of the method that was invoked
        :param str payload: The payload with the message
        :returns: A response with a code and status to show if the method was correctly handled
        :rtype: IoTResponse
        """
        return IoTResponse(200, "")

    # pylint: disable=C0103
    def cloud_to_device_message_received(self, body: str, properties: dict) -> None:
        """Called when a cloud to device message is received
        :param str body: The body of the message
        :param dict properties: The propreties sent with the mesage
        """

    def device_twin_desired_updated(
        self, desired_property_name: str, desired_property_value, desired_version: int
    ) -> None:
        """Called when the device twin desired properties are updated
        :param str desired_property_name: The name of the desired property that was updated
        :param desired_property_value: The value of the desired property that was updated
        :param int desired_version: The version of the desired property that was updated
        """

    def device_twin_reported_updated(
        self,
        reported_property_name: str,
        reported_property_value,
        reported_version: int,
    ) -> None:
        """Called when the device twin reported values are updated
        :param str reported_property_name: The name of the reported property that was updated
        :param reported_property_value: The value of the reported property that was updated
        :param int reported_version: The version of the reported property that was updated
        """


# pylint: disable=R0902
class IoTMQTT:
    """MQTT client for Azure IoT"""

    def _gen_sas_token(self) -> str:
        token_expiry = int(time.time() + self._token_expires)
        uri = self._hostname + "%2Fdevices%2F" + self._device_id
        signed_hmac_sha256 = compute_derived_symmetric_key(
            self._key, uri + "\n" + str(token_expiry)
        )
        signature = quote(signed_hmac_sha256, "~()*!.'")
        if signature.endswith(
            "\n"
        ):  # somewhere along the crypto chain a newline is inserted
            signature = signature[:-1]
        token = "SharedAccessSignature sr={}&sig={}&se={}".format(
            uri, signature, token_expiry
        )
        return token

    def _create_mqtt_client(self) -> None:
        minimqtt.set_socket(self._socket, self._iface)

        self._mqtts = MQTT(
            broker=self._hostname,
            username=self._username,
            password=self._passwd,
            port=8883,
            keep_alive=120,
            is_ssl=True,
            client_id=self._device_id,
            log=True,
        )

        self._mqtts.logger.setLevel(self._logger.getEffectiveLevel())

        # set actions to take throughout connection lifecycle
        self._mqtts.on_connect = self._on_connect
        self._mqtts.on_log = self._on_log
        self._mqtts.on_publish = self._on_publish
        self._mqtts.on_disconnect = self._on_disconnect

        # initiate the connection using the adafruit_minimqtt library
        self._mqtts.connect()

    # pylint: disable=C0103, W0613
    def _on_connect(self, client, userdata, _, rc) -> None:
        self._logger.info(
            "- iot_mqtt :: _on_connect :: rc = "
            + str(rc)
            + ", userdata = "
            + str(userdata)
        )
        if rc == 0:
            self._mqtt_connected = True
        self._auth_response_received = True
        self._callback.connection_status_change(True)

    # pylint: disable=C0103, W0613
    def _on_log(self, client, userdata, level, buf) -> None:
        self._logger.info("mqtt-log : " + buf)
        if level <= 8:
            self._logger.error("mqtt-log : " + buf)

    def _on_disconnect(self, client, userdata, rc) -> None:
        self._logger.info("- iot_mqtt :: _on_disconnect :: rc = " + str(rc))
        self._auth_response_received = True

        if rc == 5:
            self._logger.error("on(disconnect) : Not authorized")
            self.disconnect()

        if rc == 1:
            self._mqtt_connected = False

        if rc != 5:
            self._callback.connection_status_change(False)

    def _on_publish(self, client, data, topic, msg_id) -> None:
        self._logger.info(
            "- iot_mqtt :: _on_publish :: " + str(data) + " on topic " + str(topic)
        )

    # pylint: disable=W0703
    def _handle_device_twin_update(self, client, topic: str, msg: str) -> None:
        self._logger.debug("- iot_mqtt :: _echo_desired :: " + topic)
        twin = None
        desired = None

        try:
            twin = json.loads(msg)
        except json.JSONDecodeError as e:
            self._logger.error(
                "ERROR: JSON parse for Device Twin message object has failed. => "
                + msg
                + " => "
                + str(e)
            )
            return

        if "reported" in twin:
            reported = twin["reported"]

            if "$version" in reported:
                reported_version = reported["$version"]
                reported.pop("$version")
            else:
                self._logger.error(
                    "ERROR: Unexpected payload for reported twin update => " + msg
                )
                return

            for property_name, value in reported.items():
                self._callback.device_twin_reported_updated(
                    property_name, value, reported_version
                )

        is_patch = "desired" not in twin

        if is_patch:
            desired = twin
        else:
            desired = twin["desired"]

        if "$version" in desired:
            desired_version = desired["$version"]
            desired.pop("$version")
        else:
            self._logger.error(
                "ERROR: Unexpected payload for desired twin update => " + msg
            )
            return

        for property_name, value in desired.items():
            self._callback.device_twin_desired_updated(
                property_name, value, desired_version
            )

    def _handle_direct_method(self, client, topic: str, msg: str) -> None:
        index = topic.find("$rid=")
        method_id = 1
        method_name = "None"
        if index == -1:
            self._logger.error("ERROR: C2D doesn't include topic id")
        else:
            method_id = topic[index + 5 :]
            topic_template = "$iothub/methods/POST/"
            len_temp = len(topic_template)
            method_name = topic[len_temp : topic.find("/", len_temp + 1)]

        ret = self._callback.direct_method_invoked(method_name, msg)
        gc.collect()

        ret_code = 200
        ret_message = "{}"
        if ret.response_code is not None:
            ret_code = ret.response_code
        if ret.response_message is not None:
            ret_message = ret.response_message

            # ret message must be JSON
            if not ret_message.startswith("{") or not ret_message.endswith("}"):
                ret_json = {"Value": ret_message}
                ret_message = json.dumps(ret_json)

        next_topic = "$iothub/methods/res/{}/?$rid={}".format(ret_code, method_id)
        self._logger.info(
            "C2D: => "
            + next_topic
            + " with data "
            + ret_message
            + " and name => "
            + method_name
        )
        self._send_common(next_topic, ret_message)

    def _handle_cloud_to_device_message(self, client, topic: str, msg: str) -> None:
        parts = topic.split("&")[1:]

        properties = {}
        for part in parts:
            key_value = part.split("=")
            properties[key_value[0]] = key_value[1]

        self._callback.cloud_to_device_message_received(msg, properties)
        gc.collect()

    def _send_common(self, topic: str, data) -> None:
        # Convert data to a string
        if isinstance(data, dict):
            data = json.dumps(data)

        if not isinstance(data, str):
            raise IoTError("Data must be a string or a dictionary")

        self._logger.debug("Sending message on topic: " + topic)
        self._logger.debug("Sending message: " + str(data))

        retry = 0

        while True:
            gc.collect()
            try:
                self._logger.debug("Trying to send...")
                self._mqtts.publish(topic, data)
                self._logger.debug("Data sent")
                break
            except RuntimeError as runtime_error:
                self._logger.info(
                    "Could not send data, retrying after 0.5 seconds: "
                    + str(runtime_error)
                )
                retry = retry + 1

                if retry >= 10:
                    self._logger.error("Failed to send data")
                    raise

                time.sleep(0.5)
                continue

        gc.collect()

    def _get_device_settings(self) -> None:
        self._logger.info("- iot_mqtt :: _get_device_settings :: ")
        self.loop()
        self._send_common("$iothub/twin/GET/?$rid=0", " ")

    # pylint: disable=R0913
    def __init__(
        self,
        callback: IoTMQTTCallback,
        socket,
        iface,
        hostname: str,
        device_id: str,
        key: str,
        token_expires: int = 21600,
        logger: logging = None,
    ):
        """Create the Azure IoT MQTT client
        :param IoTMQTTCallback callback: A callback class
        :param socket: The socket to communicate over
        :param iface: The network interface to communicate over
        :param str hostname: The hostname of the MQTT broker to connect to, get this by registering the device
        :param str device_id: The device ID of the device to register
        :param str key: The primary or secondary key of the device to register
        :param int token_expires: The number of seconds till the token expires, defaults to 6 hours
        :param adafruit_logging logger: The logger
        """
        self._callback = callback
        self._socket = socket
        self._iface = iface
        self._mqtt_connected = False
        self._auth_response_received = False
        self._mqtts = None
        self._device_id = device_id
        self._hostname = hostname
        self._key = key
        self._token_expires = token_expires
        self._username = "{}/{}/api-version={}".format(
            self._hostname, device_id, constants.IOTC_API_VERSION
        )
        self._passwd = self._gen_sas_token()
        self._logger = logger if logger is not None else logging.getLogger("log")
        self._is_subscribed_to_twins = False

    def _subscribe_to_core_topics(self):
        device_bound_topic = "devices/{}/messages/devicebound/#".format(self._device_id)
        self._mqtts.add_topic_callback(
            device_bound_topic, self._handle_cloud_to_device_message
        )
        self._mqtts.subscribe(device_bound_topic)

        self._mqtts.add_topic_callback("$iothub/methods/#", self._handle_direct_method)
        self._mqtts.subscribe("$iothub/methods/#")

    def _subscribe_to_twin_topics(self):
        self._mqtts.add_topic_callback(
            "$iothub/twin/PATCH/properties/desired/#", self._handle_device_twin_update
        )
        self._mqtts.subscribe(
            "$iothub/twin/PATCH/properties/desired/#"
        )  # twin desired property changes

        self._mqtts.add_topic_callback(
            "$iothub/twin/res/200/#", self._handle_device_twin_update
        )
        self._mqtts.subscribe("$iothub/twin/res/200/#")  # twin properties response

    def connect(self) -> bool:
        """Connects to the MQTT broker
        :returns: True if the connection is successful, otherwise False
        :rtype: bool
        """
        self._logger.info("- iot_mqtt :: connect :: " + self._hostname)

        self._create_mqtt_client()

        self._logger.info(" - iot_mqtt :: connect :: created mqtt client. connecting..")
        while self._auth_response_received is None:
            self.loop()

        self._logger.info(
            " - iot_mqtt :: connect :: on_connect must be fired. Connected ? "
            + str(self.is_connected())
        )
        if not self.is_connected():
            return False

        self._mqtt_connected = True
        self._auth_response_received = True

        self._subscribe_to_core_topics()

        return True

    def subscribe_to_twins(self) -> None:
        """Subscribes to digital twin updates
        Only call this if your tier of IoT Hub supports this
        """
        if self._is_subscribed_to_twins:
            return

        # do this separately as this is not supported in B1 hubs
        self._subscribe_to_twin_topics()

        self._get_device_settings()

        self._is_subscribed_to_twins = True

    def disconnect(self) -> None:
        """Disconnects from the MQTT broker"""
        if not self.is_connected():
            return

        self._logger.info("- iot_mqtt :: disconnect :: ")
        self._mqtt_connected = False
        self._mqtts.disconnect()

    def reconnect(self) -> None:
        """Reconnects to the MQTT broker"""
        self._logger.info("- iot_mqtt :: reconnect :: ")

        self._mqtts.reconnect()

    def is_connected(self) -> bool:
        """Gets if there is an open connection to the MQTT broker
        :returns: True if there is an open connection, False if not
        :rtype: bool
        """
        return self._mqtt_connected

    def loop(self) -> None:
        """Listens for MQTT messages"""
        if not self.is_connected():
            return

        self._mqtts.loop()
        gc.collect()

    def send_device_to_cloud_message(
        self, message, system_properties: dict = None
    ) -> None:
        """Send a device to cloud message from this device to Azure IoT Hub
        :param message: The message data as a JSON string or a dictionary
        :param system_properties: System properties to send with the message
        :raises: ValueError if the message is not a string or dictionary
        :raises RuntimeError: if the internet connection is not responding or is unable to connect
        """
        self._logger.info("- iot_mqtt :: send_device_to_cloud_message :: " + message)
        topic = "devices/{}/messages/events/".format(self._device_id)

        if system_properties is not None:
            firstProp = True
            for prop in system_properties:
                if not firstProp:
                    topic += "&"
                else:
                    firstProp = False
                topic += prop + "=" + str(system_properties[prop])

        # Convert message to a string
        if isinstance(message, dict):
            message = json.dumps(message)

        if not isinstance(message, str):
            raise ValueError("message must be a string or a dictionary")

        self._send_common(topic, message)
        self._callback.message_sent(message)

    def send_twin_patch(self, patch) -> None:
        """Send a patch for the reported properties of the device twin
        :param patch: The patch as a JSON string or a dictionary
        :raises: IoTError if the data is not a string or dictionary
        :raises RuntimeError: if the internet connection is not responding or is unable to connect
        """
        self._logger.info("- iot_mqtt :: sendProperty :: " + str(patch))
        topic = "$iothub/twin/PATCH/properties/reported/?$rid={}".format(
            int(time.time())
        )
        self._send_common(topic, patch)
