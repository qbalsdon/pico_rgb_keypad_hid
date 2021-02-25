# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ltr390`
================================================================================

Adafruit CircuitPython library for the LTR390


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit LTR390 Breakout <https://www.adafruit.com/product/38XX>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

from time import sleep
from struct import unpack_from, pack_into
from micropython import const
import adafruit_bus_device.i2c_device as i2c_device
from adafruit_register.i2c_struct import ROUnaryStruct, Struct
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_bit import RWBit, ROBit

__version__ = "1.0.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_LTR390.git"

_DEFAULT_I2C_ADDR = const(0x53)
_CTRL = const(0x00)  # Main control register
_MEAS_RATE = const(0x04)  # Resolution and data rate
_GAIN = const(0x05)  # ALS and UVS gain range
_PART_ID = const(0x06)  # Part id/revision register
_STATUS = const(0x07)  # Main status register
_ALSDATA = const(0x0D)  # ALS data lowest byte
_UVSDATA = const(0x10)  # UVS data lowest byte
_INT_CFG = const(0x19)  # Interrupt configuration
_INT_PST = const(0x1A)  # Interrupt persistance config
_THRESH_UP = const(0x21)  # Upper threshold, low byte
_THRESH_LOW = const(0x24)  # Lower threshold, low byte

ALS = 0
UV = 1


class UnalignedStruct(Struct):
    """Class for reading multi-byte data registers with a data length less than the full bitwidth
    of the registers. Most registers of this sort are left aligned to preserve the sign bit"""

    def __init__(self, register_address, struct_format, bitwidth, length):
        super().__init__(register_address, struct_format)
        self._width = bitwidth
        self._num_bytes = length

    def __get__(self, obj, objtype=None):
        # read bytes into buffer at correct alignment
        raw_value = unpack_from(self.format, self.buffer, offset=1)[0]

        with obj.i2c_device as i2c:
            i2c.write_then_readinto(
                self.buffer,
                self.buffer,
                out_start=0,
                out_end=1,
                in_start=2,  # right aligned
                # in_end=4 # right aligned
            )
        raw_value = unpack_from(self.format, self.buffer, offset=1)[0]
        return raw_value >> 8

    def __set__(self, obj, value):
        pack_into(self.format, self.buffer, 1, value)
        with obj.i2c_device as i2c:
            i2c.write(self.buffer)


class CV:
    """struct helper"""

    @classmethod
    def add_values(cls, value_tuples):
        """Add CV values to the class"""
        cls.string = {}
        cls.lsb = {}

        for value_tuple in value_tuples:
            name, value, string, lsb = value_tuple
            setattr(cls, name, value)
            cls.string[value] = string
            cls.lsb[value] = lsb

    @classmethod
    def is_valid(cls, value):
        """Validate that a given value is a member"""
        return value in cls.string


class Gain(CV):
    """Options for `gain`

    +---------------------------+----------------------------+
    | Gain                      | Raw Measurement Multiplier |
    +===========================+============================+
    | :py:const:`Gain.GAIN_1X`  | 1                          |
    +---------------------------+----------------------------+
    | :py:const:`Gain.GAIN_3X`  | 3                          |
    +---------------------------+----------------------------+
    | :py:const:`Gain.GAIN_6X`  | 6                          |
    +---------------------------+----------------------------+
    | :py:const:`Gain.GAIN_9X`  | 9                          |
    +---------------------------+----------------------------+
    | :py:const:`Gain.GAIN_18X` | 18                         |
    +---------------------------+----------------------------+

    """


Gain.add_values(
    (
        ("GAIN_1X", 0, "1X", None),
        ("GAIN_3X", 1, "3X", None),
        ("GAIN_6X", 2, "6X", None),
        ("GAIN_9X", 3, "9X", None),
        ("GAIN_18X", 4, "18X", None),
    )
)


class Resolution(CV):
    """Options for `resolution`

    +-----------------------------------------+-------------------------+
    | Resolution                              | Internal ADC Resolution |
    +=========================================+=========================+
    | :py:const:`Resolution.RESOLUTION_13BIT` | 13 bits                 |
    +-----------------------------------------+-------------------------+
    | :py:const:`Resolution.RESOLUTION_16BIT` | 16 bits                 |
    +-----------------------------------------+-------------------------+
    | :py:const:`Resolution.RESOLUTION_17BIT` | 17 bits                 |
    +-----------------------------------------+-------------------------+
    | :py:const:`Resolution.RESOLUTION_18BIT` | 18 bits                 |
    +-----------------------------------------+-------------------------+
    | :py:const:`Resolution.RESOLUTION_19BIT` | 19 bits                 |
    +-----------------------------------------+-------------------------+
    | :py:const:`Resolution.RESOLUTION_20BIT` | 20 bits                 |
    +-----------------------------------------+-------------------------+

    """


Resolution.add_values(
    (
        ("RESOLUTION_20BIT", 0, "20 bits", None),
        ("RESOLUTION_19BIT", 1, "19 bits", None),
        ("RESOLUTION_18BIT", 2, "18 bits", None),
        ("RESOLUTION_17BIT", 3, "17 bits", None),
        ("RESOLUTION_16BIT", 4, "16 bits", None),
        ("RESOLUTION_13BIT", 5, "13 bits", None),
    )
)


class MeasurementDelay(CV):
    """Options for `measurement_delay`

    +-------------------------------------------+--------------------------------------+
    | MeasurementDelay                          | Time Between Measurement Cycles (ms) |
    +===========================================+======================================+
    | :py:const:`MeasurementDelay.DELAY_25MS`   | 25                                   |
    +-------------------------------------------+--------------------------------------+
    | :py:const:`MeasurementDelay.DELAY_50MS`   | 50                                   |
    +-------------------------------------------+--------------------------------------+
    | :py:const:`MeasurementDelay.DELAY_100MS`  | 100                                  |
    +-------------------------------------------+--------------------------------------+
    | :py:const:`MeasurementDelay.DELAY_200MS`  | 200                                  |
    +-------------------------------------------+--------------------------------------+
    | :py:const:`MeasurementDelay.DELAY_500MS`  | 500                                  |
    +-------------------------------------------+--------------------------------------+
    | :py:const:`MeasurementDelay.DELAY_1000MS` | 1000                                 |
    +-------------------------------------------+--------------------------------------+
    | :py:const:`MeasurementDelay.DELAY_2000MS` | 2000                                 |
    +-------------------------------------------+--------------------------------------+

    """


MeasurementDelay.add_values(
    (
        ("DELAY_25MS", 0, "25", None),
        ("DELAY_50MS", 1, "50", None),
        ("DELAY_100MS", 2, "100", None),
        ("DELAY_200MS", 3, "200", None),
        ("DELAY_500MS", 4, "500", None),
        ("DELAY_1000MS", 5, "1000", None),
        ("DELAY_2000MS", 6, "2000", None),
    )
)


class LTR390:  # pylint:disable=too-many-instance-attributes
    """Class to use the LTR390 Ambient Light and UV sensor"""

    _reset_bit = RWBit(_CTRL, 4)
    _enable_bit = RWBit(_CTRL, 1)
    _mode_bit = RWBit(_CTRL, 3)
    _int_enable_bit = RWBit(_INT_CFG, 2)

    _gain_bits = RWBits(3, _GAIN, 0)
    _resolution_bits = RWBits(3, _MEAS_RATE, 4)
    _measurement_delay_bits = RWBits(3, _MEAS_RATE, 0)
    _rate_bits = RWBits(3, _MEAS_RATE, 4)
    _int_src_bits = RWBits(2, _INT_CFG, 4)
    _int_persistance_bits = RWBits(4, _INT_PST, 4)

    _id_reg = ROUnaryStruct(_PART_ID, "<B")
    _uvs_data_reg = UnalignedStruct(_UVSDATA, "<I", 24, 3)
    _als_data_reg = UnalignedStruct(_ALSDATA, "<I", 24, 3)

    data_ready = ROBit(_STATUS, 3)
    """Ask the sensor if new data is available"""
    high_threshold = UnalignedStruct(_THRESH_UP, "<I", 24, 3)
    """When the measured value is more than the low_threshold, the sensor will raise an alert"""

    low_threshold = UnalignedStruct(_THRESH_LOW, "<I", 24, 3)
    """When the measured value is less than the low_threshold, the sensor will raise an alert"""

    threshold_passed = ROBit(_STATUS, 4)
    """The status of any configured alert. If True, a threshold has been passed.

    Once read, this property will be False until it is updated in the next measurement cycle"""

    def __init__(self, i2c, address=_DEFAULT_I2C_ADDR):
        self.i2c_device = i2c_device.I2CDevice(i2c, address)
        if self._id_reg != 0xB2:

            raise RuntimeError("Unable to find LTR390; check your wiring")

        self._mode_cache = None
        self.initialize()

    def initialize(self):
        """Reset the sensor to it's initial unconfigured state and configure it with sensible
        defaults so it can be used"""

        self._reset()
        self._enable_bit = True
        if not self._enable_bit:
            raise RuntimeError("Unable to enable sensor")
        self._mode = UV
        self.gain = Gain.GAIN_3X  # pylint:disable=no-member
        self.resolution = Resolution.RESOLUTION_16BIT  # pylint:disable=no-member

        # ltr.setThresholds(100, 1000);
        # self.low_threshold = 100
        # self.high_threshold = 1000
        # ltr.configInterrupt(true, LTR390_MODE_UVS);

    def _reset(self):
        try:
            self._reset_bit = True
        except OSError:
            # The write to the reset bit will fail because it seems to not ACK before it resets
            pass

        sleep(0.1)
        # check that reset is complete w/ the bit unset
        if self._reset_bit:
            raise RuntimeError("Unable to reset sensor")

    @property
    def _mode(self):
        return self._mode_bit

    @_mode.setter
    def _mode(self, value):
        if not value in [ALS, UV]:
            raise AttributeError("Mode must be ALS or UV")
        if self._mode_cache != value:
            self._mode_bit = value
            self._mode_cache = value
            sleep(0.030)

    # something is wrong here; I had to add a sleep to the loop to get both to update correctly
    @property
    def uvs(self):
        """The calculated UV value"""
        self._mode = UV
        while not self.data_ready:
            sleep(0.010)
        return self._uvs_data_reg

    @property
    def light(self):
        """The currently measured ambient light level"""
        self._mode = ALS
        while not self.data_ready:
            sleep(0.010)
        return self._als_data_reg

    @property
    def gain(self):
        """The amount of gain the raw measurements are multiplied by"""
        return self._gain_bits

    @gain.setter
    def gain(self, value):
        if not Gain.is_valid(value):
            raise AttributeError("gain must be a Gain")
        self._gain_bits = value

    @property
    def resolution(self):
        """Set the precision of the internal ADC used to read the light measurements"""
        return self._resolution_bits

    @resolution.setter
    def resolution(self, value):
        if not Resolution.is_valid(value):
            raise AttributeError("resolution must be a Resolution")
        self._resolution_bits = value

    def enable_alerts(self, enable, source, persistance):
        """The configuraiton of alerts raised by the sensor

        :param enable: Whether the interrupt output is enabled
        :param source: Whether to use the ALS or UVS data register to compare
        :param persistance: The number of consecutive out-of-range readings before
        """
        self._int_enable_bit = enable
        if not enable:
            return
        if source == ALS:
            self._int_src_bits = 1
        elif source == UV:
            self._int_src_bits = 3
        else:
            raise AttributeError("interrupt source must be UV or ALS")
        self._int_persistance_bits = persistance

    @property
    def measurement_delay(self):
        """The delay between measurements. This can be used to set the measurement rate which
        affects the sensors power usage."""
        return self._measurement_delay_bits

    @measurement_delay.setter
    def measurement_delay(self, value):
        if not MeasurementDelay.is_valid(value):
            raise AttributeError("measurement_delay must be a MeasurementDelay")
        self._measurement_delay_bits = value
