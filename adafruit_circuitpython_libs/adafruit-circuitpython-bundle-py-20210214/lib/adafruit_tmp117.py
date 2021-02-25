# SPDX-FileCopyrightText: Copyright (c) 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_tmp117`
================================================================================

CircuitPython library for the TI TMP117 Temperature sensor

* Author(s): Bryan Siepert

parts based on SparkFun_TMP117_Arduino_Library by Madison Chodikov @ SparkFun Electronics:
https://github.com/sparkfunX/Qwiic_TMP117
https://github.com/sparkfun/SparkFun_TMP117_Arduino_Library

Implementation Notes
--------------------

**Hardware:**

* `Adafruit TMP117 Breakout <https:#www.adafruit.com/product/PID_HERE>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

import time
from collections import namedtuple
from micropython import const
import adafruit_bus_device.i2c_device as i2c_device
from adafruit_register.i2c_struct import ROUnaryStruct, UnaryStruct

from adafruit_register.i2c_bit import RWBit, ROBit
from adafruit_register.i2c_bits import RWBits, ROBits

__version__ = "1.0.1"
__repo__ = "https:#github.com/adafruit/Adafruit_CircuitPython_TMP117.git"


_I2C_ADDR = 0x48  # default I2C Address
_TEMP_RESULT = const(0x00)
_CONFIGURATION = const(0x01)
_T_HIGH_LIMIT = const(0x02)
_T_LOW_LIMIT = const(0x03)
_EEPROM_UL = const(0x04)
_EEPROM1 = const(0x05)
_EEPROM2 = const(0x06)
_TEMP_OFFSET = const(0x07)
_EEPROM3 = const(0x08)
_DEVICE_ID = const(0x0F)
_DEVICE_ID_VALUE = 0x0117
_TMP117_RESOLUTION = (
    0.0078125  # Resolution of the device, found on (page 1 of datasheet)
)

_CONTINUOUS_CONVERSION_MODE = 0b00  # Continuous Conversion Mode
_ONE_SHOT_MODE = 0b11  # One Shot Conversion Mode
_SHUTDOWN_MODE = 0b01  # Shutdown Conversion Mode

AlertStatus = namedtuple("AlertStatus", ["high_alert", "low_alert"])


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


class AverageCount(CV):
    """Options for `averaged_measurements`"""


AverageCount.add_values(
    (
        ("AVERAGE_1X", 0b00, 1, None),
        ("AVERAGE_8X", 0b01, 8, None),
        ("AVERAGE_32X", 0b10, 32, None),
        ("AVERAGE_64X", 0b11, 64, None),
    )
)


class MeasurementDelay(CV):
    """Options for `measurement_delay`"""


MeasurementDelay.add_values(
    (
        ("DELAY_0_0015_S", 0b000, 0.00155, None),
        ("DELAY_0_125_S", 0b01, 0.125, None),
        ("DELAY_0_250_S", 0b010, 0.250, None),
        ("DELAY_0_500_S", 0b011, 0.500, None),
        ("DELAY_1_S", 0b100, 1, None),
        ("DELAY_4_S", 0b101, 4, None),
        ("DELAY_8_S", 0b110, 8, None),
        ("DELAY_16_S", 0b111, 16, None),
    )
)


class AlertMode(CV):
    """Options for `alert_mode`. See `alert_mode` for more information."""


AlertMode.add_values(
    (("WINDOW", 0, "Window", None), ("HYSTERESIS", 1, "Hysteresis", None))
)


class MeasurementMode(CV):
    """Options for `measurement_mode`. See `measurement_mode` for more information."""


MeasurementMode.add_values(
    (
        ("CONTINUOUS", 0, "Continuous", None),
        ("ONE_SHOT", 2, "One shot", None),
        ("SHUTDOWN", 1, "Shutdown", None),
    )
)


class TMP117:
    """Library for the TI TMP117 high-accuracy temperature sensor"""

    _part_id = ROUnaryStruct(_DEVICE_ID, ">H")
    _raw_temperature = ROUnaryStruct(_TEMP_RESULT, ">h")
    _raw_high_limit = UnaryStruct(_T_HIGH_LIMIT, ">h")
    _raw_low_limit = UnaryStruct(_T_LOW_LIMIT, ">h")
    _raw_temperature_offset = UnaryStruct(_TEMP_OFFSET, ">h")

    # these three bits will clear on read in some configurations, so we read them together
    _alert_status_data_ready = ROBits(3, _CONFIGURATION, 13, 2, False)
    _eeprom_busy = ROBit(_CONFIGURATION, 12, 2, False)
    _mode = RWBits(2, _CONFIGURATION, 10, 2, False)

    _raw_measurement_delay = RWBits(3, _CONFIGURATION, 7, 2, False)
    _raw_averaged_measurements = RWBits(2, _CONFIGURATION, 5, 2, False)

    _raw_alert_mode = RWBit(_CONFIGURATION, 4, 2, False)  # T/nA bits in the datasheet
    _int_active_high = RWBit(_CONFIGURATION, 3, 2, False)
    _data_ready_int_en = RWBit(_CONFIGURATION, 2, 2, False)
    _soft_reset = RWBit(_CONFIGURATION, 1, 2, False)

    def __init__(self, i2c_bus, address=_I2C_ADDR):

        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        if self._part_id != _DEVICE_ID_VALUE:
            raise AttributeError("Cannot find a TMP117")
        # currently set when `alert_status` is read, but not exposed
        self.reset()
        self.initialize()

    def reset(self):
        """Reset the sensor to its unconfigured power-on state"""
        self._soft_reset = True

    def initialize(self):
        """Configure the sensor with sensible defaults. `initialize` is primarily provided to be
        called after `reset`, however it can also be used to easily set the sensor to a known
        configuration"""
        # Datasheet specifies that reset will finish in 2ms however by default the first
        # conversion will be averaged 8x and take 1s
        # TODO: sleep depending on current averaging config
        self._set_mode_and_wait_for_measurement(_CONTINUOUS_CONVERSION_MODE)  # one shot
        time.sleep(1)

    @property
    def temperature(self):
        """The current measured temperature in degrees celcius"""

        return self._read_temperature()

    @property
    def temperature_offset(self):
        """User defined temperature offset to be added to measurements from `temperature`

        .. code-block::python3

            # SPDX-FileCopyrightText: 2020 Bryan Siepert, written for Adafruit Industries
            #
            # SPDX-License-Identifier: Unlicense
            import time
            import board
            import busio
            import adafruit_tmp117

            i2c = busio.I2C(board.SCL, board.SDA)

            tmp117 = adafruit_tmp117.TMP117(i2c)

            print("Temperature without offset: %.2f degrees C" % tmp117.temperature)
            tmp117.temperature_offset = 10.0
            while True:
                print("Temperature w/ offset: %.2f degrees C" % tmp117.temperature)
                time.sleep(1)

        """
        return self._raw_temperature_offset * _TMP117_RESOLUTION

    @temperature_offset.setter
    def temperature_offset(self, value):
        if value > 256 or value < -256:
            raise AttributeError("temperature_offset must be ")
        scaled_offset = int(value / _TMP117_RESOLUTION)
        self._raw_temperature_offset = scaled_offset

    @property
    def high_limit(self):
        """The high temperature limit in degrees celcius. When the measured temperature exceeds this
        value, the `high_alert` attribute of the `alert_status` property will be True. See the
        documentation for `alert_status` for more information"""

        return self._raw_high_limit * _TMP117_RESOLUTION

    @high_limit.setter
    def high_limit(self, value):
        if value > 256 or value < -256:
            raise AttributeError("high_limit must be from 255 to -256")
        scaled_limit = int(value / _TMP117_RESOLUTION)
        self._raw_high_limit = scaled_limit

    @property
    def low_limit(self):
        """The low  temperature limit in degrees celcius. When the measured temperature goes below
        this value, the `low_alert` attribute of the `alert_status` property will be True. See the
        documentation for `alert_status` for more information"""

        return self._raw_low_limit * _TMP117_RESOLUTION

    @low_limit.setter
    def low_limit(self, value):
        if value > 256 or value < -256:
            raise AttributeError("low_limit must be from 255 to -256")
        scaled_limit = int(value / _TMP117_RESOLUTION)
        self._raw_low_limit = scaled_limit

    @property
    def alert_status(self):
        """The current triggered status of the high and low temperature alerts as a AlertStatus
        named tuple with attributes for the triggered status of each alert.

        .. code-block :: python3

            import board
            import busio
            import adafruit_tmp117
            i2c = busio.I2C(board.SCL, board.SDA)

            tmp117 = adafruit_tmp117.TMP117(i2c)

            tmp117.high_limit = 25
            tmp117.low_limit = 10

            print("High limit", tmp117.high_limit)
            print("Low limit", tmp117.low_limit)

            # Try changing `alert_mode`  to see how it modifies the behavior of the alerts.
            # tmp117.alert_mode = AlertMode.WINDOW #default
            # tmp117.alert_mode = AlertMode.HYSTERESIS

            print("Alert mode:", AlertMode.string[tmp117.alert_mode])
            print("")
            print("")
            while True:
                print("Temperature: %.2f degrees C" % tmp117.temperature)
                alert_status = tmp117.alert_status
                print("High alert:", alert_status.high_alert)
                print("Low alert:", alert_status.low_alert)
                print("")
                time.sleep(1)

        """
        high_alert, low_alert, *_ = self._read_status()
        return AlertStatus(high_alert=high_alert, low_alert=low_alert)

    @property
    def averaged_measurements(self):
        """The number of measurements that are taken and averaged before updating the temperature
        measurement register. A larger number will reduce measurement noise but may also affect
        the rate at which measurements are updated, depending on the value of `measurement_delay`

        Note that each averaged measurement takes 15.5ms which means that larger numbers of averaged
        measurements may make the delay between new reported measurements to exceed the delay set
        by `measurement_delay`

        .. code-block::python3

            import time
            import board
            import busio
            from adafruit_tmp117 import TMP117, AverageCount

            i2c = busio.I2C(board.SCL, board.SDA)

            tmp117 = TMP117(i2c)

            # uncomment different options below to see how it affects the reported temperature
            # tmp117.averaged_measurements = AverageCount.AVERAGE_1X
            # tmp117.averaged_measurements = AverageCount.AVERAGE_8X
            # tmp117.averaged_measurements = AverageCount.AVERAGE_32X
            # tmp117.averaged_measurements = AverageCount.AVERAGE_64X

            print(
                "Number of averaged samples per measurement:",
                AverageCount.string[tmp117.averaged_measurements],
            )
            print("")

            while True:
                print("Temperature:", tmp117.temperature)
                time.sleep(0.1)

        """
        return self._raw_averaged_measurements

    @averaged_measurements.setter
    def averaged_measurements(self, value):
        if not AverageCount.is_valid(value):
            raise AttributeError("averaged_measurements must be an `AverageCount`")
        self._raw_averaged_measurements = value

    @property
    def measurement_mode(self):
        """Sets the measurement mode, specifying the behavior of how often measurements are taken.
        `measurement_mode` must be one of:

+----------------------------------------+------------------------------------------------------+
| Mode                                   | Behavior                                             |
+========================================+======================================================+
| :py:const:`MeasurementMode.CONTINUOUS` | Measurements are made at the interval determined by  |
|                                        |                                                      |
|                                        | `averaged_measurements` and `measurement_delay`.     |
|                                        |                                                      |
|                                        | `temperature` returns the most recent measurement    |
+----------------------------------------+------------------------------------------------------+
| :py:const:`MeasurementMode.ONE_SHOT`   | Take a single measurement with the current number of |
|                                        |                                                      |
|                                        | `averaged_measurements` and switch to                |
|                                        | :py:const:`SHUTDOWN` when                            |
|                                        |                                                      |
|                                        | finished.                                            |
|                                        |                                                      |
|                                        |                                                      |
|                                        | `temperature` will return the new measurement until  |
|                                        |                                                      |
|                                        | `measurement_mode` is set to :py:const:`CONTINUOUS`  |
|                                        | or :py:const:`ONE_SHOT` is                           |
|                                        |                                                      |
|                                        | set again.                                           |
+----------------------------------------+------------------------------------------------------+
| :py:const:`MeasurementMode.SHUTDOWN`   | The sensor is put into a low power state and no new  |
|                                        |                                                      |
|                                        | measurements are taken.                              |
|                                        |                                                      |
|                                        | `temperature` will return the last measurement until |
|                                        |                                                      |
|                                        | a new `measurement_mode` is selected.                |
+----------------------------------------+------------------------------------------------------+

        """
        return self._mode

    @measurement_mode.setter
    def measurement_mode(self, value):
        if not MeasurementMode.is_valid(value):
            raise AttributeError("measurement_mode must be a `MeasurementMode` ")

        self._set_mode_and_wait_for_measurement(value)

    @property
    def measurement_delay(self):
        """The minimum amount of time between measurements in seconds. Must be a
        `MeasurementDelay`. The specified amount may be exceeded depending on the
        current setting off `averaged_measurements` which determines the minimum
        time needed between reported measurements.

        .. code-block::python3

            import time
            import board
            import busio
            from adafruit_tmp117 import TMP117, AverageCount, MeasurementDelay

            i2c = busio.I2C(board.SCL, board.SDA)

            tmp117 = TMP117(i2c)

            # uncomment different options below to see how it affects the reported temperature

            # tmp117.measurement_delay = MeasurementDelay.DELAY_0_0015_S
            # tmp117.measurement_delay = MeasurementDelay.DELAY_0_125_S
            # tmp117.measurement_delay = MeasurementDelay.DELAY_0_250_S
            # tmp117.measurement_delay = MeasurementDelay.DELAY_0_500_S
            # tmp117.measurement_delay = MeasurementDelay.DELAY_1_S
            # tmp117.measurement_delay = MeasurementDelay.DELAY_4_S
            # tmp117.measurement_delay = MeasurementDelay.DELAY_8_S
            # tmp117.measurement_delay = MeasurementDelay.DELAY_16_S

            print("Minimum time between measurements:",
            MeasurementDelay.string[tmp117.measurement_delay], "seconds")

            print("")

            while True:
                print("Temperature:", tmp117.temperature)
                time.sleep(0.01)

        """

        return self._raw_measurement_delay

    @measurement_delay.setter
    def measurement_delay(self, value):
        if not MeasurementDelay.is_valid(value):
            raise AttributeError("measurement_delay must be a `MeasurementDelay`")
        self._raw_measurement_delay = value

    def take_single_measurememt(self):
        """Perform a single measurement cycle respecting the value of `averaged_measurements`,
        returning the measurement once complete. Once finished the sensor is placed into a low power
        state until :py:meth:`take_single_measurement` or `temperature` are read.

        **Note:** if `averaged_measurements` is set to a high value there will be a notable
        delay before the temperature measurement is returned while the sensor takes the required
        number of measurements
        """

        return self._set_mode_and_wait_for_measurement(_ONE_SHOT_MODE)  # one shot

    @property
    def alert_mode(self):
        """Sets the behavior of the `low_limit`, `high_limit`, and `alert_status` properties.

        When set to :py:const:`AlertMode.WINDOW`, the `high_limit` property will unset when the
        measured temperature goes below `high_limit`. Similarly `low_limit` will be True or False
        depending on if the measured temperature is below (`False`) or above(`True`) `low_limit`.

        When set to :py:const:`AlertMode.HYSTERESIS`, the `high_limit` property will be set to
        `False` when the measured temperature goes below `low_limit`. In this mode, the `low_limit`
        property of `alert_status` will not be set.

        The default is :py:const:`AlertMode.WINDOW`"""

        return self._raw_alert_mode

    @alert_mode.setter
    def alert_mode(self, value):
        if not AlertMode.is_valid(value):
            raise AttributeError("alert_mode must be an `AlertMode`")
        self._raw_alert_mode = value

    def _set_mode_and_wait_for_measurement(self, mode):

        self._mode = mode
        # poll for data ready
        while not self._read_status()[2]:
            time.sleep(0.001)

        return self._read_temperature()

    # eeprom write enable to set defaults for limits and config
    # requires context manager or something to perform a general call reset

    def _read_status(self):
        # 3 bits: high_alert, low_alert, data_ready
        status_flags = self._alert_status_data_ready

        high_alert = 0b100 & status_flags > 0
        low_alert = 0b010 & status_flags > 0
        data_ready = 0b001 & status_flags > 0

        return (high_alert, low_alert, data_ready)

    def _read_temperature(self):
        return self._raw_temperature * _TMP117_RESOLUTION
