# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_tla202x`
================================================================================

Library for the TI TLA202x 12-bit ADCs

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* `Adafruit TLA2024 12-Bit 4-Channel ADC Breakout <https://www.adafruit.com/product/XXXX>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


* `Adafruit's Bus Device library: <https://github.com/adafruit/Adafruit_CircuitPython_BusDevice>`_
* `Adafruit's Register library: <https://github.com/adafruit/Adafruit_CircuitPython_Register>`_
"""

from micropython import const

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_struct import ROUnaryStruct
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_bit import RWBit

__version__ = "1.0.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TLA202x.git"

_TLA_DEFAULT_ADDRESS = const(0x48)
_DATA_REG = const(0x00)
_CONFIG_REG = const(0x01)


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


class DataRate(CV):
    """Options for :py:attr:`~adafruit_tla202x.TLA2024.data_rate`, to select the rate at which
    samples are taken while measuring the voltage across the input pins

    +-------------------------------+-------------------------+
    | Rate                          | Measurement Rate        |
    +===============================+=========================+
    | :py:const:`Rate.RATE_128SPS`  | 128 Samples per second  |
    +-------------------------------+-------------------------+
    | :py:const:`Rate.RATE_250SPS`  | 250 Samples per second  |
    +-------------------------------+-------------------------+
    | :py:const:`Rate.RATE_490SPS`  | 490 Samples per second  |
    +-------------------------------+-------------------------+
    | :py:const:`Rate.RATE_920SPS`  | 920 Samples per second  |
    +-------------------------------+-------------------------+
    | :py:const:`Rate.RATE_1600SPS` | 1600 Samples per second |
    +-------------------------------+-------------------------+
    | :py:const:`Rate.RATE_2400SPS` | 2400 Samples per second |
    +-------------------------------+-------------------------+
    | :py:const:`Rate.RATE_3300SPS` | 3300 Samples per second |
    +-------------------------------+-------------------------+


    """


DataRate.add_values(
    (
        ("RATE_128SPS", 0x0, 128, None),
        ("RATE_250SPS", 0x1, 250, None),
        ("RATE_490SPS", 0x2, 490, None),
        ("RATE_920SPS", 0x3, 920, None),
        ("RATE_1600SPS", 0x4, 1600, None),
        ("RATE_2400SPS", 0x5, 2400, None),
        ("RATE_3300SPS", 0x6, 3300, None),
    )
)


class Mode(CV):
    """Options for :py:attr:`~adafruit_tla202x.TLA2024.mode`

    +----------------------------+--------------------------------------------------------------+
    | Mode                       | Description                                                  |
    +============================+==============================================================+
    | :py:const:`Mode.CONTINUOUS`| In Continuous mode, measurements are taken                   |
    |                            |                                                              |
    |                            | continuously and getting                                     |
    |                            | :py:attr:`~adafruit_tla202x.TLA2024.voltage`                 |
    |                            |                                                              |
    |                            | will return the latest measurement.                          |
    +----------------------------+--------------------------------------------------------------+
    | :py:const:`Mode.ONE_SHOT`  | Setting the mode to :py:data:`~Mode.ONE_SHOT` takes a single |
    |                            |                                                              |
    |                            | measurement and then goes into a low power state.            |
    +----------------------------+--------------------------------------------------------------+

    """


Mode.add_values(
    (("CONTINUOUS", 0, "Continuous", None), ("ONE_SHOT", 1, "One Shot", None),)
)


class Range(CV):
    """Options for :py:attr:`~adafruit_tla202x.TLA2024.range`, used to select the measurement range
    by adjusting the gain of the internal amplifier

    +--------------------------------+-------------------+------------+
    | Range                          | Measurement Range | Resolution |
    +================================+===================+============+
    | :py:const:`Range.RANGE_6_144V` | ±6.144 V          | 3 mV       |
    +--------------------------------+-------------------+------------+
    | :py:const:`Range.RANGE_4_096V` | ±4.096 V          | 2 mV       |
    +--------------------------------+-------------------+------------+
    | :py:const:`Range.RANGE_2_048V` | ±2.048 V          | 1 mV       |
    +--------------------------------+-------------------+------------+
    | :py:const:`Range.RANGE_1_024V` | ±1.024 V          | 0.5 mV     |
    +--------------------------------+-------------------+------------+
    | :py:const:`Range.RANGE_0_512V` | ±0.512 V          | 0.25 mV    |
    +--------------------------------+-------------------+------------+

    """


Range.add_values(
    (
        ("RANGE_6_144V", 0x0, 6.144, 3),
        ("RANGE_4_096V", 0x1, 4.096, 2),
        ("RANGE_2_048V", 0x2, 2.048, 1),
        ("RANGE_1_024V", 0x3, 1.024, 0.5),
        ("RANGE_0_512V", 0x4, 0.512, 0.25),
        ("RANGE_0_256V", 0x5, 0.256, 0.125),
    )
)


class Mux(CV):
    """Options for :py:attr:`~adafruit_tla202x.TLA2024.mux` to choose the inputs that voltage will
    be measured across

    +-------------------------------+--------------+--------------+
    | Mux                           | Positive Pin | Negative Pin |
    +===============================+==============+==============+
    | :py:const:`Mux.MUX_AIN0_AIN1` | AIN 0        | AIN 1        |
    +-------------------------------+--------------+--------------+
    | :py:const:`Mux.MUX_AIN0_AIN3` | AIN 0        | AIN 3        |
    +-------------------------------+--------------+--------------+
    | :py:const:`Mux.MUX_AIN1_AIN3` | AIN 1        | AIN 3        |
    +-------------------------------+--------------+--------------+
    | :py:const:`Mux.MUX_AIN2_AIN3` | AIN 2        | AIN 3        |
    +-------------------------------+--------------+--------------+
    | :py:const:`Mux.MUX_AIN0_GND`  | AIN 0        | GND          |
    +-------------------------------+--------------+--------------+
    | :py:const:`Mux.MUX_AIN1_GND`  | AIN 1        | GND          |
    +-------------------------------+--------------+--------------+
    | :py:const:`Mux.MUX_AIN2_GND`  | AIN 2        | GND          |
    +-------------------------------+--------------+--------------+
    | :py:const:`Mux.MUX_AIN3_GND`  | AIN 3        | GND          |
    +-------------------------------+--------------+--------------+

    """


Mux.add_values(
    (
        ("MUX_AIN0_AIN1", 0x0, "AIN 0 to AIN 1", None),
        ("MUX_AIN0_AIN3", 0x1, "AIN 0 to AIN 3", None),
        ("MUX_AIN1_AIN3", 0x2, "AIN 1 to AIN 3", None),
        ("MUX_AIN2_AIN3", 0x3, "AIN 2 to AIN 3", None),
        ("MUX_AIN0_GND", 0x4, "AIN 0 to GND", None),
        ("MUX_AIN1_GND", 0x5, "AIN 1 to GND", None),
        ("MUX_AIN2_GND", 0x6, "AIN 2 to GND", None),
        ("MUX_AIN3_GND", 0x7, "AIN 3 to GND", None),
    )
)


class TLA2024:  # pylint:disable=too-many-instance-attributes
    """

    I2C Interface for analog voltage measurements using the TI TLA2024 12-bit 4-channel ADC

        :param i2c_bus: The I2C bus that the ADC is on.
        :param int address: The I2C address for the ADC. Defaults to ~0x48
    """

    _raw_adc_read = ROUnaryStruct(_DATA_REG, ">h")

    _os = RWBit(_CONFIG_REG, 15, 2, lsb_first=False)
    _mux = RWBits(3, _CONFIG_REG, 12, 2, lsb_first=False)
    _pga = RWBits(3, _CONFIG_REG, 9, 2, lsb_first=False)
    _mode = RWBit(_CONFIG_REG, 8, 2, lsb_first=False)
    _data_rate = RWBits(3, _CONFIG_REG, 5, 2, lsb_first=False)

    def __init__(self, i2c_bus, address=_TLA_DEFAULT_ADDRESS):

        # pylint:disable=no-member

        self.i2c_device = I2CDevice(i2c_bus, address)
        self._last_one_shot = None
        self.mode = Mode.CONTINUOUS
        self.mux = Mux.MUX_AIN0_GND
        # default to widest range and highest sample rate
        self.data_rate = DataRate.RATE_3300SPS
        self.range = Range.RANGE_6_144V

    @property
    def voltage(self):
        """The voltage between the two selected inputs"""
        if self.mode == Mode.ONE_SHOT:  # pylint:disable=no-member
            return self._last_one_shot
        return self._read_volts()

    @property
    def input_channel(self):
        """The channel to be sampled"""
        return self._mux

    @input_channel.setter
    def input_channel(self, channel):
        """The input number to measure the voltage at, referenced to GND.

        :param channel: The channel number to switch to, from 0-4"""

        if channel not in range(4):
            raise AttributeError("input_channel must be set to a number from 0 to 3")
        self._mux = 4 + channel

    @property
    def mode(self):
        """The measurement mode of the sensor. Must be a :py:const:`~Mode`.  See the documentation
        for :py:const:`~Mode` for more information"""
        return self._mode

    @mode.setter
    def mode(self, mode):
        if not Mode.is_valid(mode):
            raise AttributeError("mode must be a valid Mode")
        if mode == Mode.CONTINUOUS:  # pylint:disable=no-member
            self._mode = mode
            return
        # One Shot mode; switch mode, take a measurement and store it
        self._mode = mode
        self._os = True
        while self._os:
            pass

        self._last_one_shot = self._read_volts()

    @property
    def range(self):
        """The measurement range of the ADC, changed by adjusting the Programmable Gain Amplifier
        `range` must be a :py:const:`~Range`.  See the documentation for :py:const:`~Range`
        for more information"""
        return self._pga

    @range.setter
    def range(self, measurement_range):
        if not Range.is_valid(measurement_range):
            raise AttributeError("range must be a valid Range")
        self._pga = measurement_range

    @property
    def data_rate(self):
        """selects the rate at which measurement samples are taken.  Must be a :py:const:`~DataRate`
        . See the documentation for :py:const:`~DataRate` for more information"""
        return self._data_rate

    @data_rate.setter
    def data_rate(self, rate):
        if not DataRate.is_valid(rate):  # pylint:disable=no-member
            raise AttributeError("data_rate must be a valid DataRate")
        self._data_rate = rate

    @property
    def mux(self):
        """selects the inputs that voltage will be measured between. Must be a
        :py:const:`~adafruit_tla202x.Mux`. See the :py:const:`~adafruit_tla202x.Mux` documentation
        for more information about the available options"""
        return self._mux

    @mux.setter
    def mux(self, mux_connection):
        if not Mux.is_valid(mux_connection):  # pylint:disable=no-member
            raise AttributeError("mux must be a valid Mux")
        self._mux = mux_connection

    def read(self, channel):
        """Switch to the given channel and take a single ADC reading in One Shot mode

        :param channel: The channel number to switch to, from 0-3

        """
        if not self.input_channel == channel:
            self.input_channel = channel
        self.mode = Mode.ONE_SHOT  # pylint:disable=no-member
        return self._read_adc()

    def _read_volts(self):
        value_lsb = self._read_adc()
        return value_lsb * Range.lsb[self.range] / 1000.0

    def _read_adc(self):
        value_lsb = self._raw_adc_read
        value_lsb >>= 4

        if value_lsb & (1 << 11):
            value_lsb |= 0xF000
        else:
            value_lsb &= ~0xF000
        return value_lsb
