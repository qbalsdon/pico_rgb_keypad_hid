# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_max9744`
====================================================

CircuitPython module for the MAX9744 20W class D amplifier.  See
examples/simpletest.py for a demo of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `MAX9744 Stereo 20W Class D Audio Amplifier
  <https://www.adafruit.com/product/1752>`_ (Product ID: 1752)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
"""
from micropython import const

__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MAX9744.git"


# Internal constants:
_MAX9744_DEFAULT_ADDRESS = const(0b01001011)
_MAX9744_COMMAND_VOLUME = const(0b00000000)
_MAX9744_COMMAND_FILTERLESS = const(0b01000000)
_MAX9744_COMMAND_CLASSIC_PWM = const(0b01000001)
_MAX9744_COMMAND_VOLUME_UP = const(0b11000100)
_MAX9744_COMMAND_VOLUME_DOWN = const(0b11000101)


class MAX9744:
    """MAX9744 20 watt class D amplifier.

    :param i2c: The I2C bus for the device.

    :param address: (Optional) The address of the device if it has been overridden from the
                    default with the AD1, AD2 pins.
    """

    # Global buffer for writing data.  This saves memory use and prevents
    # heap fragmentation.  However this is not thread-safe or re-entrant by
    # design!
    _BUFFER = bytearray(1)

    def __init__(self, i2c, *, address=_MAX9744_DEFAULT_ADDRESS):
        # This device doesn't use registers and instead just accepts a single
        # command string over I2C.  As a result we don't use bus device or
        # other abstractions and just talk raw I2C protocol.
        self._i2c = i2c
        self._address = address

    def _write(self, val):
        # Perform a write to update the amplifier state.
        try:
            # Make sure bus is locked before write.
            while not self._i2c.try_lock():
                pass
            # Build bytes to send to device with updated value.
            self._BUFFER[0] = val & 0xFF
            self._i2c.writeto(self._address, self._BUFFER)
        finally:
            # Ensure bus is always unlocked.
            self._i2c.unlock()

    def _set_volume(self, volume):
        # Set the volume to the specified level (0-63).
        assert 0 <= volume <= 63
        self._write(_MAX9744_COMMAND_VOLUME | (volume & 0x3F))

    # pylint: disable=line-too-long
    volume = property(
        None,
        _set_volume,
        "Set the volume of the amplifier.  Specify a value from 0-63 where 0 is muted/off and 63 is maximum volume.",
    )
    # pylint: enable=line-too-long

    def volume_up(self):
        """Increase the volume by one level."""
        self._write(_MAX9744_COMMAND_VOLUME_UP)

    def volume_down(self):
        """Decrease the volume by one level."""
        self._write(_MAX9744_COMMAND_VOLUME_DOWN)
