# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_emc2101`
================================================================================

Brushless fan controller


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* `Adafruit EMC2101 Breakout <https://adafruit.com/product/4808>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

from micropython import const
from adafruit_register.i2c_struct import ROUnaryStruct, UnaryStruct
from adafruit_register.i2c_bit import RWBit
from adafruit_register.i2c_bits import RWBits
import adafruit_bus_device.i2c_device as i2cdevice

__version__ = "1.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_EMC2101.git"

_INTERNAL_TEMP = const(0x00)
_EXTERNAL_TEMP_MSB = const(0x01)
_EXTERNAL_TEMP_LSB = const(0x10)

_STATUS = const(0x02)
_REG_CONFIG = const(0x03)
_TEMP_FORCE = const(0x0C)
_TACH_LSB = const(0x46)
_TACH_MSB = const(0x47)
_TACH_LIMIT_LSB = const(0x48)
_TACH_LIMIT_MSB = const(0x49)
_FAN_CONFIG = const(0x4A)
_FAN_SPINUP = const(0x4B)
_REG_FAN_SETTING = const(0x4C)
_PWM_FREQ = const(0x4D)
_PWM_DIV = const(0x4E)
_LUT_HYSTERESIS = const(0x4F)

_TEMP_FILTER = const(0xBF)
_REG_PARTID = const(0xFD)  # 0x16
_REG_MFGID = const(0xFE)  # 0xFF16

MAX_LUT_SPEED = 0x3F  # 6-bit value
MAX_LUT_TEMP = 0x7F  # 7-bit

_I2C_ADDR = const(0x4C)
_FAN_RPM_DIVISOR = const(5400000)
_TEMP_LSB = 0.125


def _speed_to_lsb(percentage):
    return round((percentage / 100.0) * MAX_LUT_SPEED)


def _lsb_to_speed(lsb_speed):
    return round((lsb_speed / MAX_LUT_SPEED) * 100.0)


class FanSpeedLUT:
    """A class used to provide a dict-like interface to the EMC2101's Temperature to Fan speed
    Look Up Table"""

    # seems like a pain but ¯\_(ツ)_/¯
    _fan_lut_t1 = UnaryStruct(0x50, "<B")
    _fan_lut_s1 = UnaryStruct(0x51, "<B")

    _fan_lut_t2 = UnaryStruct(0x52, "<B")
    _fan_lut_s2 = UnaryStruct(0x53, "<B")

    _fan_lut_t3 = UnaryStruct(0x54, "<B")
    _fan_lut_s3 = UnaryStruct(0x55, "<B")

    _fan_lut_t4 = UnaryStruct(0x56, "<B")
    _fan_lut_s4 = UnaryStruct(0x57, "<B")

    _fan_lut_t5 = UnaryStruct(0x58, "<B")
    _fan_lut_s5 = UnaryStruct(0x59, "<B")

    _fan_lut_t6 = UnaryStruct(0x5A, "<B")
    _fan_lut_s6 = UnaryStruct(0x5B, "<B")

    _fan_lut_t7 = UnaryStruct(0x5C, "<B")
    _fan_lut_s7 = UnaryStruct(0x5D, "<B")

    _fan_lut_t8 = UnaryStruct(0x5E, "<B")
    _fan_lut_s8 = UnaryStruct(0x5F, "<B")

    _lut_speed_setters = [
        _fan_lut_s1,
        _fan_lut_s2,
        _fan_lut_s3,
        _fan_lut_s4,
        _fan_lut_s5,
        _fan_lut_s6,
        _fan_lut_s7,
        _fan_lut_s8,
    ]
    _lut_temp_setters = [
        _fan_lut_t1,
        _fan_lut_t2,
        _fan_lut_t3,
        _fan_lut_t4,
        _fan_lut_t5,
        _fan_lut_t6,
        _fan_lut_t7,
        _fan_lut_t8,
    ]

    def __init__(self, fan_obj):
        self.emc_fan = fan_obj
        self.lut_values = {}
        self.i2c_device = fan_obj.i2c_device

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise IndexError
        if not index in self.lut_values:
            raise IndexError
        return self.lut_values[index]

    def __setitem__(self, index, value):
        if not isinstance(index, int):
            raise IndexError
        self.lut_values[index] = value
        self._set_lut(self.lut_values)

    def __repr__(self):
        """return the official string representation of the LUT"""
        return "FanSpeedLUT <%x>" % id(self)

    def __str__(self):
        """return the official string representation of the LUT"""
        value_strs = []
        lut_keys = list(self.lut_values.keys())
        lut_keys.sort()
        for temp in lut_keys:
            fan_drive = self.lut_values[temp]
            value_strs.append("%d deg C => %.1f%% duty cycle" %
                              (temp, fan_drive))

        return "\n".join(value_strs)

    def __len__(self):
        return len(self.lut_values)

    # this function does a whole lot of work to organized the user-supplied lut dict into
    # their correct spot within the lut table as pairs of set registers, sorted with the lowest
    # temperature first

    def _set_lut(self, lut_dict):
        lut_keys = list(lut_dict.keys())
        lut_size = len(lut_dict)
        # Make sure we're not going to try to set more entries than we have slots
        if lut_size > 8:
            raise AttributeError("LUT can only contain a maximum of 8 items")

        # we want to assign the lowest temperature to the lowest LUT slot, so we sort the keys/temps
        for k in lut_keys:
            # Verify that the value is a correct amount
            lut_value = lut_dict[k]
            if lut_value > 100.0 or lut_value < 0:
                raise AttributeError(
                    "LUT values must be a fan speed from 0-100%")

            # add the current temp/speed to our internal representation
            self.lut_values[k] = lut_value
        current_mode = self.emc_fan.lut_enabled

        # Disable the lut to allow it to be updated
        self.emc_fan.lut_enabled = False

        # get and sort the new lut keys so that we can assign them in order
        lut_keys = list(self.lut_values.keys())
        lut_keys.sort()
        for idx in range(lut_size):
            current_temp = lut_keys[idx]
            current_speed = _speed_to_lsb(self.lut_values[current_temp])
            getattr(self, "_fan_lut_t%d" %
                    (idx + 1)).__set__(self, current_temp)
            getattr(self, "_fan_lut_s%d" %
                    (idx + 1)).__set__(self, current_speed)

            # self.emc_fan._lut_temp_setters[idx].__set__(self.emc_fan, current_temp)
            # self.emc_fan._lut_speed_setters[idx].__set__(self.emc_fan, current_speed)

        # Set the remaining LUT entries to the default (Temp/Speed = max value)
        for idx in range(8)[lut_size:]:
            getattr(self, "_fan_lut_t%d" %
                    (idx + 1)).__set__(self, MAX_LUT_TEMP)
            getattr(self, "_fan_lut_s%d" %
                    (idx + 1)).__set__(self, MAX_LUT_SPEED)
        self.emc_fan.lut_enabled = current_mode


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


class ConversionRate(CV):
    """Options for ``accelerometer_data_rate`` and ``gyro_data_rate``"""


ConversionRate.add_values(
    (
        ("RATE_1_16", 0, str(1 / 16.0), None),
        ("RATE_1_8", 1, str(1 / 8.0), None),
        ("RATE_1_4", 2, str(1 / 4.0), None),
        ("RATE_1_2", 3, str(126.0), None),
        ("RATE_1", 4, str(1.0), None),
        ("RATE_2", 5, str(2.0), None),
        ("RATE_4", 6, str(4.0), None),
        ("RATE_8", 7, str(8.0), None),
        ("RATE_16", 8, str(16.0), None),
        ("RATE_32", 9, str(32.0), None),
    )
)


class SpinupDrive(CV):
    """Options for ``spinup_drive``"""


SpinupDrive.add_values(
    (
        ("BYPASS", 0, "Disabled", None),
        ("DRIVE_50", 1, "50% Duty Cycle", None),
        ("DRIVE_75", 2, "25% Duty Cycle", None),
        ("DRIVE_100", 3, "100% Duty Cycle", None),
    )
)


class SpinupTime(CV):
    """Options for ``spinup_time``"""


SpinupTime.add_values(
    (
        ("BYPASS", 0, "Disabled", None),
        ("SPIN_0_05_SEC", 1, "0.05 seconds", None),
        ("SPIN_0_1_SEC", 2, "0.1 seconds", None),
        ("SPIN_0_2_SEC", 3, "0.2 seconds", None),
        ("SPIN_0_4_SEC", 4, "0.4 seconds", None),
        ("SPIN_0_8_SEC", 5, "0.8 seconds", None),
        ("SPIN_1_6_SEC", 6, "1.6 seconds", None),
        ("SPIN_3_2_SEC", 7, "3.2 seconds", None),
    )
)


class EMC2101:  # pylint: disable=too-many-instance-attributes
    """Driver for the EMC2101 Fan Controller.
        :param ~busio.I2C i2c_bus: The I2C bus the EMC is connected to.
    """

    _part_id = ROUnaryStruct(_REG_PARTID, "<B")
    _mfg_id = ROUnaryStruct(_REG_MFGID, "<B")
    _int_temp = ROUnaryStruct(_INTERNAL_TEMP, "<b")

    # IMPORTANT! the sign bit for the external temp is in the msbyte so mark it as signed
    # and lsb as unsigned
    _ext_temp_msb = ROUnaryStruct(_EXTERNAL_TEMP_MSB, "<b")
    _ext_temp_lsb = ROUnaryStruct(_EXTERNAL_TEMP_LSB, "<B")

    # _tach_read = ROUnaryStruct(_TACH_LSB, "<H")
    _tach_read_lsb = ROUnaryStruct(_TACH_LSB, "<B")
    _tach_read_msb = ROUnaryStruct(_TACH_MSB, "<B")
    _tach_mode_enable = RWBit(_REG_CONFIG, 2)
    _tach_limit_lsb = UnaryStruct(_TACH_LIMIT_LSB, "<B")
    _tach_limit_msb = UnaryStruct(_TACH_LIMIT_MSB, "<B")
    # temp used to override current external temp measurement
    forced_ext_temp = UnaryStruct(_TEMP_FORCE, "<b")
    """The value that the external temperature will be forced to read when `forced_temp_enabled` is
    set. This can be used to test the behavior of the LUT without real temperature changes"""
    forced_temp_enabled = RWBit(_FAN_CONFIG, 6)
    """When True, the external temperature measurement will always be read as the value in
    `forced_ext_temp`"""

    _fan_setting = UnaryStruct(_REG_FAN_SETTING, "<B")
    _fan_lut_prog = RWBit(_FAN_CONFIG, 5)
    invert_fan_output = RWBit(_FAN_CONFIG, 4)
    """When set to True, the magnitude of the fan output signal is inverted, making 0 the maximum
    value and 100 the minimum value"""

    _fan_pwm_clock_select = RWBit(_FAN_CONFIG, 3)
    _fan_pwm_clock_override = RWBit(_FAN_CONFIG, 2)
    _pwm_freq = RWBits(5, _PWM_FREQ, 0)
    _pwm_freq_div = UnaryStruct(_PWM_DIV, "<B")

    dac_output_enabled = RWBit(_REG_CONFIG, 4)
    """When set, the fan control signal is output as a DC voltage instead of a PWM signal"""

    _conversion_rate = RWBits(4, 0x04, 0)
    # fan spin-up
    _spin_drive = RWBits(2, _FAN_SPINUP, 3)
    _spin_time = RWBits(3, _FAN_SPINUP, 0)
    _spin_tach_limit = RWBit(_FAN_SPINUP, 5)

    lut_temperature_hysteresis = UnaryStruct(_LUT_HYSTERESIS, "<B")
    """The amount of hysteresis in Degrees celcius of hysteresis applied to temperature readings
    used for the LUT. As the temperature drops, the controller will switch to a lower LUT entry when
    the measured value is belowthe lower entry's threshold, minus the hysteresis value"""

    def __init__(self, i2c_bus):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, _I2C_ADDR)

        if not self._part_id in [0x16, 0x28] or self._mfg_id != 0x5D:
            raise AttributeError("Cannot find a EMC2101")
        # self._lut = {}

        self.initialize()
        self._lut = FanSpeedLUT(self)

    def initialize(self):
        """Reset the controller to an initial default configuration"""
        self._tach_mode_enable = True
        self.lut_enabled = False
        self._enabled_forced_temp = False
        self._fan_pwm_clock_override = True
        self._spin_tach_limit = False

    @property
    def internal_temperature(self):
        """The temperature as measured by the EMC2101's internal 8-bit temperature sensor"""
        return self._int_temp

    @property
    def external_temperature(self):
        """The temperature measured using the external diode"""

        temp_lsb = self._ext_temp_lsb
        temp_msb = self._ext_temp_msb
        full_tmp = (temp_msb << 8) | temp_lsb
        full_tmp >>= 5
        full_tmp *= 0.125

        return full_tmp

    def set_pwm_clock(self, use_preset=False, use_slow=False):
        """
        Select the PWM clock source, chosing between two preset clocks or by configuring the
        clock using `pwm_frequency` and `pwm_frequency_divisor`.

   :param bool use_preset:
    True: Select between two preset clock sources
    False: The PWM clock is set by `pwm_frequency` and `pwm_frequency_divisor`
   :param bool use_slow:
        True: Use the 1.4kHz clock
        False: Use the 360kHz clock.
   :type priority: integer or None
   :return: None
   :raises AttributeError: if use_preset is not a `bool`
   :raises AttributeError: if use_slow is not a `bool`

        """

        if not isinstance(use_preset, bool):
            raise AttributeError("use_preset must be given a bool")
        if not isinstance(use_slow, bool):
            raise AttributeError("use_slow_pwm must be given a bool")

        self._fan_pwm_clock_override = not use_preset
        self._fan_pwm_clock_select = use_slow

    @property
    def pwm_frequency(self):
        """Selects the base clock frequency used for the fan PWM output"""
        return self._pwm_freq

    @pwm_frequency.setter
    def pwm_frequency(self, value):
        if value < 0 or value > 0x1F:
            raise AttributeError("pwm_frequency must be from 0-31")
        self._pwm_freq = value

    @property
    def pwm_frequency_divisor(self):
        """The Divisor applied to the PWM frequency to set the final frequency"""
        return self._pwm_freq_div

    @pwm_frequency_divisor.setter
    def pwm_frequency_divisor(self, divisor):
        if divisor < 0 or divisor > 255:
            raise AttributeError("pwm_frequency_divisor must be from 0-255")
        self._pwm_freq_div = divisor

    @property
    def fan_speed(self):
        """The current speed in Revolutions per Minute (RPM)"""

        val = self._tach_read_lsb
        val |= self._tach_read_msb << 8
        return _FAN_RPM_DIVISOR / val

    @property
    def manual_fan_speed(self):
        """The fan speed used while the LUT is being updated and is unavailable. The speed is
        given as the fan's PWM duty cycle represented as a float percentage.
        The value roughly approximates the percentage of the fan's maximum speed"""
        raw_setting = self._fan_setting & MAX_LUT_SPEED
        return (raw_setting / MAX_LUT_SPEED) * 100

    @manual_fan_speed.setter
    def manual_fan_speed(self, fan_speed):
        if fan_speed not in range(0, 101):
            raise AttributeError("manual_fan_speed must be from 0-100 ")

        # convert from a percentage to an lsb value
        percentage = fan_speed / 100.0
        fan_speed_lsb = round(percentage * MAX_LUT_SPEED)
        lut_disabled = self._fan_lut_prog
        self._fan_lut_prog = True
        self._fan_setting = fan_speed_lsb
        self._fan_lut_prog = lut_disabled

    @property
    def lut_enabled(self):
        """Enable or disable the internal look up table used to map a given temperature
      to a fan speed. When the LUT is disabled, fan speed can be changed with `manual_fan_speed`"""
        return not self._fan_lut_prog

    @lut_enabled.setter
    def lut_enabled(self, enable_lut):
        self._fan_lut_prog = not enable_lut

    @property
    def lut(self):
        """The dict-like representation of the LUT"""
        return self._lut

    @property
    def tach_limit(self):
        """The maximum /minimum speed expected for the fan"""

        low = self._tach_limit_lsb
        high = self._tach_limit_msb

        return _FAN_RPM_DIVISOR / ((high << 8) | low)

    @tach_limit.setter
    def tach_limit(self, new_limit):
        num = int(_FAN_RPM_DIVISOR / new_limit)
        self._tach_limit_lsb = num & 0xFF
        self._tach_limit_msb = (num >> 8) & 0xFF

    @property
    def spinup_time(self):
        """The amount of time the fan will spin at the current set drive strength.
        Must be a `SpinupTime`"""
        return self._spin_time

    @spinup_time.setter
    def spinup_time(self, spin_time):
        if not SpinupTime.is_valid(spin_time):
            raise AttributeError("spinup_time must be a SpinupTime")
        self._spin_time = spin_time

    @property
    def spinup_drive(self):
        """The drive strengh of the fan on spinup in % max RPM"""
        return self._spin_drive

    @spinup_drive.setter
    def spinup_drive(self, spin_drive):
        if not SpinupDrive.is_valid(spin_drive):
            raise AttributeError("spinup_drive must be a SpinupDrive")
        self._spin_drive = spin_drive

    @property
    def conversion_rate(self):
        """The rate at which temperature measurements are taken. Must be a `ConversionRate`"""
        return self._conversion_rate

    @conversion_rate.setter
    def conversion_rate(self, rate):
        if not ConversionRate.is_valid(rate):
            raise AttributeError("conversion_rate must be a `ConversionRate`")
        self._conversion_rate = rate
