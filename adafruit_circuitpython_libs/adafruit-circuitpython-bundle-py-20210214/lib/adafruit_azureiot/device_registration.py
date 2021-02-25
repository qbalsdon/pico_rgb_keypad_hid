# SPDX-FileCopyrightText: 2020 Jim Bennet for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Elena Horton for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`device_registration`
=====================

Handles registration of IoT Central devices, and gets the hostname to use when connecting
to IoT Central over MQTT

* Author(s): Jim Bennett, Elena Horton
"""

import gc
import json
import time
import adafruit_requests as requests
import adafruit_logging as logging
from adafruit_logging import Logger
from . import constants
from .quote import quote
from .keys import compute_derived_symmetric_key

# Azure HTTP error status codes
AZURE_HTTP_ERROR_CODES = [400, 401, 404, 403, 412, 429, 500]


class DeviceRegistrationError(Exception):
    """
    An error from the device registration
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class DeviceRegistration:
    """
    Handles registration of IoT Central devices, and gets the hostname to use when connecting
    to IoT Central over MQTT
    """

    _loop_interval = 2

    @staticmethod
    def _parse_http_status(status_code: int, status_reason: str) -> None:
        """Parses status code, throws error based on Azure IoT Common Error Codes.
        :param int status_code: HTTP status code.
        :param str status_reason: Description of HTTP status.
        :raises DeviceRegistrationError: if the status code is an error code
        """
        for error in AZURE_HTTP_ERROR_CODES:
            if error == status_code:
                raise DeviceRegistrationError(
                    "Error {0}: {1}".format(status_code, status_reason)
                )

    def __init__(
        self, socket, id_scope: str, device_id: str, key: str, logger: Logger = None
    ):
        """Creates an instance of the device registration service
        :param socket: The network socket
        :param str id_scope: The ID scope of the device to register
        :param str device_id: The device ID of the device to register
        :param str key: The primary or secondary key of the device to register
        :param adafruit_logging.Logger logger: The logger to use to log messages
        """
        self._id_scope = id_scope
        self._device_id = device_id
        self._key = key
        self._logger = logger if logger is not None else logging.getLogger("log")

        requests.set_socket(socket)

    def _loop_assign(self, operation_id, headers) -> str:
        uri = "https://%s/%s/registrations/%s/operations/%s?api-version=%s" % (
            constants.DPS_END_POINT,
            self._id_scope,
            self._device_id,
            operation_id,
            constants.DPS_API_VERSION,
        )
        self._logger.info("- iotc :: _loop_assign :: " + uri)

        response = self._run_get_request_with_retry(uri, headers)

        try:
            data = response.json()
        except ValueError as error:
            err = "ERROR: " + str(error) + " => " + str(response)
            self._logger.error(err)
            raise DeviceRegistrationError(err) from error

        loop_try = 0

        if data is not None and "status" in data:
            if data["status"] == "assigning":
                time.sleep(self._loop_interval)
                if loop_try < 20:
                    loop_try = loop_try + 1
                    return self._loop_assign(operation_id, headers)

                err = "ERROR: Unable to provision the device."
                self._logger.error(err)
                raise DeviceRegistrationError(err)

            if data["status"] == "assigned":
                state = data["registrationState"]
                return state["assignedHub"]
        else:
            data = str(data)

        err = "DPS L => " + str(data)
        self._logger.error(err)
        raise DeviceRegistrationError(err)

    def _run_put_request_with_retry(self, url, body, headers):
        retry = 0
        response = None

        while True:
            gc.collect()
            try:
                self._logger.debug("Trying to send...")
                response = requests.put(url, json=body, headers=headers)
                self._logger.debug("Sent!")
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
        return response

    def _run_get_request_with_retry(self, url, headers):
        retry = 0
        response = None

        while True:
            gc.collect()
            try:
                self._logger.debug("Trying to send...")
                response = requests.get(url, headers=headers)
                self._logger.debug("Sent!")
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
        return response

    def register_device(self, expiry: int) -> str:
        """
        Registers the device with the IoT Central device registration service.
        Returns the hostname of the IoT hub to use over MQTT
        :param int expiry: The expiry time for the registration
        :returns: The underlying IoT Hub that this device should connect to
        :rtype: str
        :raises DeviceRegistrationError: if the device cannot be registered successfully
        :raises RuntimeError: if the internet connection is not responding or is unable to connect
        """
        # pylint: disable=C0103
        sr = self._id_scope + "%2Fregistrations%2F" + self._device_id
        sig_no_encode = compute_derived_symmetric_key(
            self._key, sr + "\n" + str(expiry)
        )
        sig_encoded = quote(sig_no_encode, "~()*!.'")
        auth_string = (
            "SharedAccessSignature sr="
            + sr
            + "&sig="
            + sig_encoded
            + "&se="
            + str(expiry)
            + "&skn=registration"
        )

        headers = {
            "content-type": "application/json; charset=utf-8",
            "user-agent": "iot-central-client/1.0",
            "Accept": "*/*",
        }

        if auth_string is not None:
            headers["authorization"] = auth_string

        body = {"registrationId": self._device_id}

        uri = "https://%s/%s/registrations/%s/register?api-version=%s" % (
            constants.DPS_END_POINT,
            self._id_scope,
            self._device_id,
            constants.DPS_API_VERSION,
        )

        self._logger.info("Connecting...")
        self._logger.info("URL: " + uri)
        self._logger.info("body: " + json.dumps(body))

        response = self._run_put_request_with_retry(uri, body, headers)

        data = None
        try:
            data = response.json()
        except ValueError as error:
            err = (
                "ERROR: non JSON is received from "
                + constants.DPS_END_POINT
                + " => "
                + str(response)
                + " .. message : "
                + str(error)
            )
            self._logger.error(err)
            raise DeviceRegistrationError(err) from error

        if "errorCode" in data:
            err = "DPS => " + str(data)
            self._logger.error(err)
            raise DeviceRegistrationError(err)

        time.sleep(1)
        return self._loop_assign(data["operationId"], headers)
