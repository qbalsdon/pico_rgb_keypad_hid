# SPDX-FileCopyrightText: 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`MSA301`
================================================================================

CircuitPython library for the MSA301 Accelerometer


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit MSA301 Breakout https://www.adafruit.com/product/4344

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MSA301.git"

from micropython import const
from adafruit_register.i2c_struct import Struct, ROUnaryStruct
from adafruit_register.i2c_bit import RWBit
from adafruit_register.i2c_bits import RWBits
import adafruit_bus_device.i2c_device as i2cdevice

_MSA301_I2CADDR_DEFAULT = const(0x26)

_MSA301_REG_PARTID = const(0x01)
_MSA301_REG_OUT_X_L = const(0x02)
_MSA301_REG_OUT_X_H = const(0x03)
_MSA301_REG_OUT_Y_L = const(0x04)
_MSA301_REG_OUT_Y_H = const(0x05)
_MSA301_REG_OUT_Z_L = const(0x06)
_MSA301_REG_OUT_Z_H = const(0x07)
_MSA301_REG_MOTIONINT = const(0x09)
_MSA301_REG_DATAINT = const(0x0A)
_MSA301_REG_RESRANGE = const(0x0F)
_MSA301_REG_ODR = const(0x10)
_MSA301_REG_POWERMODE = const(0x11)
_MSA301_REG_INTSET0 = const(0x16)
_MSA301_REG_INTSET1 = const(0x17)
_MSA301_REG_INTMAP0 = const(0x19)
_MSA301_REG_INTMAP1 = const(0x1A)
_MSA301_REG_TAPDUR = const(0x2A)
_MSA301_REG_TAPTH = const(0x2B)


_STANDARD_GRAVITY = 9.806


class Mode:  # pylint: disable=too-few-public-methods
    """An enum-like class representing the different modes that the MSA301 can
    use. The values can be referenced like ``Mode.NORMAL`` or ``Mode.SUSPEND``
    Possible values are

    - ``Mode.NORMAL``
    - ``Mode.LOW_POWER``
    - ``Mode.SUSPEND``
    """

    # pylint: disable=invalid-name
    NORMAL = 0b00
    LOWPOWER = 0b01
    SUSPEND = 0b010


class DataRate:  # pylint: disable=too-few-public-methods
    """An enum-like class representing the different data rates that the MSA301 can
    use. The values can be referenced like ``DataRate.RATE_1_HZ`` or ``DataRate.RATE_1000_HZ``
    Possible values are

    - ``DataRate.RATE_1_HZ``
    - ``DataRate.RATE_1_95_HZ``
    - ``DataRate.RATE_3_9_HZ``
    - ``DataRate.RATE_7_81_HZ``
    - ``DataRate.RATE_15_63_HZ``
    - ``DataRate.RATE_31_25_HZ``
    - ``DataRate.RATE_62_5_HZ``
    - ``DataRate.RATE_125_HZ``
    - ``DataRate.RATE_250_HZ``
    - ``DataRate.RATE_500_HZ``
    - ``DataRate.RATE_1000_HZ``
    """

    RATE_1_HZ = 0b0000  # 1 Hz
    RATE_1_95_HZ = 0b0001  # 1.95 Hz
    RATE_3_9_HZ = 0b0010  # 3.9 Hz
    RATE_7_81_HZ = 0b0011  # 7.81 Hz
    RATE_15_63_HZ = 0b0100  # 15.63 Hz
    RATE_31_25_HZ = 0b0101  # 31.25 Hz
    RATE_62_5_HZ = 0b0110  # 62.5 Hz
    RATE_125_HZ = 0b0111  # 125 Hz
    RATE_250_HZ = 0b1000  # 250 Hz
    RATE_500_HZ = 0b1001  # 500 Hz
    RATE_1000_HZ = 0b1010  # 1000 Hz


class BandWidth:  # pylint: disable=too-few-public-methods
    """An enum-like class representing the different bandwidths that the MSA301 can
    use. The values can be referenced like ``BandWidth.WIDTH_1_HZ`` or ``BandWidth.RATE_500_HZ``
    Possible values are

    - ``BandWidth.RATE_1_HZ``
    - ``BandWidth.RATE_1_95_HZ``
    - ``BandWidth.RATE_3_9_HZ``
    - ``BandWidth.RATE_7_81_HZ``
    - ``BandWidth.RATE_15_63_HZ``
    - ``BandWidth.RATE_31_25_HZ``
    - ``BandWidth.RATE_62_5_HZ``
    - ``BandWidth.RATE_125_HZ``
    - ``BandWidth.RATE_250_HZ``
    - ``BandWidth.RATE_500_HZ``
    - ``BandWidth.RATE_1000_HZ``
    """

    WIDTH_1_95_HZ = 0b0000  # 1.95 Hz
    WIDTH_3_9_HZ = 0b0011  # 3.9 Hz
    WIDTH_7_81_HZ = 0b0100  # 7.81 Hz
    WIDTH_15_63_HZ = 0b0101  # 15.63 Hz
    WIDTH_31_25_HZ = 0b0110  # 31.25 Hz
    WIDTH_62_5_HZ = 0b0111  # 62.5 Hz
    WIDTH_125_HZ = 0b1000  # 125 Hz
    WIDTH_250_HZ = 0b1001  # 250 Hz
    WIDTH_500_HZ = 0b1010  # 500 Hz


class Range:  # pylint: disable=too-few-public-methods
    """An enum-like class representing the different acceleration measurement ranges that the
    MSA301 can use. The values can be referenced like ``Range.RANGE_2_G`` or ``Range.RANGE_16_G``
    Possible values are

    - ``Range.RANGE_2_G``
    - ``Range.RANGE_4_G``
    - ``Range.RANGE_8_G``
    - ``Range.RANGE_16_G``
    """

    RANGE_2_G = 0b00  # +/- 2g (default value)
    RANGE_4_G = 0b01  # +/- 4g
    RANGE_8_G = 0b10  # +/- 8g
    RANGE_16_G = 0b11  # +/- 16g


class Resolution:  # pylint: disable=too-few-public-methods
    """An enum-like class representing the different measurement ranges that the MSA301 can
    use. The values can be referenced like ``Range.RANGE_2_G`` or ``Range.RANGE_16_G``
    Possible values are

    - ``Resolution.RESOLUTION_14_BIT``
    - ``Resolution.RESOLUTION_12_BIT``
    - ``Resolution.RESOLUTION_10_BIT``
    - ``Resolution.RESOLUTION_8_BIT``
    """

    RESOLUTION_14_BIT = 0b00
    RESOLUTION_12_BIT = 0b01
    RESOLUTION_10_BIT = 0b10
    RESOLUTION_8_BIT = 0b11


class TapDuration:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """An enum-like class representing the options for the "double_tap_window" parameter of
    `enable_tap_detection`"""

    DURATION_50_MS = 0b000  # < 50 millis
    DURATION_100_MS = 0b001  # < 100 millis
    DURATION_150_MS = 0b010  # < 150 millis
    DURATION_200_MS = 0b011  # < 200 millis
    DURATION_250_MS = 0b100  # < 250 millis
    DURATION_375_MS = 0b101  # < 375 millis
    DURATION_500_MS = 0b110  # < 500 millis
    DURATION_700_MS = 0b111  # < 50 millis700 millis


class MSA301:  # pylint: disable=too-many-instance-attributes
    """Driver for the MSA301 Accelerometer.

    :param ~busio.I2C i2c_bus: The I2C bus the MSA is connected to.
    """

    _part_id = ROUnaryStruct(_MSA301_REG_PARTID, "<B")

    def __init__(self, i2c_bus):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, _MSA301_I2CADDR_DEFAULT)

        if self._part_id != 0x13:
            raise AttributeError("Cannot find a MSA301")

        self._disable_x = self._disable_y = self._disable_z = False
        self.power_mode = Mode.NORMAL
        self.data_rate = DataRate.RATE_500_HZ
        self.bandwidth = BandWidth.WIDTH_250_HZ
        self.range = Range.RANGE_4_G
        self.resolution = Resolution.RESOLUTION_14_BIT
        self._tap_count = 0

    _disable_x = RWBit(_MSA301_REG_ODR, 7)
    _disable_y = RWBit(_MSA301_REG_ODR, 6)
    _disable_z = RWBit(_MSA301_REG_ODR, 5)

    # _xyz_raw = ROBits(48, _MSA301_REG_OUT_X_L, 0, 6)
    _xyz_raw = Struct(_MSA301_REG_OUT_X_L, "<hhh")

    # tap INT enable and status
    _single_tap_int_en = RWBit(_MSA301_REG_INTSET0, 5)
    _double_tap_int_en = RWBit(_MSA301_REG_INTSET0, 4)
    _motion_int_status = ROUnaryStruct(_MSA301_REG_MOTIONINT, "B")

    # tap interrupt knobs
    _tap_quiet = RWBit(_MSA301_REG_TAPDUR, 7)
    _tap_shock = RWBit(_MSA301_REG_TAPDUR, 6)
    _tap_duration = RWBits(3, _MSA301_REG_TAPDUR, 0)
    _tap_threshold = RWBits(5, _MSA301_REG_TAPTH, 0)
    reg_tapdur = ROUnaryStruct(_MSA301_REG_TAPDUR, "B")

    # general settings knobs
    power_mode = RWBits(2, _MSA301_REG_POWERMODE, 6)
    bandwidth = RWBits(4, _MSA301_REG_POWERMODE, 1)
    data_rate = RWBits(4, _MSA301_REG_ODR, 0)
    range = RWBits(2, _MSA301_REG_RESRANGE, 0)
    resolution = RWBits(2, _MSA301_REG_RESRANGE, 2)

    @property
    def acceleration(self):
        """The x, y, z acceleration values returned in a 3-tuple and are in m / s ^ 2."""
        # read the 6 bytes of acceleration data

        current_range = self.range
        scale = 1.0
        if current_range == 3:
            scale = 512.0
        if current_range == 2:
            scale = 1024.0
        if current_range == 1:
            scale = 2048.0
        if current_range == 0:
            scale = 4096.0

        # shift down to the actual 14 bits and scale based on the range
        x, y, z = [((i >> 2) / scale) * _STANDARD_GRAVITY for i in self._xyz_raw]

        return (x, y, z)

    def enable_tap_detection(
        self,
        *,
        tap_count=1,
        threshold=25,
        long_initial_window=True,
        long_quiet_window=True,
        double_tap_window=TapDuration.DURATION_250_MS
    ):
        """
        Enables tap detection with configurable parameters.

        :param int tap_count: 1 to detect only single taps, or 2 to detect only double taps.\
        default is 1

        :param int threshold: A threshold for the tap detection.\
        The higher the value the less sensitive the detection. This changes based on the\
        accelerometer range. Default is 25.

        :param int long_initial_window: This sets the length of the window of time where a\
        spike in acceleration must occour in before being followed by a quiet period.\
        `True` (default) sets the value to 70ms, False to 50ms. Default is `True`

        :param int long_quiet_window: The length of the "quiet" period after an acceleration\
        spike where no more spikes can occour for a tap to be registered.\
        `True` (default) sets the value to 30ms, False to 20ms. Default is `True`.

        :param int double_tap_window: The length of time after an initial tap is registered\
        in which a second tap must be detected to count as a double tap. Setting a lower\
        value will require a faster double tap. The value must be a\
        ``TapDuration``. Default is ``TapDuration.DURATION_250_MS``.

        If you wish to set them yourself rather than using the defaults,
        you must use keyword arguments::

            msa.enable_tap_detection(tap_count=2,
                                     threshold=25,
                                     double_tap_window=TapDuration.DURATION_700_MS)

        """
        self._tap_shock = not long_initial_window
        self._tap_quiet = long_quiet_window
        self._tap_threshold = threshold
        self._tap_count = tap_count

        if double_tap_window > 7 or double_tap_window < 0:
            raise ValueError("double_tap_window must be a TapDuration")
        if tap_count == 1:
            self._single_tap_int_en = True
        elif tap_count == 2:
            self._tap_duration = double_tap_window
            self._double_tap_int_en = True
        else:
            raise ValueError("tap must be 1 for single tap, or 2 for double tap")

    @property
    def tapped(self):
        """`True` if a single or double tap was detected, depending on the value of the\
           ``tap_count`` argument passed to ``enable_tap_detection``"""
        if self._tap_count == 0:
            return False

        motion_int_status = self._motion_int_status

        if motion_int_status == 0:  # no interrupts triggered
            return False

        if self._tap_count == 1 and motion_int_status & 1 << 5:
            return True
        if self._tap_count == 2 and motion_int_status & 1 << 4:
            return True

        return False
