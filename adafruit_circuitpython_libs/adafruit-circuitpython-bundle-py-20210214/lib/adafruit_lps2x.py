# The MIT License (MIT)
#
# Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
`adafruit_lps2x`
================================================================================

Library for the ST LPS2X family of pressure sensors

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* LPS25HB Breakout https://www.adafruit.com/products/4530

**Software and Dependencies:**
 * Adafruit CircuitPython firmware for the supported boards:
    https://circuitpythohn.org/downloads
 * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
 * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register

"""
__version__ = "2.0.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LPS2X.git"
from time import sleep
from micropython import const
import adafruit_bus_device.i2c_device as i2cdevice
from adafruit_register.i2c_struct import ROUnaryStruct
from adafruit_register.i2c_bits import RWBits, ROBits
from adafruit_register.i2c_bit import RWBit

# _LPS2X_I2CADDR_DEFAULT = 0x5D # LPS2X default i2c address
# _LPS2X_WHOAMI = 0x0F          # Chip ID register
# _LPS2X_PRESS_OUT_XL =(# | 0x80) ///< | 0x80 to set auto increment on multi-byte read
# _LPS2X_TEMP_OUT_L =  (0x2B # 0x80) ///< | 0x80 to set auto increment on
_LPS2X_WHO_AM_I = const(0x0F)
_LPS2X_PRESS_OUT_XL = const(
    0x28 | 0x80
)  # | 0x80 to set auto increment on multi-byte read
_LPS2X_TEMP_OUT_L = const(
    0x2B | 0x80
)  # | 0x80 to set auto increment on multi-byte read

_LPS25_CTRL_REG1 = const(0x20)  # First control register. Includes BD & ODR
_LPS25_CTRL_REG2 = const(0x21)  # Second control register. Includes SW Reset
# _LPS25_CTRL_REG3 = 0x22 # Third control register. Includes interrupt polarity
# _LPS25_CTRL_REG4 = 0x23 # Fourth control register. Includes DRDY INT control
# _LPS25_INTERRUPT_CFG = 0x24 # Interrupt control register
# _LPS25_THS_P_L_REG = 0xB0   # Pressure threshold value for int


# _LPS22_THS_P_L_REG = 0x0C # Pressure threshold value for int
_LPS22_CTRL_REG1 = 0x10  # First control register. Includes BD & ODR
_LPS22_CTRL_REG2 = 0x11  # Second control register. Includes SW Reset
# _LPS22_CTRL_REG3 = 0x12 # Third control register. Includes interrupt polarity

_LPS2X_DEFAULT_ADDRESS = 0x5D
_LPS25HB_CHIP_ID = 0xBD
_LPS22HB_CHIP_ID = 0xB1  # LPS22 default device id from WHOAMI


class CV:
    """struct helper"""

    @classmethod
    def add_values(cls, value_tuples):
        "creates CV entires"
        cls.string = {}
        cls.lsb = {}

        for value_tuple in value_tuples:
            name, value, string, lsb = value_tuple
            setattr(cls, name, value)
            cls.string[value] = string
            cls.lsb[value] = lsb

    @classmethod
    def is_valid(cls, value):
        "Returns true if the given value is a member of the CV"
        return value in cls.string


class Rate(CV):
    """Options for ``data_rate``

    +-----------------------------+------------------------------------------------+
    | Rate                        | Description                                    |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP25_SHUTDOWN``     | Setting `data_rate` to ``Rate.LSP25_SHUTDOWN`` |
    |                             | stops measurements from being taken            |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP25_RATE_1_HZ``    | 1 Hz                                           |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP25_RATE_7_HZ``    | 7 Hz                                           |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP25_RATE_12_5_HZ`` | 12.5 Hz                                        |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP25_RATE_25_HZ``   | 25 Hz                                          |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP22_SHUTDOWN``     | Setting `data_rate` to ``Rate.LSP22_SHUTDOWN`` |
    |                             | stops measurements from being taken            |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP22_RATE_1_HZ``    | 1 Hz                                           |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP22_RATE_10_HZ``   | 10 Hz                                          |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP22_RATE_25_HZ``   | 25 Hz                                          |
    +-----------------------------+------------------------------------------------+
    | ``Rate.LSP22_RATE_50_HZ``   | 50 Hz                                          |
    +-----------------------------+------------------------------------------------+

    """

    pass  # pylint: disable=unnecessary-pass


class LPS2X:  # pylint: disable=too-many-instance-attributes
    """Base class ST LPS2x family of pressure sensors

        :param ~busio.I2C i2c_bus: The I2C bus the sensor is connected to.
        :param address: The I2C device address for the sensor. Default is ``0x5d`` but will accept
            ``0x5c`` when the ``SDO`` pin is connected to Ground.

    """

    _chip_id = ROUnaryStruct(_LPS2X_WHO_AM_I, "<B")
    _raw_temperature = ROUnaryStruct(_LPS2X_TEMP_OUT_L, "<h")
    _raw_pressure = ROBits(24, _LPS2X_PRESS_OUT_XL, 0, 3)

    def __init__(self, i2c_bus, address=_LPS2X_DEFAULT_ADDRESS, chip_id=None):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)
        if not self._chip_id in [chip_id]:
            raise RuntimeError(
                "Failed to find LPS2X! Found chip ID 0x%x" % self._chip_id
            )
        self.reset()
        self.initialize()
        sleep(0.010)  # delay 10ms for first reading

    def initialize(self):  # pylint: disable=no-self-use
        """Configure the sensor with the default settings. For use after calling `reset()`"""
        raise RuntimeError(
            "LPS2X Base class cannot be instantiated directly. Use LPS22 or LPS25 instead"
        )  # override in subclass

    def reset(self):
        """Reset the sensor, restoring all configuration registers to their defaults"""
        self._reset = True
        # wait for the reset to finish
        while self._reset:
            pass

    @property
    def pressure(self):
        """The current pressure measurement in hPa"""
        raw = self._raw_pressure

        if raw & (1 << 23) != 0:
            raw = raw - (1 << 24)
        return raw / 4096.0

    @property
    def temperature(self):
        """The current temperature measurement in degrees C"""

        raw_temperature = self._raw_temperature
        return (
            raw_temperature / self._temp_scaling  # pylint:disable=no-member
        ) + self._temp_offset  # pylint:disable=no-member

    @property
    def data_rate(self):
        """The rate at which the sensor measures ``pressure`` and ``temperature``. ``data_rate``
        shouldbe set to one of the values of ``adafruit_lps2x.Rate``."""
        return self._data_rate

    @data_rate.setter
    def data_rate(self, value):
        if not Rate.is_valid(value):
            raise AttributeError("data_rate must be a `Rate`")

        self._data_rate = value


class LPS25(LPS2X):
    """Library for the ST LPS25 pressure sensors

        :param ~busio.I2C i2c_bus: The I2C bus the LPS25HB is connected to.
        :param address: The I2C device address for the sensor. Default is ``0x5d`` but will accept
            ``0x5c`` when the ``SDO`` pin is connected to Ground.

    """

    enabled = RWBit(_LPS25_CTRL_REG1, 7)
    """Controls the power down state of the sensor. Setting to `False` will shut the sensor down"""
    _reset = RWBit(_LPS25_CTRL_REG2, 2)
    _data_rate = RWBits(3, _LPS25_CTRL_REG1, 4)

    def __init__(self, i2c_bus, address=_LPS2X_DEFAULT_ADDRESS):

        Rate.add_values(
            (
                ("LPS25_RATE_ONE_SHOT", 0, 0, None),
                ("LPS25_RATE_1_HZ", 1, 1, None),
                ("LPS25_RATE_7_HZ", 2, 7, None),
                ("LPS25_RATE_12_5_HZ", 3, 12.5, None),
                ("LPS25_RATE_25_HZ", 4, 25, None),
            )
        )
        super().__init__(i2c_bus, address, chip_id=_LPS25HB_CHIP_ID)

        self._temp_scaling = 480
        self._temp_offset = 42.5
        # self._inc_spi_flag = 0x40

    def initialize(self):
        """Configure the sensor with the default settings. For use after calling `reset()`"""
        self.enabled = True
        self.data_rate = Rate.LPS25_RATE_25_HZ  # pylint:disable=no-member

    # void configureInterrupt(bool activelow, bool opendrain,
    #                       bool pres_high = false, bool pres_low = false);


class LPS22(LPS2X):
    """Library for the ST LPS22 pressure sensors

        :param ~busio.I2C i2c_bus: The I2C bus the LPS22HB is connected to.
        :param address: The I2C device address for the sensor. Default is ``0x5d`` but will accept
            ``0x5c`` when the ``SDO`` pin is connected to Ground.

    """

    _reset = RWBit(_LPS22_CTRL_REG2, 2)
    _data_rate = RWBits(3, _LPS22_CTRL_REG1, 4)

    def __init__(self, i2c_bus, address=_LPS2X_DEFAULT_ADDRESS):
        # Only adding Class-appropriate rates
        Rate.add_values(
            (
                ("LPS22_RATE_ONE_SHOT", 0, 0, None),
                ("LPS22_RATE_1_HZ", 1, 1, None),
                ("LPS22_RATE_10_HZ", 2, 10, None),
                ("LPS22_RATE_25_HZ", 3, 25, None),
                ("LPS22_RATE_50_HZ", 4, 50, None),
                ("LPS22_RATE_75_HZ", 5, 75, None),
            )
        )

        super().__init__(i2c_bus, address, chip_id=_LPS22HB_CHIP_ID)
        self._temp_scaling = 100
        self._temp_offset = 0

    def initialize(self):
        """Configure the sensor with the default settings. For use after calling `reset()`"""
        self.data_rate = Rate.LPS22_RATE_75_HZ  # pylint:disable=no-member

    # void configureInterrupt(bool activelow, bool opendrain, bool data_ready,
    #                         bool pres_high = false, bool pres_low = false,
    #                         bool fifo_full = false, bool fifo_watermark = false,
    #                         bool fifo_overflow = false);
