# SPDX-FileCopyrightText: 2018 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_adxl34x`
====================================================

A driver for the ADXL34x 3-axis accelerometer family

* Author(s): Bryan Siepert

Based on drivers by K. Townsend and Tony DiCola

Implementation Notes
--------------------

**Hardware:**
https://www.adafruit.com/product/1231

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

from micropython import const
from adafruit_bus_device import i2c_device

try:
    from struct import unpack
except ImportError:
    from ustruct import unpack
__version__ = "1.11.6"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ADXL34x.git"
_ADXL345_DEFAULT_ADDRESS = const(0x53)  # Assumes ALT address pin low

# Conversion factors
_ADXL345_MG2G_MULTIPLIER = 0.004  # 4mg per lsb
_STANDARD_GRAVITY = 9.80665  # earth standard gravity

_REG_DEVID = const(0x00)  # Device ID
_REG_THRESH_TAP = const(0x1D)  # Tap threshold
_REG_OFSX = const(0x1E)  # X-axis offset
_REG_OFSY = const(0x1F)  # Y-axis offset
_REG_OFSZ = const(0x20)  # Z-axis offset
_REG_DUR = const(0x21)  # Tap duration
_REG_LATENT = const(0x22)  # Tap latency
_REG_WINDOW = const(0x23)  # Tap window
_REG_THRESH_ACT = const(0x24)  # Activity threshold
_REG_THRESH_INACT = const(0x25)  # Inactivity threshold
_REG_TIME_INACT = const(0x26)  # Inactivity time
_REG_ACT_INACT_CTL = const(0x27)  # Axis enable control for [in]activity detection
_REG_THRESH_FF = const(0x28)  # Free-fall threshold
_REG_TIME_FF = const(0x29)  # Free-fall time
_REG_TAP_AXES = const(0x2A)  # Axis control for single/double tap
_REG_ACT_TAP_STATUS = const(0x2B)  # Source for single/double tap
_REG_BW_RATE = const(0x2C)  # Data rate and power mode control
_REG_POWER_CTL = const(0x2D)  # Power-saving features control
_REG_INT_ENABLE = const(0x2E)  # Interrupt enable control
_REG_INT_MAP = const(0x2F)  # Interrupt mapping control
_REG_INT_SOURCE = const(0x30)  # Source of interrupts
_REG_DATA_FORMAT = const(0x31)  # Data format control
_REG_DATAX0 = const(0x32)  # X-axis data 0
_REG_DATAX1 = const(0x33)  # X-axis data 1
_REG_DATAY0 = const(0x34)  # Y-axis data 0
_REG_DATAY1 = const(0x35)  # Y-axis data 1
_REG_DATAZ0 = const(0x36)  # Z-axis data 0
_REG_DATAZ1 = const(0x37)  # Z-axis data 1
_REG_FIFO_CTL = const(0x38)  # FIFO control
_REG_FIFO_STATUS = const(0x39)  # FIFO status
_INT_SINGLE_TAP = const(0b01000000)  # SINGLE_TAP bit
_INT_DOUBLE_TAP = const(0b00100000)  # DOUBLE_TAP bit
_INT_ACT = const(0b00010000)  # ACT bit
_INT_INACT = const(0b00001000)  # INACT bit
_INT_FREE_FALL = const(0b00000100)  # FREE_FALL  bit


class DataRate:  # pylint: disable=too-few-public-methods
    """An enum-like class representing the possible data rates.
    Possible values are

    - ``DataRate.RATE_3200_HZ``
    - ``DataRate.RATE_1600_HZ``
    - ``DataRate.RATE_800_HZ``
    - ``DataRate.RATE_400_HZ``
    - ``DataRate.RATE_200_HZ``
    - ``DataRate.RATE_100_HZ``
    - ``DataRate.RATE_50_HZ``
    - ``DataRate.RATE_25_HZ``
    - ``DataRate.RATE_12_5_HZ``
    - ``DataRate.RATE_6_25HZ``
    - ``DataRate.RATE_3_13_HZ``
    - ``DataRate.RATE_1_56_HZ``
    - ``DataRate.RATE_0_78_HZ``
    - ``DataRate.RATE_0_39_HZ``
    - ``DataRate.RATE_0_20_HZ``
    - ``DataRate.RATE_0_10_HZ``

    """

    RATE_3200_HZ = const(0b1111)  # 1600Hz Bandwidth   140mA IDD
    RATE_1600_HZ = const(0b1110)  #  800Hz Bandwidth    90mA IDD
    RATE_800_HZ = const(0b1101)  #  400Hz Bandwidth   140mA IDD
    RATE_400_HZ = const(0b1100)  #  200Hz Bandwidth   140mA IDD
    RATE_200_HZ = const(0b1011)  #  100Hz Bandwidth   140mA IDD
    RATE_100_HZ = const(0b1010)  #   50Hz Bandwidth   140mA IDD
    RATE_50_HZ = const(0b1001)  #   25Hz Bandwidth    90mA IDD
    RATE_25_HZ = const(0b1000)  # 12.5Hz Bandwidth    60mA IDD
    RATE_12_5_HZ = const(0b0111)  # 6.25Hz Bandwidth    50mA IDD
    RATE_6_25HZ = const(0b0110)  # 3.13Hz Bandwidth    45mA IDD
    RATE_3_13_HZ = const(0b0101)  # 1.56Hz Bandwidth    40mA IDD
    RATE_1_56_HZ = const(0b0100)  # 0.78Hz Bandwidth    34mA IDD
    RATE_0_78_HZ = const(0b0011)  # 0.39Hz Bandwidth    23mA IDD
    RATE_0_39_HZ = const(0b0010)  # 0.20Hz Bandwidth    23mA IDD
    RATE_0_20_HZ = const(0b0001)  # 0.10Hz Bandwidth    23mA IDD
    RATE_0_10_HZ = const(0b0000)  # 0.05Hz Bandwidth    23mA IDD (default value)


class Range:  # pylint: disable=too-few-public-methods
    """An enum-like class representing the possible measurement ranges in +/- G.

    Possible values are

    - ``Range.RANGE_16_G``
    - ``Range.RANGE_8_G``
    - ``Range.RANGE_4_G``
    - ``Range.RANGE_2_G``

    """

    RANGE_16_G = const(0b11)  # +/- 16g
    RANGE_8_G = const(0b10)  # +/- 8g
    RANGE_4_G = const(0b01)  # +/- 4g
    RANGE_2_G = const(0b00)  # +/- 2g (default value)


class ADXL345:
    """Driver for the ADXL345 3 axis accelerometer

    :param ~busio.I2C i2c_bus: The I2C bus the ADXL345 is connected to.
    :param address: The I2C device address for the sensor. Default is ``0x53``.

    """

    def __init__(self, i2c, address=_ADXL345_DEFAULT_ADDRESS):

        self._i2c = i2c_device.I2CDevice(i2c, address)
        self._buffer = bytearray(6)
        # set the 'measure' bit in to enable measurement
        self._write_register_byte(_REG_POWER_CTL, 0x08)
        self._write_register_byte(_REG_INT_ENABLE, 0x0)

        self._enabled_interrupts = {}
        self._event_status = {}

    @property
    def acceleration(self):
        """The x, y, z acceleration values returned in a 3-tuple in m / s ^ 2."""
        x, y, z = unpack("<hhh", self._read_register(_REG_DATAX0, 6))
        x = x * _ADXL345_MG2G_MULTIPLIER * _STANDARD_GRAVITY
        y = y * _ADXL345_MG2G_MULTIPLIER * _STANDARD_GRAVITY
        z = z * _ADXL345_MG2G_MULTIPLIER * _STANDARD_GRAVITY
        return (x, y, z)

    @property
    def events(self):
        """
        ``events`` will return a dictionary with a key for each event type that has been enabled.
        The possible keys are:

        +------------+----------------------------------------------------------------------------+
        | Key        | Description                                                                |
        +============+============================================================================+
        | ``tap``    | True if a tap was detected recently. Whether it's looking for a single or  |
        |            | double tap is determined by the tap param of `enable_tap_detection`        |
        +------------+----------------------------------------------------------------------------+
        | ``motion`` | True if the sensor has seen acceleration above the threshold               |
        |            | set with `enable_motion_detection`.                                        |
        +------------+----------------------------------------------------------------------------+
        |``freefall``| True if the sensor was in freefall. Parameters are set when enabled with   |
        |            | `enable_freefall_detection`                                                |
        +------------+----------------------------------------------------------------------------+


        """

        interrupt_source_register = self._read_clear_interrupt_source()

        self._event_status.clear()

        for event_type, value in self._enabled_interrupts.items():
            if event_type == "motion":
                self._event_status[event_type] = (
                    interrupt_source_register & _INT_ACT > 0
                )
            if event_type == "tap":
                if value == 1:
                    self._event_status[event_type] = (
                        interrupt_source_register & _INT_SINGLE_TAP > 0
                    )
                else:
                    self._event_status[event_type] = (
                        interrupt_source_register & _INT_DOUBLE_TAP > 0
                    )
            if event_type == "freefall":
                self._event_status[event_type] = (
                    interrupt_source_register & _INT_FREE_FALL > 0
                )

        return self._event_status

    def enable_motion_detection(self, *, threshold=18):
        """
        The activity detection parameters.

        :param int threshold: The value that acceleration on any axis must exceed to\
        register as active. The scale factor is 62.5 mg/LSB.

        If you wish to set them yourself rather than using the defaults,
        you must use keyword arguments::

            accelerometer.enable_motion_detection(threshold=20)

        """
        active_interrupts = self._read_register_unpacked(_REG_INT_ENABLE)

        self._write_register_byte(_REG_INT_ENABLE, 0x0)  # disable interrupts for setup
        self._write_register_byte(
            _REG_ACT_INACT_CTL, 0b01110000
        )  # enable activity on X,Y,Z
        self._write_register_byte(_REG_THRESH_ACT, threshold)
        self._write_register_byte(_REG_INT_ENABLE, _INT_ACT)  # Inactive interrupt only

        active_interrupts |= _INT_ACT
        self._write_register_byte(_REG_INT_ENABLE, active_interrupts)
        self._enabled_interrupts["motion"] = True

    def disable_motion_detection(self):
        """
        Disable motion detection
        """
        active_interrupts = self._read_register_unpacked(_REG_INT_ENABLE)
        active_interrupts &= ~_INT_ACT
        self._write_register_byte(_REG_INT_ENABLE, active_interrupts)
        self._enabled_interrupts.pop("motion")

    def enable_freefall_detection(self, *, threshold=10, time=25):
        """
        Freefall detection parameters:

        :param int threshold: The value that acceleration on all axes must be under to\
        register as dropped. The scale factor is 62.5 mg/LSB.

        :param int time: The amount of time that acceleration on all axes must be less than\
        ``threshhold`` to register as dropped. The scale factor is 5 ms/LSB. Values between 100 ms\
        and 350 ms (20 to 70) are recommended.

        If you wish to set them yourself rather than using the defaults,
        you must use keyword arguments::

            accelerometer.enable_freefall_detection(time=30)

       """

        active_interrupts = self._read_register_unpacked(_REG_INT_ENABLE)

        self._write_register_byte(_REG_INT_ENABLE, 0x0)  # disable interrupts for setup
        self._write_register_byte(_REG_THRESH_FF, threshold)
        self._write_register_byte(_REG_TIME_FF, time)

        # add FREE_FALL to the active interrupts and set them to re-enable
        active_interrupts |= _INT_FREE_FALL
        self._write_register_byte(_REG_INT_ENABLE, active_interrupts)
        self._enabled_interrupts["freefall"] = True

    def disable_freefall_detection(self):
        "Disable freefall detection"
        active_interrupts = self._read_register_unpacked(_REG_INT_ENABLE)
        active_interrupts &= ~_INT_FREE_FALL
        self._write_register_byte(_REG_INT_ENABLE, active_interrupts)
        self._enabled_interrupts.pop("freefall")

    def enable_tap_detection(
        self, *, tap_count=1, threshold=20, duration=50, latency=20, window=255
    ):  # pylint: disable=line-too-long
        """
        The tap detection parameters.

        :param int tap_count: 1 to detect only single taps, and 2 to detect only double taps.

        :param int threshold: A threshold for the tap detection. The scale factor is 62.5 mg/LSB\
        The higher the value the less sensitive the detection.


        :param int duration: This caps the duration of the impulse above ``threshhold``.\
        Anything above ``duration`` won't register as a tap. The scale factor is 625 µs/LSB

        :param int latency(double tap only): The length of time after the initial impulse\
        falls below ``threshold`` to start the window looking for a second impulse.\
        The scale factor is 1.25 ms/LSB.

        :param int window(double tap only): The length of the window in which to look for a\
        second tap. The scale factor is 1.25 ms/LSB

        If you wish to set them yourself rather than using the defaults,
        you must use keyword arguments::

            accelerometer.enable_tap_detection(duration=30, threshold=25)

        """
        active_interrupts = self._read_register_unpacked(_REG_INT_ENABLE)

        self._write_register_byte(_REG_INT_ENABLE, 0x0)  # disable interrupts for setup
        self._write_register_byte(
            _REG_TAP_AXES, 0b00000111
        )  # enable X, Y, Z axes for tap
        self._write_register_byte(_REG_THRESH_TAP, threshold)
        self._write_register_byte(_REG_DUR, duration)

        if tap_count == 1:
            active_interrupts |= _INT_SINGLE_TAP
            self._write_register_byte(_REG_INT_ENABLE, active_interrupts)
            self._enabled_interrupts["tap"] = 1
        elif tap_count == 2:
            self._write_register_byte(_REG_LATENT, latency)
            self._write_register_byte(_REG_WINDOW, window)

            active_interrupts |= _INT_DOUBLE_TAP
            self._write_register_byte(_REG_INT_ENABLE, active_interrupts)
            self._enabled_interrupts["tap"] = 2
        else:
            raise ValueError(
                "tap must be 0 to disable, 1 for single tap, or 2 for double tap"
            )

    def disable_tap_detection(self):
        "Disable tap detection"
        active_interrupts = self._read_register_unpacked(_REG_INT_ENABLE)
        active_interrupts &= ~_INT_SINGLE_TAP
        active_interrupts &= ~_INT_DOUBLE_TAP
        self._write_register_byte(_REG_INT_ENABLE, active_interrupts)
        self._enabled_interrupts.pop("tap")

    @property
    def data_rate(self):
        """The data rate of the sensor."""
        rate_register = self._read_register_unpacked(_REG_BW_RATE)
        return rate_register & 0x0F

    @data_rate.setter
    def data_rate(self, val):
        self._write_register_byte(_REG_BW_RATE, val)

    @property
    def range(self):
        """The measurement range of the sensor."""
        range_register = self._read_register_unpacked(_REG_DATA_FORMAT)
        return range_register & 0x03

    @range.setter
    def range(self, val):
        # read the current value of the data format register
        format_register = self._read_register_unpacked(_REG_DATA_FORMAT)

        # clear the bottom 4 bits and update the data rate
        format_register &= ~0x0F
        format_register |= val

        # Make sure that the FULL-RES bit is enabled for range scaling
        format_register |= 0x08

        # write the updated values
        self._write_register_byte(_REG_DATA_FORMAT, format_register)

    def _read_clear_interrupt_source(self):
        return self._read_register_unpacked(_REG_INT_SOURCE)

    def _read_register_unpacked(self, register):
        return unpack("<b", self._read_register(register, 1))[0]

    def _read_register(self, register, length):
        self._buffer[0] = register & 0xFF
        with self._i2c as i2c:
            i2c.write(self._buffer, start=0, end=1)
            i2c.readinto(self._buffer, start=0, end=length)
            return self._buffer[0:length]

    def _write_register_byte(self, register, value):
        self._buffer[0] = register & 0xFF
        self._buffer[1] = value & 0xFF
        with self._i2c as i2c:
            i2c.write(self._buffer, start=0, end=2)


class ADXL343(ADXL345):
    """
    Stub class for the ADXL343 3-axis accelerometer
    """
