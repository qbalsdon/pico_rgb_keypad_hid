# SPDX-FileCopyrightText: 2017 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# pylint: disable=missing-docstring,invalid-name,too-many-public-methods

"""
`adafruit_seesaw.digitalio`
====================================================
"""

import digitalio

__version__ = "1.7.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_seesaw.git"


class DigitalIO:
    """CircuitPython-compatible class for digital I/O pins

    This class is intended to be a compatible subset of `digitalio.DigitalInOut`.

    Due to technical limitations, PULL_DOWNs are not supported.

    :param ~adafruit_seesaw.seesaw.Seesaw seesaw: The device
    :param int pin: The pin number on the device"""

    def __init__(self, seesaw, pin):
        self._seesaw = seesaw
        self._pin = pin
        self._drive_mode = digitalio.DriveMode.PUSH_PULL
        self._direction = digitalio.Direction.INPUT
        self._pull = None
        self._value = False

    def deinit(self):
        pass

    def switch_to_output(self, value=False, drive_mode=digitalio.DriveMode.PUSH_PULL):
        """Switch the pin to output mode"""
        self._seesaw.pin_mode(self._pin, self._seesaw.OUTPUT)
        self._seesaw.digital_write(self._pin, value)
        self._drive_mode = drive_mode
        self._pull = None

    def switch_to_input(self, pull=None):
        """Switch the pin to input mode"""
        if pull == digitalio.Pull.DOWN:
            self._seesaw.pin_mode(self._pin, self._seesaw.INPUT_PULLDOWN)
        elif pull == digitalio.Pull.UP:
            self._seesaw.pin_mode(self._pin, self._seesaw.INPUT_PULLUP)
        else:
            self._seesaw.pin_mode(self._pin, self._seesaw.INPUT)
        self._pull = pull

    @property
    def direction(self):
        """Retrieve or set the direction of the pin"""
        return self._direction

    @direction.setter
    def direction(self, value):
        if value == digitalio.Direction.OUTPUT:
            self.switch_to_output()
        elif value == digitalio.Direction.INPUT:
            self.switch_to_input()
        else:
            raise ValueError("Out of range")
        self._direction = value

    @property
    def value(self):
        """Retrieve or set the value of the pin"""
        if self._direction == digitalio.Direction.OUTPUT:
            return self._value
        return self._seesaw.digital_read(self._pin)

    @value.setter
    def value(self, val):
        if not 0 <= val <= 1:
            raise ValueError("Out of range")
        self._seesaw.digital_write(self._pin, val)
        self._value = val

    @property
    def drive_mode(self):
        """Retrieve or set the drive mode of an output pin"""
        return self._drive_mode

    @drive_mode.setter
    def drive_mode(self, mode):
        pass

    @property
    def pull(self):
        """Retrieve or set the pull mode of an input pin"""
        return self._pull

    @pull.setter
    def pull(self, mode):
        if self._direction == digitalio.Direction.OUTPUT:
            raise AttributeError("cannot set pull on an output pin")
        if mode == digitalio.Pull.DOWN:
            self._seesaw.pin_mode(self._pin, self._seesaw.INPUT_PULLDOWN)
        elif mode == digitalio.Pull.UP:
            self._seesaw.pin_mode(self._pin, self._seesaw.INPUT_PULLUP)
        elif mode is None:
            self._seesaw.pin_mode(self._pin, self._seesaw.INPUT)
        else:
            raise ValueError("Out of range")
