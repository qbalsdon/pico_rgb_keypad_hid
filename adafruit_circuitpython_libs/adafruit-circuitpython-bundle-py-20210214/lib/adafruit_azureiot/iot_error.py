# SPDX-FileCopyrightText: 2020 Jim Bennet for Adafruit Industries
# SPDX-FileCopyrightText: 2020 Elena Horton for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`iot_error`
=====================

An error from the IoT service

* Author(s): Jim Bennett, Elena Horton
"""


class IoTError(Exception):
    """
    An error from the IoT service
    """

    def __init__(self, message: str):
        """Create the IoT Error
        :param str message: The error message
        """
        super().__init__(message)
        self.message = message
