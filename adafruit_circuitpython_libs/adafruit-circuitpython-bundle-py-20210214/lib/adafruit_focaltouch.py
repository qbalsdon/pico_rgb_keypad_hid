# SPDX-FileCopyrightText: 2017 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_focaltouch`
====================================================

CircuitPython driver for common low-cost FocalTech capacitive touch chips.
Currently supports FT6206 & FT6236.

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* Adafruit `2.8" TFT LCD with Cap Touch Breakout Board w/MicroSD Socket
  <http://www.adafruit.com/product/2090>`_ (Product ID: 2090)

* Adafruit `2.8" TFT Touch Shield for Arduino w/Capacitive Touch
  <http://www.adafruit.com/product/1947>`_ (Product ID: 1947)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library (when using I2C/SPI):
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# imports

__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FocalTouch.git"

try:
    import struct
except ImportError:
    import ustruct as struct

from adafruit_bus_device.i2c_device import I2CDevice

from micropython import const


_FT6206_DEFAULT_I2C_ADDR = 0x38

_FT6XXX_REG_DATA = const(0x00)
_FT6XXX_REG_NUMTOUCHES = const(0x02)
_FT6XXX_REG_THRESHHOLD = const(0x80)
_FT6XXX_REG_POINTRATE = const(0x88)
_FT6XXX_REG_LIBH = const(0xA1)
_FT6XXX_REG_LIBL = const(0xA2)
_FT6XXX_REG_CHIPID = const(0xA3)
_FT6XXX_REG_FIRMVERS = const(0xA6)
_FT6XXX_REG_VENDID = const(0xA8)
_FT6XXX_REG_RELEASE = const(0xAF)


class Adafruit_FocalTouch:
    """
    A driver for the FocalTech capacitive touch sensor.
    """

    _debug = False
    chip = None

    def __init__(
        self, i2c, address=_FT6206_DEFAULT_I2C_ADDR, debug=False, irq_pin=None
    ):
        self._i2c = I2CDevice(i2c, address)
        self._debug = debug
        self._irq_pin = irq_pin

        chip_data = self._read(_FT6XXX_REG_LIBH, 8)  # don't wait for IRQ
        lib_ver, chip_id, _, _, firm_id, _, vend_id = struct.unpack(
            ">HBBBBBB", chip_data
        )

        if vend_id != 0x11:
            raise RuntimeError("Did not find FT chip")

        if chip_id == 0x06:
            self.chip = "FT6206"
        elif chip_id == 0x64:
            self.chip = "FT6236"

        if debug:
            print("Library vers %04X" % lib_ver)
            print("Firmware ID %02X" % firm_id)
            print("Point rate %d Hz" % self._read(_FT6XXX_REG_POINTRATE, 1)[0])
            print("Thresh %d" % self._read(_FT6XXX_REG_THRESHHOLD, 1)[0])

    @property
    def touched(self):
        """ Returns the number of touches currently detected """
        return self._read(_FT6XXX_REG_NUMTOUCHES, 1, irq_pin=self._irq_pin)[0]

    # pylint: disable=unused-variable
    @property
    def touches(self):
        """
        Returns a list of touchpoint dicts, with 'x' and 'y' containing the
        touch coordinates, and 'id' as the touch # for multitouch tracking
        """
        touchpoints = []
        data = self._read(_FT6XXX_REG_DATA, 32, irq_pin=self._irq_pin)

        for i in range(2):
            point_data = data[i * 6 + 3 : i * 6 + 9]
            if all([i == 0xFF for i in point_data]):
                continue
            # print([hex(i) for i in point_data])
            x, y, weight, misc = struct.unpack(">HHBB", point_data)
            # print(x, y, weight, misc)
            touch_id = y >> 12
            x &= 0xFFF
            y &= 0xFFF
            point = {"x": x, "y": y, "id": touch_id}
            touchpoints.append(point)
        return touchpoints

    # pylint: enable=unused-variable

    def _read(self, register, length, irq_pin=None):
        """Returns an array of 'length' bytes from the 'register'"""
        with self._i2c as i2c:

            if irq_pin is not None:
                while irq_pin.value:
                    pass

            i2c.write(bytes([register & 0xFF]))
            result = bytearray(length)

            i2c.readinto(result)
            if self._debug:
                print("\t$%02X => %s" % (register, [hex(i) for i in result]))
            return result

    def _write(self, register, values):
        """Writes an array of 'length' bytes to the 'register'"""
        with self._i2c as i2c:
            values = [(v & 0xFF) for v in [register] + values]
            i2c.write(bytes(values))
            if self._debug:
                print("\t$%02X <= %s" % (values[0], [hex(i) for i in values[1:]]))
