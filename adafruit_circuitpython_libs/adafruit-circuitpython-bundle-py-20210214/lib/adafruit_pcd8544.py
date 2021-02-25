# SPDX-FileCopyrightText: 2018 Tony DiCola for Adafruit Industries
# SPDX-FileCopyrightText: 2018 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_pcd8544`
====================================================

A display control library for Nokia 5110 PCD8544 monochrome displays

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* `Nokia 5110 PCD8544 Display <https://www.adafruit.com/product/338>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

import time
from micropython import const
from adafruit_bus_device import spi_device

try:
    import framebuf
except ImportError:
    import adafruit_framebuf as framebuf

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_PCD8544.git"

_LCDWIDTH = const(84)
_LCDHEIGHT = const(48)
_PCD8544_POWERDOWN = const(0x04)
_PCD8544_ENTRYMODE = const(0x02)
_PCD8544_EXTENDEDINSTRUCTION = const(0x01)
_PCD8544_DISPLAYBLANK = const(0x0)
_PCD8544_DISPLAYNORMAL = const(0x4)
_PCD8544_DISPLAYALLON = const(0x1)
_PCD8544_DISPLAYINVERTED = const(0x5)
_PCD8544_FUNCTIONSET = const(0x20)
_PCD8544_DISPLAYCONTROL = const(0x08)
_PCD8544_SETYADDR = const(0x40)
_PCD8544_SETXADDR = const(0x80)
_PCD8544_SETTEMP = const(0x04)
_PCD8544_SETBIAS = const(0x10)
_PCD8544_SETVOP = const(0x80)


class PCD8544(framebuf.FrameBuffer):
    """Nokia 5110/3310 PCD8544-based LCD display."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        spi,
        dc_pin,
        cs_pin,
        reset_pin=None,
        *,
        contrast=80,
        bias=4,
        baudrate=1000000
    ):
        self._dc_pin = dc_pin
        dc_pin.switch_to_output(value=False)

        self.spi_device = spi_device.SPIDevice(spi, cs_pin, baudrate=baudrate)

        self._reset_pin = reset_pin
        if reset_pin:
            reset_pin.switch_to_output(value=True)

        self.buffer = bytearray((_LCDHEIGHT // 8) * _LCDWIDTH)
        super().__init__(self.buffer, _LCDWIDTH, _LCDHEIGHT)

        self._contrast = None
        self._bias = None
        self._invert = False

        self.reset()
        # Set LCD bias.
        self.bias = bias
        self.contrast = contrast

    def reset(self):
        """Reset the display"""
        if self._reset_pin:
            # Toggle RST low to reset.
            self._reset_pin.value = False
            time.sleep(0.5)
            self._reset_pin.value = True
            time.sleep(0.5)

    def write_cmd(self, cmd):
        """Send a command to the SPI device"""
        self._dc_pin.value = 0
        with self.spi_device as spi:
            spi.write(bytearray([cmd]))  # pylint: disable=no-member

    def extended_command(self, cmd):
        """Send a command in extended mode"""
        # Set extended command mode
        self.write_cmd(_PCD8544_FUNCTIONSET | _PCD8544_EXTENDEDINSTRUCTION)
        self.write_cmd(cmd)
        # Set normal display mode.
        self.write_cmd(_PCD8544_FUNCTIONSET)
        self.write_cmd(_PCD8544_DISPLAYCONTROL | _PCD8544_DISPLAYNORMAL)

    def show(self):
        """write out the frame buffer via SPI"""
        self.write_cmd(_PCD8544_SETYADDR)
        self.write_cmd(_PCD8544_SETXADDR)
        self._dc_pin.value = True
        with self.spi_device as spi:
            spi.write(self.buffer)  # pylint: disable=no-member

    @property
    def invert(self):
        """Whether the display is inverted, cached value"""
        return self._invert

    @invert.setter
    def invert(self, val):
        """Set invert on or normal display on"""
        self._invert = val
        self.write_cmd(_PCD8544_FUNCTIONSET)
        if val:
            self.write_cmd(_PCD8544_DISPLAYCONTROL | _PCD8544_DISPLAYINVERTED)
        else:
            self.write_cmd(_PCD8544_DISPLAYCONTROL | _PCD8544_DISPLAYNORMAL)

    @property
    def contrast(self):
        """The cached contrast value"""
        return self._contrast

    @contrast.setter
    def contrast(self, val):
        """Set contrast to specified value (should be 0-127)."""
        self._contrast = max(0, min(val, 0x7F))  # Clamp to values 0-0x7f
        self.extended_command(_PCD8544_SETVOP | self._contrast)

    @property
    def bias(self):
        """The cached bias value"""
        return self._bias

    @bias.setter
    def bias(self, val):
        """Set display bias"""
        self._bias = val
        self.extended_command(_PCD8544_SETBIAS | self._bias)
