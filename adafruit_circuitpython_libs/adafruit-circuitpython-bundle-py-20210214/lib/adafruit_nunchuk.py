# SPDX-FileCopyrightText: 2019 Carter Nelson for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_nunchuk`
================================================================================

CircuitPython library for Nintendo Nunchuk controller


* Author(s): Carter Nelson

Implementation Notes
--------------------

**Hardware:**

* `Wii Remote Nunchuk <https://en.wikipedia.org/wiki/Wii_Remote#Nunchuk>`_
* `Wiichuck <https://www.adafruit.com/product/342>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
import time
from collections import namedtuple
from adafruit_bus_device.i2c_device import I2CDevice

__version__ = "1.0.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Nunchuk.git"

_I2C_INIT_DELAY = 0.1


class Nunchuk:
    """
    Class which provides interface to Nintendo Nunchuk controller.

    :param i2c: The `busio.I2C` object to use.
    :param address: The I2C address of the device. Default is 0x52.
    :type address: int, optional
    :param i2c_read_delay: The time in seconds to pause between the
        I2C write and read. This needs to be at least 200us. A
        conservative default of 2000us is used since some hosts may
        not be able to achieve such timing.
    :type i2c_read_delay: float, optional
    """

    _Values = namedtuple("Values", ("joystick", "buttons", "acceleration"))
    _Joystick = namedtuple("Joystick", ("x", "y"))
    _Buttons = namedtuple("Buttons", ("C", "Z"))
    _Acceleration = namedtuple("Acceleration", ("x", "y", "z"))

    def __init__(self, i2c, address=0x52, i2c_read_delay=0.002):
        self.buffer = bytearray(8)
        self.i2c_device = I2CDevice(i2c, address)
        self._i2c_read_delay = i2c_read_delay
        time.sleep(_I2C_INIT_DELAY)
        with self.i2c_device as i2c_dev:
            # turn off encrypted data
            # http://wiibrew.org/wiki/Wiimote/Extension_Controllers
            i2c_dev.write(b"\xF0\x55")
            time.sleep(_I2C_INIT_DELAY)
            i2c_dev.write(b"\xFB\x00")

    @property
    def values(self):
        """The current state of all values."""
        self._read_data()
        return self._Values(
            self._joystick(do_read=False),
            self._buttons(do_read=False),
            self._acceleration(do_read=False),
        )

    @property
    def joystick(self):
        """The current joystick position."""
        return self._joystick()

    @property
    def buttons(self):  # pylint: disable=invalid-name
        """The current pressed state of button Z."""
        return self._buttons()

    @property
    def acceleration(self):
        """The current accelerometer reading."""
        return self._acceleration()

    def _joystick(self, do_read=True):
        if do_read:
            self._read_data()
        return self._Joystick(self.buffer[0], self.buffer[1])  # x, y

    def _buttons(self, do_read=True):
        if do_read:
            self._read_data()
        return self._Buttons(
            not bool(self.buffer[5] & 0x02), not bool(self.buffer[5] & 0x01)  # C  # Z
        )

    def _acceleration(self, do_read=True):
        if do_read:
            self._read_data()
        return self._Acceleration(
            ((self.buffer[5] & 0xC0) >> 6) | (self.buffer[2] << 2),  # ax
            ((self.buffer[5] & 0x30) >> 4) | (self.buffer[3] << 2),  # ay
            ((self.buffer[5] & 0x0C) >> 2) | (self.buffer[4] << 2),  # az
        )

    def _read_data(self):
        return self._read_register(b"\x00")

    def _read_register(self, address):
        with self.i2c_device as i2c:
            i2c.write(address)
            time.sleep(self._i2c_read_delay)  # at least 200us
            i2c.readinto(self.buffer)
        return self.buffer
