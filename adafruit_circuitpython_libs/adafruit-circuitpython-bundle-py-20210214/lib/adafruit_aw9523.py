# SPDX-FileCopyrightText: Copyright (c) 2021 ladyada for Adafruit
#
# SPDX-License-Identifier: MIT
"""
`adafruit_aw9523`
================================================================================

Python library for AW9523 GPIO expander and LED driver


* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* Adafruit AW9523 Breakout https://www.adafruit.com/product/4886

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

import digitalio
import adafruit_bus_device.i2c_device as i2c_device
from adafruit_register.i2c_struct import ROUnaryStruct, UnaryStruct
from adafruit_register.i2c_bit import RWBit
from micropython import const

__version__ = "1.0.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_AW9523.git"

_AW9523_DEFAULT_ADDR = const(0x58)
_AW9523_REG_CHIPID = const(0x10)  # Register for hardcode chip ID
_AW9523_REG_SOFTRESET = const(0x7F)  # Register for soft resetting
_AW9523_REG_INPUT0 = const(0x00)  # Register for reading input values
_AW9523_REG_OUTPUT0 = const(0x02)  # Register for writing output values
_AW9523_REG_CONFIG0 = const(0x04)  # Register for configuring direction
_AW9523_REG_INTENABLE0 = const(0x06)  # Register for enabling interrupt
_AW9523_REG_GCR = const(0x11)  # Register for general configuration
_AW9523_REG_LEDMODE = const(0x12)  # Register for configuring const current

# pylint: disable=invalid-name


class AW9523:
    """CircuitPython helper class for using the AW9523 GPIO expander"""

    _chip_id = ROUnaryStruct(_AW9523_REG_CHIPID, "<B")
    _reset_reg = UnaryStruct(_AW9523_REG_SOFTRESET, "<B")

    # Set all 16 gpio outputs
    outputs = UnaryStruct(_AW9523_REG_OUTPUT0, "<H")
    # Read all 16 gpio inputs
    inputs = UnaryStruct(_AW9523_REG_INPUT0, "<H")
    # Set all 16 gpio interrupt enable
    _interrupt_enables = UnaryStruct(_AW9523_REG_INTENABLE0, "<H")
    # Set all 16 gpio directions
    _directions = UnaryStruct(_AW9523_REG_CONFIG0, "<H")
    # Set all 16 gpio LED modes
    _LED_modes = UnaryStruct(_AW9523_REG_LEDMODE, "<H")

    # Whether port 0 is push-pull
    port0_push_pull = RWBit(_AW9523_REG_GCR, 4)

    def __init__(self, i2c_bus, address=_AW9523_DEFAULT_ADDR, reset=True):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._buffer = bytearray(2)
        if self._chip_id != 0x23:
            raise AttributeError("Cannot find a AW9523")
        if reset:
            self.reset()
            self.port0_push_pull = True  # pushpull output
            self.interrupt_enables = 0x0000  # no IRQ
            self.directions = 0x0000  # all inputs!

    def reset(self):
        """Perform a soft reset, check datasheets for post-reset defaults!"""
        self._reset_reg = 0

    def set_constant_current(self, pin, value):
        """
        Set the constant current drain for an AW9523 pin
        :param int pin: pin to set constant current, 0..15
        :param int value: the value ranging from 0 (off) to 255 (max current)
        """
        # See Table 13. 256 step dimming control register
        if 0 <= pin <= 7:
            self._buffer[0] = 0x24 + pin
        elif 8 <= pin <= 11:
            self._buffer[0] = 0x20 + pin - 8
        elif 12 <= pin <= 15:
            self._buffer[0] = 0x2C + pin - 12
        else:
            raise ValueError("Pin must be 0 to 15")

        # set value
        if not 0 <= value <= 255:
            raise ValueError("Value must be 0 to 255")
        self._buffer[1] = value
        with self.i2c_device as i2c:
            i2c.write(self._buffer)

    def get_pin(self, pin):
        """Convenience function to create an instance of the DigitalInOut class
        pointing at the specified pin of this AW9523 device.
        :param int pin: pin to use for digital IO, 0 to 15
        """
        assert 0 <= pin <= 15
        return DigitalInOut(pin, self)

    @property
    def interrupt_enables(self):
        """Enables interrupt for input pin change if bit mask is 1"""
        return ~self._interrupt_enables & 0xFFFF

    @interrupt_enables.setter
    def interrupt_enables(self, enables):
        self._interrupt_enables = ~enables & 0xFFFF

    @property
    def directions(self):
        """Direction is output if bit mask is 1, input if bit is 0"""
        return ~self._directions & 0xFFFF

    @directions.setter
    def directions(self, dirs):
        self._directions = (~dirs) & 0xFFFF

    @property
    def LED_modes(self):
        """Pin is set up for constant current mode if bit mask is 1"""
        return ~self._LED_modes & 0xFFFF

    @LED_modes.setter
    def LED_modes(self, modes):
        self._LED_modes = ~modes & 0xFFFF


# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2019 Carter Nelson
#
# SPDX-License-Identifier: MIT

"""
`digital_inout`
====================================================

Digital input/output of the MCP230xx.

* Author(s): Tony DiCola
"""

# Internal helpers to simplify setting and getting a bit inside an integer.
def _get_bit(val, bit):
    return val & (1 << bit) > 0


def _enable_bit(val, bit):
    return val | (1 << bit)


def _clear_bit(val, bit):
    return val & ~(1 << bit)


class DigitalInOut:
    """Digital input/output of the AW9523.  The interface is exactly the
    same as the digitalio.DigitalInOut class, however:

      * AW9523 family does not support pull-up or -down resistors

    Exceptions will be thrown when attempting to set unsupported pull
    configurations.
    """

    def __init__(self, pin_number, aw):
        """Specify the pin number of the AW9523 0..15, and instance."""
        self._pin = pin_number
        self._aw = aw

    # kwargs in switch functions below are _necessary_ for compatibility
    # with DigitalInout class (which allows specifying pull, etc. which
    # is unused by this class).  Do not remove them, instead turn off pylint
    # in this case.
    # pylint: disable=unused-argument
    def switch_to_output(self, value=False, **kwargs):
        """Switch the pin state to a digital output with the provided starting
        value (True/False for high or low, default is False/low).
        """
        self.direction = digitalio.Direction.OUTPUT
        self.value = value

    def switch_to_input(self, pull=None, **kwargs):
        """Switch the pin state to a digital input with the provided starting
        pull-up resistor state (optional, no pull-up by default) and input polarity.  Note that
        pull-down resistors are NOT supported!
        """
        self.direction = digitalio.Direction.INPUT
        self.pull = pull

    # pylint: enable=unused-argument

    @property
    def value(self):
        """The value of the pin, either True for high or False for
        low.  Note you must configure as an output or input appropriately
        before reading and writing this value.
        """
        return _get_bit(self._aw.inputs, self._pin)

    @value.setter
    def value(self, val):
        if val:
            self._aw.outputs = _enable_bit(self._aw.outputs, self._pin)
        else:
            self._aw.outputs = _clear_bit(self._aw.outputs, self._pin)

    @property
    def direction(self):
        """The direction of the pin, either True for an input or
        False for an output.
        """
        if _get_bit(self._aw.direction, self._pin):
            return digitalio.Direction.INPUT
        return digitalio.Direction.OUTPUT

    @direction.setter
    def direction(self, val):
        if val == digitalio.Direction.INPUT:
            self._aw.directions = _clear_bit(self._aw.directions, self._pin)

        elif val == digitalio.Direction.OUTPUT:
            self._aw.directions = _enable_bit(self._aw.directions, self._pin)
        else:
            raise ValueError("Expected INPUT or OUTPUT direction!")

    @property
    def pull(self):
        """
        Pull-down resistors are NOT supported!
        """
        raise NotImplementedError("Pull-up/pull-down resistors not supported.")

    @pull.setter
    def pull(self, val):  # pylint: disable=no-self-use
        if val is not None:
            raise NotImplementedError("Pull-up/pull-down resistors not supported.")
