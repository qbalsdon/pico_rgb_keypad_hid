# SPDX-FileCopyrightText: 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_dps310`
================================================================================

Library for the DPS310 Precision Barometric Pressure Sensor

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit's DPS310 Breakout: https://www.adafruit.com/product/4494

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register"""

__version__ = "1.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DPS310.git"

# Common imports; remove if unused or pylint will complain
import math
from time import sleep
import adafruit_bus_device.i2c_device as i2c_device
from adafruit_register.i2c_struct import UnaryStruct, ROUnaryStruct
from adafruit_register.i2c_bit import RWBit, ROBit
from adafruit_register.i2c_bits import RWBits, ROBits

_DPS310_DEFAULT_ADDRESS = 0x77  # DPS310 default i2c address
_DPS310_DEVICE_ID = 0x10  # DPS310 device identifier

_DPS310_PRSB2 = 0x00  # Highest byte of pressure data
_DPS310_TMPB2 = 0x03  # Highest byte of temperature data
_DPS310_PRSCFG = 0x06  # Pressure configuration
_DPS310_TMPCFG = 0x07  # Temperature configuration
_DPS310_MEASCFG = 0x08  # Sensor configuration
_DPS310_CFGREG = 0x09  # Interrupt/FIFO configuration
_DPS310_RESET = 0x0C  # Soft reset
_DPS310_PRODREVID = 0x0D  # Register that contains the part ID
_DPS310_TMPCOEFSRCE = 0x28  # Temperature calibration src

# pylint: disable=no-member,unnecessary-pass


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


class Mode(CV):
    """Options for ``mode``

    +--------------------------+------------------------------------------------------------------+
    | Mode                     | Description                                                      |
    +--------------------------+------------------------------------------------------------------+
    | ``Mode.IDLE``            | Puts the sensor into a shutdown state                            |
    +--------------------------+------------------------------------------------------------------+
    | ``Mode.ONE_PRESSURE``    | Setting `mode` to ``Mode.ONE_PRESSURE`` takes a single pressure  |
    |                          | measurement then switches to ``Mode.IDLE``                       |
    +--------------------------+------------------------------------------------------------------+
    | ``Mode.ONE_TEMPERATURE`` | Setting `mode` to ``Mode.ONE_TEMPERATURE`` takes a single        |
    |                          | temperature measurement then switches to ``Mode.IDLE``           |
    +--------------------------+------------------------------------------------------------------+
    | ``Mode.CONT_PRESSURE``   | Take pressure measurements at the current `pressure_rate`.       |
    |                          | `temperature` will not be updated                                |
    +--------------------------+------------------------------------------------------------------+
    | ``Mode.CONT_TEMP``       | Take temperature measurements at the current `temperature_rate`. |
    |                          | `pressure` will not be updated                                   |
    +--------------------------+------------------------------------------------------------------+
    | ``Mode.CONT_PRESTEMP``   | Take temperature and pressure measurements at the current        |
    |                          | `pressure_rate` and `temperature_rate`                           |
    +--------------------------+------------------------------------------------------------------+

    """

    pass  # pylint: disable=unnecessary-pass


Mode.add_values(
    (
        ("IDLE", 0, "Idle", None),
        ("ONE_PRESSURE", 1, "One-Shot Pressure", None),
        ("ONE_TEMPERATURE", 2, "One-Shot Temperature", None),
        ("CONT_PRESSURE", 5, "Continuous Pressure", None),
        ("CONT_TEMP", 6, "Continuous Temperature", None),
        ("CONT_PRESTEMP", 7, "Continuous Pressure & Temperature", None),
    )
)


class Rate(CV):
    """Options for `pressure_rate` and `temperature_rate`"""

    pass


Rate.add_values(
    (
        ("RATE_1_HZ", 0, 1, None),
        ("RATE_2_HZ", 1, 2, None),
        ("RATE_4_HZ", 2, 4, None),
        ("RATE_8_HZ", 3, 8, None),
        ("RATE_16_HZ", 4, 16, None),
        ("RATE_32_HZ", 5, 32, None),
        ("RATE_64_HZ", 6, 64, None),
        ("RATE_128_HZ", 7, 128, None),
    )
)


class SampleCount(CV):
    """Options for `temperature_oversample_count` and `pressure_oversample_count`"""

    pass


SampleCount.add_values(
    (
        ("COUNT_1", 0, 1, None),
        ("COUNT_2", 1, 2, None),
        ("COUNT_4", 2, 4, None),
        ("COUNT_8", 3, 8, None),
        ("COUNT_16", 4, 16, None),
        ("COUNT_32", 5, 32, None),
        ("COUNT_64", 6, 64, None),
        ("COUNT_128", 7, 128, None),
    )
)
# pylint: enable=unnecessary-pass
class DPS310:
    # pylint: disable=too-many-instance-attributes
    """Library for the DPS310 Precision Barometric Pressure Sensor.

    :param ~busio.I2C i2c_bus: The I2C bus the DPS310 is connected to.
    :param address: The I2C slave address of the sensor

    """
    # Register definitions
    _device_id = ROUnaryStruct(_DPS310_PRODREVID, ">B")
    _reset_register = UnaryStruct(_DPS310_RESET, ">B")
    _mode_bits = RWBits(3, _DPS310_MEASCFG, 0)

    _pressure_ratebits = RWBits(3, _DPS310_PRSCFG, 4)
    _pressure_osbits = RWBits(4, _DPS310_PRSCFG, 0)

    _temp_ratebits = RWBits(3, _DPS310_TMPCFG, 4)
    _temp_osbits = RWBits(4, _DPS310_TMPCFG, 0)

    _temp_measurement_src_bit = RWBit(_DPS310_TMPCFG, 7)

    _pressure_shiftbit = RWBit(_DPS310_CFGREG, 2)
    _temp_shiftbit = RWBit(_DPS310_CFGREG, 3)

    _coefficients_ready = RWBit(_DPS310_MEASCFG, 7)
    _sensor_ready = RWBit(_DPS310_MEASCFG, 6)
    _temp_ready = RWBit(_DPS310_MEASCFG, 5)
    _pressure_ready = RWBit(_DPS310_MEASCFG, 4)

    _raw_pressure = ROBits(24, _DPS310_PRSB2, 0, 3, lsb_first=False)
    _raw_temperature = ROBits(24, _DPS310_TMPB2, 0, 3, lsb_first=False)

    _calib_coeff_temp_src_bit = ROBit(_DPS310_TMPCOEFSRCE, 7)

    _reg0e = RWBits(8, 0x0E, 0)
    _reg0f = RWBits(8, 0x0F, 0)
    _reg62 = RWBits(8, 0x62, 0)

    def __init__(self, i2c_bus, address=_DPS310_DEFAULT_ADDRESS):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)

        if self._device_id != _DPS310_DEVICE_ID:
            raise RuntimeError("Failed to find DPS310 - check your wiring!")
        self._pressure_scale = None
        self._temp_scale = None
        self._c0 = None
        self._c1 = None
        self._c00 = None
        self._c00 = None
        self._c10 = None
        self._c10 = None
        self._c01 = None
        self._c11 = None
        self._c20 = None
        self._c21 = None
        self._c30 = None
        self._oversample_scalefactor = (
            524288,
            1572864,
            3670016,
            7864320,
            253952,
            516096,
            1040384,
            2088960,
        )
        self.sea_level_pressure = 1013.25
        """Pressure in hectoPascals at sea level. Used to calibrate `altitude`."""
        self.initialize()

    def initialize(self):
        """Initialize the sensor to continuous measurement"""

        self.reset()

        self.pressure_rate = Rate.RATE_64_HZ
        self.pressure_oversample_count = SampleCount.COUNT_64
        self.temperature_rate = Rate.RATE_64_HZ
        self.temperature_oversample_count = SampleCount.COUNT_64
        self.mode = Mode.CONT_PRESTEMP

        # wait until we have at least one good measurement
        self.wait_temperature_ready()
        self.wait_pressure_ready()

    # (https://github.com/Infineon/DPS310-Pressure-Sensor#temperature-measurement-issue)
    # similar to DpsClass::correctTemp(void) from infineon's c++ library
    def _correct_temp(self):
        """Correct temperature readings on ICs with a fuse bit problem"""
        self._reg0e = 0xA5
        self._reg0f = 0x96
        self._reg62 = 0x02
        self._reg0e = 0
        self._reg0f = 0

        # perform a temperature measurement
        # the most recent temperature will be saved internally
        # and used for compensation when calculating pressure
        _unused = self._raw_temperature

    def reset(self):
        """Reset the sensor"""
        self._reset_register = 0x89
        # wait for hardware reset to finish
        sleep(0.010)
        while not self._sensor_ready:
            sleep(0.001)
        self._correct_temp()
        self._read_calibration()
        # make sure we're using the temperature source used for calibration
        self._temp_measurement_src_bit = self._calib_coeff_temp_src_bit

    @property
    def pressure(self):
        """Returns the current pressure reading in kPA"""

        temp_reading = self._raw_temperature
        raw_temperature = self._twos_complement(temp_reading, 24)
        pressure_reading = self._raw_pressure
        raw_pressure = self._twos_complement(pressure_reading, 24)
        _scaled_rawtemp = raw_temperature / self._temp_scale

        _temperature = _scaled_rawtemp * self._c1 + self._c0 / 2.0

        p_red = raw_pressure / self._pressure_scale

        pres_calc = (
            self._c00
            + p_red * (self._c10 + p_red * (self._c20 + p_red * self._c30))
            + _scaled_rawtemp * (self._c01 + p_red * (self._c11 + p_red * self._c21))
        )

        final_pressure = pres_calc / 100
        return final_pressure

    @property
    def altitude(self):
        """The altitude based on the sea level pressure (`sea_level_pressure`) - which you must
        enter ahead of time)"""
        return 44330 * (1.0 - math.pow(self.pressure / self.sea_level_pressure, 0.1903))

    @property
    def temperature(self):
        """The current temperature reading in degrees C"""
        _scaled_rawtemp = self._raw_temperature / self._temp_scale
        _temperature = _scaled_rawtemp * self._c1 + self._c0 / 2.0
        return _temperature

    @property
    def temperature_ready(self):
        """Returns true if there is a temperature reading ready"""
        return self._temp_ready

    def wait_temperature_ready(self):
        """Wait until a temperature measurement is available.

        To avoid waiting indefinitely this function raises an
        error if the sensor isn't configured for temperate measurements,
        ie. ``Mode.ONE_TEMPERATURE``, ``Mode.CONT_TEMP`` or ``Mode.CONT_PRESTEMP``.
        See the `Mode` documentation for details.
        """
        if (
            self._mode_bits == Mode.IDLE
            or self._mode_bits == Mode.ONE_PRESSURE
            or self._mode_bits == Mode.CONT_PRESSURE
        ):
            raise RuntimeError(
                "Sensor mode is set to idle or pressure measurement,\
                    can't wait for a temperature measurement"
            )
        while self._temp_ready is False:
            sleep(0.001)

    @property
    def pressure_ready(self):
        """Returns true if pressure readings are ready"""
        return self._pressure_ready

    def wait_pressure_ready(self):
        """Wait until a pressure measurement is available

        To avoid waiting indefinitely this function raises an
        error if the sensor isn't configured for pressure measurements,
        ie.  ``Mode.ONE_PRESSURE``, ``Mode.CONT_PRESSURE`` or ``Mode.CONT_PRESTEMP``
        See the `Mode` documentation for details.
        """
        if (
            self._mode_bits == Mode.IDLE
            or self._mode_bits == Mode.ONE_TEMPERATURE
            or self._mode_bits == Mode.CONT_TEMP
        ):
            raise RuntimeError(
                "Sensor mode is set to idle or temperature measurement,\
                    can't wait for a pressure measurement"
            )
        while self._pressure_ready is False:
            sleep(0.001)

    @property
    def mode(self):
        """The measurement mode. Must be a `Mode`. See the `Mode` documentation for details"""
        return self._mode_bits

    @mode.setter
    def mode(self, value):
        if not Mode.is_valid(value):
            raise AttributeError("mode must be an `Mode`")

        self._mode_bits = value

    @property
    def pressure_rate(self):
        """Configure the pressure measurement rate. Must be a `Rate`"""
        return self._pressure_ratebits

    @pressure_rate.setter
    def pressure_rate(self, value):
        if not Rate.is_valid(value):
            raise AttributeError("pressure_rate must be a Rate")
        self._pressure_ratebits = value

    @property
    def pressure_oversample_count(self):
        """The number of samples taken per pressure measurement. Must be a `SampleCount`"""
        return self._pressure_osbits

    @pressure_oversample_count.setter
    def pressure_oversample_count(self, value):
        if not SampleCount.is_valid(value):
            raise AttributeError("pressure_oversample_count must be a SampleCount")

        self._pressure_osbits = value
        self._pressure_shiftbit = value > SampleCount.COUNT_8
        self._pressure_scale = self._oversample_scalefactor[value]

    @property
    def temperature_rate(self):
        """Configure the temperature measurement rate. Must be a `Rate`"""
        return self._temp_ratebits

    @temperature_rate.setter
    def temperature_rate(self, value):
        if not Rate.is_valid(value):
            raise AttributeError("temperature_rate must be a Rate")
        self._temp_ratebits = value

    @property
    def temperature_oversample_count(self):
        """The number of samples taken per temperature measurement. Must be a `SampleCount`"""
        return self._temp_osbits

    @temperature_oversample_count.setter
    def temperature_oversample_count(self, value):
        if not SampleCount.is_valid(value):
            raise AttributeError("temperature_oversample_count must be a SampleCount")

        self._temp_osbits = value
        self._temp_scale = self._oversample_scalefactor[value]
        self._temp_shiftbit = value > SampleCount.COUNT_8

    @staticmethod
    def _twos_complement(val, bits):
        if val & (1 << (bits - 1)):
            val -= 1 << bits

        return val

    def _read_calibration(self):

        while not self._coefficients_ready:
            sleep(0.001)

        buffer = bytearray(19)
        coeffs = [None] * 18
        for offset in range(18):
            buffer = bytearray(2)
            buffer[0] = 0x10 + offset

            with self.i2c_device as i2c:

                i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)

                coeffs[offset] = buffer[1]

        self._c0 = (coeffs[0] << 4) | ((coeffs[1] >> 4) & 0x0F)
        self._c0 = self._twos_complement(self._c0, 12)

        self._c1 = self._twos_complement(((coeffs[1] & 0x0F) << 8) | coeffs[2], 12)

        self._c00 = (coeffs[3] << 12) | (coeffs[4] << 4) | ((coeffs[5] >> 4) & 0x0F)
        self._c00 = self._twos_complement(self._c00, 20)

        self._c10 = ((coeffs[5] & 0x0F) << 16) | (coeffs[6] << 8) | coeffs[7]
        self._c10 = self._twos_complement(self._c10, 20)

        self._c01 = self._twos_complement((coeffs[8] << 8) | coeffs[9], 16)
        self._c11 = self._twos_complement((coeffs[10] << 8) | coeffs[11], 16)
        self._c20 = self._twos_complement((coeffs[12] << 8) | coeffs[13], 16)
        self._c21 = self._twos_complement((coeffs[14] << 8) | coeffs[15], 16)
        self._c30 = self._twos_complement((coeffs[16] << 8) | coeffs[17], 16)
