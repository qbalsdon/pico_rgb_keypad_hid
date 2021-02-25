# SPDX-FileCopyrightText: 2020 Jim Bennet for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Elena Horton for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`iothub_device`
=====================

Connectivity to Azure IoT Hub

* Author(s): Jim Bennett, Elena Horton
"""

import json
import adafruit_logging as logging
from .iot_error import IoTError
from .iot_mqtt import IoTMQTT, IoTMQTTCallback, IoTResponse


def _validate_keys(connection_string_parts):
    """Raise ValueError if incorrect combination of keys"""
    host_name = connection_string_parts.get(HOST_NAME)
    shared_access_key_name = connection_string_parts.get(SHARED_ACCESS_KEY_NAME)
    shared_access_key = connection_string_parts.get(SHARED_ACCESS_KEY)
    device_id = connection_string_parts.get(DEVICE_ID)

    if host_name and device_id and shared_access_key:
        pass
    elif host_name and shared_access_key and shared_access_key_name:
        pass
    else:
        raise ValueError("Invalid Connection String - Incomplete")


DELIMITER = ";"
VALUE_SEPARATOR = "="

HOST_NAME = "HostName"
SHARED_ACCESS_KEY_NAME = "SharedAccessKeyName"
SHARED_ACCESS_KEY = "SharedAccessKey"
SHARED_ACCESS_SIGNATURE = "SharedAccessSignature"
DEVICE_ID = "DeviceId"
MODULE_ID = "ModuleId"
GATEWAY_HOST_NAME = "GatewayHostName"

VALID_KEYS = [
    HOST_NAME,
    SHARED_ACCESS_KEY_NAME,
    SHARED_ACCESS_KEY,
    SHARED_ACCESS_SIGNATURE,
    DEVICE_ID,
    MODULE_ID,
    GATEWAY_HOST_NAME,
]


class IoTHubDevice(IoTMQTTCallback):
    """A device client for the Azure IoT Hub service"""

    def connection_status_change(self, connected: bool) -> None:
        """Called when the connection status changes
        :param bool connected: True if the device is connected, otherwise false
        """
        if self._on_connection_status_changed is not None:
            # pylint: disable=E1102
            self._on_connection_status_changed(connected)

    # pylint: disable=W0613, R0201
    def direct_method_invoked(self, method_name: str, payload) -> IoTResponse:
        """Called when a direct method is invoked
        :param str method_name: The name of the method that was invoked
        :param str payload: The payload with the message
        :returns: A response with a code and status to show if the method was correctly handled
        :rtype: IoTResponse
        """
        if self._on_direct_method_invoked is not None:
            # pylint: disable=E1102
            return self._on_direct_method_invoked(method_name, payload)

        raise IoTError("on_direct_method_invoked not set")

    # pylint: disable=C0103
    def cloud_to_device_message_received(self, body: str, properties: dict) -> None:
        """Called when a cloud to device message is received
        :param str body: The body of the message
        :param dict properties: The propreties sent with the mesage
        """
        if self._on_cloud_to_device_message_received is not None:
            # pylint: disable=E1102
            self._on_cloud_to_device_message_received(body, properties)

    def device_twin_desired_updated(
        self, desired_property_name: str, desired_property_value, desired_version: int
    ) -> None:
        """Called when the device twin desired properties are updated
        :param str desired_property_name: The name of the desired property that was updated
        :param desired_property_value: The value of the desired property that was updated
        :param int desired_version: The version of the desired property that was updated
        """
        if self._on_device_twin_desired_updated is not None:
            # pylint: disable=E1102
            self._on_device_twin_desired_updated(
                desired_property_name, desired_property_value, desired_version
            )

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
        if self._on_device_twin_reported_updated is not None:
            # pylint: disable=E1102
            self._on_device_twin_reported_updated(
                reported_property_name, reported_property_value, reported_version
            )

    def __init__(
        self,
        socket,
        iface,
        device_connection_string: str,
        token_expires: int = 21600,
        logger: logging = None,
    ):
        """Create the Azure IoT Central device client
        :param socket: The network socket
        :param iface: The network interface
        :param str device_connection_string: The Iot Hub device connection string
        :param int token_expires: The number of seconds till the token expires, defaults to 6 hours
        :param adafruit_logging logger: The logger
        """
        self._socket = socket
        self._iface = iface
        self._token_expires = token_expires
        self._logger = logger if logger is not None else logging.getLogger("log")

        connection_string_values = {}

        try:
            cs_args = device_connection_string.split(DELIMITER)
            connection_string_values = dict(
                arg.split(VALUE_SEPARATOR, 1) for arg in cs_args
            )
        except (ValueError, AttributeError) as e:
            raise ValueError(
                "Connection string is required and should not be empty or blank and must be supplied as a string"
            ) from e

        if len(cs_args) != len(connection_string_values):
            raise ValueError("Invalid Connection String - Unable to parse")

        _validate_keys(connection_string_values)

        self._hostname = connection_string_values[HOST_NAME]
        self._device_id = connection_string_values[DEVICE_ID]
        self._shared_access_key = connection_string_values[SHARED_ACCESS_KEY]

        self._logger.debug("Hostname: " + self._hostname)
        self._logger.debug("Device Id: " + self._device_id)
        self._logger.debug("Shared Access Key: " + self._shared_access_key)

        self._on_connection_status_changed = None
        self._on_direct_method_invoked = None
        self._on_cloud_to_device_message_received = None
        self._on_device_twin_desired_updated = None
        self._on_device_twin_reported_updated = None

        self._mqtt = None

    @property
    def on_connection_status_changed(self):
        """A callback method that is called when the connection status is changed. This method should have the following signature:
        def connection_status_changed(connected: bool) -> None
        """
        return self._on_connection_status_changed

    @on_connection_status_changed.setter
    def on_connection_status_changed(self, new_on_connection_status_changed):
        """A callback method that is called when the connection status is changed. This method should have the following signature:
        def connection_status_changed(connected: bool) -> None
        """
        self._on_connection_status_changed = new_on_connection_status_changed

    @property
    def on_direct_method_invoked(self):
        """A callback method that is called when a direct method is invoked.  This method should have the following signature:
        def direct_method_invoked(method_name: str, payload: str) -> IoTResponse:

        This method returns an IoTResponse containing a status code and message from the method invocation. Set this appropriately
        depending on if the method was successfully handled or not. For example, if the method was handled successfully, set
        the code to 200 and message to "OK":

        return IoTResponse(200, "OK")
        """
        return self._on_direct_method_invoked

    @on_direct_method_invoked.setter
    def on_direct_method_invoked(self, new_on_direct_method_invoked):
        """A callback method that is called when a direct method is invoked.  This method should have the following signature:
        def direct_method_invoked(method_name: str, payload: str) -> IoTResponse:

        This method returns an IoTResponse containing a status code and message from the method invocation. Set this appropriately
        depending on if the method was successfully handled or not. For example, if the method was handled successfully, set
        the code to 200 and message to "OK":

        return IoTResponse(200, "OK")
        """
        self._on_direct_method_invoked = new_on_direct_method_invoked

    @property
    def on_cloud_to_device_message_received(self):
        """A callback method that is called when a cloud to device message is received. This method should have the following signature:
        def cloud_to_device_message_received(body: str, properties: dict) -> None:
        """
        return self._on_cloud_to_device_message_received

    @on_cloud_to_device_message_received.setter
    def on_cloud_to_device_message_received(
        self, new_on_cloud_to_device_message_received
    ):
        """A callback method that is called when a cloud to device message is received. This method should have the following signature:
        def cloud_to_device_message_received(body: str, properties: dict) -> None:
        """
        self._on_cloud_to_device_message_received = (
            new_on_cloud_to_device_message_received
        )

    @property
    def on_device_twin_desired_updated(self):
        """A callback method that is called when the desired properties of the devices device twin are updated.
        This method should have the following signature:
        def device_twin_desired_updated(desired_property_name: str, desired_property_value, desired_version: int) -> None:
        """
        return self._on_device_twin_desired_updated

    @on_device_twin_desired_updated.setter
    def on_device_twin_desired_updated(self, new_on_device_twin_desired_updated):
        """A callback method that is called when the desired properties of the devices device twin are updated.
        This method should have the following signature:
        def device_twin_desired_updated(desired_property_name: str, desired_property_value, desired_version: int) -> None:
        """
        self._on_device_twin_desired_updated = new_on_device_twin_desired_updated

        if self._mqtt is not None:
            self._mqtt.subscribe_to_twins()

    @property
    def on_device_twin_reported_updated(self):
        """A callback method that is called when the reported properties of the devices device twin are updated.
        This method should have the following signature:
        def device_twin_reported_updated(reported_property_name: str, reported_property_value, reported_version: int) -> None:
        """
        return self._on_device_twin_reported_updated

    @on_device_twin_reported_updated.setter
    def on_device_twin_reported_updated(self, new_on_device_twin_reported_updated):
        """A callback method that is called when the reported properties of the devices device twin are updated.
        This method should have the following signature:
        def device_twin_reported_updated(reported_property_name: str, reported_property_value, reported_version: int) -> None:
        """
        self._on_device_twin_reported_updated = new_on_device_twin_reported_updated

        if self._mqtt is not None:
            self._mqtt.subscribe_to_twins()

    def connect(self) -> None:
        """Connects to Azure IoT Hub
        :raises RuntimeError: if the internet connection is not responding or is unable to connect
        """
        self._mqtt = IoTMQTT(
            self,
            self._socket,
            self._iface,
            self._hostname,
            self._device_id,
            self._shared_access_key,
            self._token_expires,
            self._logger,
        )
        self._mqtt.connect()

        if (
            self._on_device_twin_desired_updated is not None
            or self._on_device_twin_reported_updated is not None
        ):
            self._mqtt.subscribe_to_twins()

    def disconnect(self) -> None:
        """Disconnects from the MQTT broker
        :raises IoTError: if there is no open connection to the MQTT broker
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        self._mqtt.disconnect()

    def reconnect(self) -> None:
        """Reconnects to the MQTT broker"""
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        self._mqtt.reconnect()

    def is_connected(self) -> bool:
        """Gets if there is an open connection to the MQTT broker
        :returns: True if there is an open connection, False if not
        :rtype: bool
        """
        if self._mqtt is not None:
            return self._mqtt.is_connected()

        return False

    def loop(self) -> None:
        """Listens for MQTT messages
        :raises IoTError: if there is no open connection to the MQTT broker
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        self._mqtt.loop()

    def send_device_to_cloud_message(self, message, system_properties=None) -> None:
        """Send a device to cloud message from this device to Azure IoT Hub
        :param message: The message data as a JSON string or a dictionary
        :param system_properties: System properties to send with the message
        :raises: ValueError if the message is not a string or dictionary
        :raises RuntimeError: if the internet connection is not responding or is unable to connect
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        self._mqtt.send_device_to_cloud_message(message, system_properties)

    def update_twin(self, patch) -> None:
        """Updates the reported properties in the devices device twin
        :param patch: The JSON patch to apply to the device twin reported properties
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        if isinstance(patch, dict):
            patch = json.dumps(patch)

        self._mqtt.send_twin_patch(patch)
