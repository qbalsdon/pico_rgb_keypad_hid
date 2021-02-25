# SPDX-FileCopyrightText: 2020 Jim Bennet for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Elena Horton for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`iotcentral_device`
=====================

Connectivity to Azure IoT Central

* Author(s): Jim Bennett, Elena Horton
"""

import json
import time
import adafruit_logging as logging
from .device_registration import DeviceRegistration
from .iot_error import IoTError
from .iot_mqtt import IoTMQTT, IoTMQTTCallback, IoTResponse


class IoTCentralDevice(IoTMQTTCallback):
    """A device client for the Azure IoT Central service"""

    def connection_status_change(self, connected: bool) -> None:
        """Called when the connection status changes
        :param bool connected: True if the device is connected, otherwise false
        """
        if self.on_connection_status_changed is not None:
            # pylint: disable=E1102
            self.on_connection_status_changed(connected)

    # pylint: disable=W0613, R0201
    def direct_method_called(self, method_name: str, payload: str) -> IoTResponse:
        """Called when a direct method is invoked
        :param str method_name: The name of the method that was invoked
        :param str payload: The payload with the message
        :returns: A response with a code and status to show if the method was correctly handled
        :rtype: IoTResponse
        """
        if self.on_command_executed is not None:
            # pylint: disable=E1102
            return self.on_command_executed(method_name, payload)

        raise IoTError("on_command_executed not set")

    def device_twin_desired_updated(
        self, desired_property_name: str, desired_property_value, desired_version: int
    ) -> None:
        """Called when the device twin desired properties are updated
        :param str desired_property_name: The name of the desired property that was updated
        :param desired_property_value: The value of the desired property that was updated
        :param int desired_version: The version of the desired property that was updated
        """
        if self.on_property_changed is not None:
            # pylint: disable=E1102
            self.on_property_changed(
                desired_property_name, desired_property_value, desired_version
            )

        # when a desired property changes, update the reported to match to keep them in sync
        self.send_property(desired_property_name, desired_property_value)

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
        if self.on_property_changed is not None:
            # pylint: disable=E1102
            self.on_property_changed(
                reported_property_name, reported_property_value, reported_version
            )

    # pylint: disable=R0913
    def __init__(
        self,
        socket,
        iface,
        id_scope: str,
        device_id: str,
        key: str,
        token_expires: int = 21600,
        logger: logging = None,
    ):
        """Create the Azure IoT Central device client
        :param socket: The network socket
        :param iface: The network interface
        :param str id_scope: The ID Scope of the device in IoT Central
        :param str device_id: The device ID of the device in IoT Central
        :param str key: The primary or secondary key of the device in IoT Central
        :param int token_expires: The number of seconds till the token expires, defaults to 6 hours
        :param adafruit_logging logger: The logger
        """
        self._socket = socket
        self._iface = iface
        self._id_scope = id_scope
        self._device_id = device_id
        self._key = key
        self._token_expires = token_expires
        self._logger = logger if logger is not None else logging.getLogger("log")
        self._device_registration = None
        self._mqtt = None

        self.on_connection_status_changed = None
        """A callback method that is called when the connection status is changed. This method should have the following signature:
        def connection_status_changed(connected: bool) -> None
        """

        self.on_command_executed = None
        """A callback method that is called when a command is executed on the device. This method should have the following signature:
        def connection_status_changed(method_name: str, payload: str) -> IoTResponse:

        This method returns an IoTResponse containing a status code and message from the command call. Set this appropriately
        depending on if the command was successfully handled or not. For example, if the command was handled successfully, set
        the code to 200 and message to "OK":

        return IoTResponse(200, "OK")
        """

        self.on_property_changed = None
        """A callback method that is called when property values are updated. This method should have the following signature:
        def property_changed(_property_name: str, property_value, version: int) -> None
        """

    def connect(self) -> None:
        """Connects to Azure IoT Central
        :raises DeviceRegistrationError: if the device cannot be registered successfully
        :raises RuntimeError: if the internet connection is not responding or is unable to connect
        """
        self._device_registration = DeviceRegistration(
            self._socket, self._id_scope, self._device_id, self._key, self._logger
        )

        token_expiry = int(time.time() + self._token_expires)
        hostname = self._device_registration.register_device(token_expiry)
        self._mqtt = IoTMQTT(
            self,
            self._socket,
            self._iface,
            hostname,
            self._device_id,
            self._key,
            self._token_expires,
            self._logger,
        )

        self._mqtt.connect()
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

    def send_property(self, property_name: str, value) -> None:
        """Updates the value of a writable property
        :param str property_name: The name of the property to write to
        :param value: The value to set on the property
        :raises IoTError: if there is no open connection to the MQTT broker
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        patch_json = {property_name: value}
        patch = json.dumps(patch_json)
        self._mqtt.send_twin_patch(patch)

    def send_telemetry(self, data) -> None:
        """Sends telemetry to the IoT Central app
        :param data: The telemetry data to send
        :raises IoTError: if there is no open connection to the MQTT broker
        """
        if self._mqtt is None:
            raise IoTError("You are not connected to IoT Central")

        if isinstance(data, dict):
            data = json.dumps(data)

        self._mqtt.send_device_to_cloud_message(data)
