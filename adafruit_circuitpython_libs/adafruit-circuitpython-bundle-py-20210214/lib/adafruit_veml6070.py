# SPDX-FileCopyrightText: 2018 Michael Schroeder(sommersoft)
#
# SPDX-License-Identifier: MIT

#  This CircuitPython library is based on Limor Fried's Arduino
#  library for the Adafruit VEML6070 UV Sensor Breakout.
#  License information from that library is included below.
#
#  Designed specifically to work with the VEML6070 sensor from Adafruit
#  ----> https://www.adafruit.com/products/2899
#
#  These sensors use I2C to communicate, 2 pins are required to
#  interface.
#
#  Adafruit invests time and resources providing this open source code,
#  please support Adafruit and open-source hardware by purchasing
#  products from Adafruit!
#
#  Arduino Library: Written by Limor Fried/Ladyada for Adafruit Industries.
#  MIT license, all text above must be included in any redistribution
#  https://github.com/adafruit/Adafruit_VEML6070

"""
`adafruit_veml6070` - VEML6070 UV Sensor
====================================================

CircuitPython library to support VEML6070 UV Index sensor.

* Author(s): Limor Fried & Michael Schroeder

Implementation Notes
--------------------

**Hardware:**

* Adafruit `VEML6070 UV Index Sensor Breakout
  <https://www.adafruit.com/products/2899>`_ (Product ID: 2899)

**Software and Dependencies:**

* Adafruit CircuitPython firmware (2.2.0+) for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

**Notes:**

#.  Datasheet: https://cdn-learn.adafruit.com/assets/assets/000/032/482/original/veml6070.pdf

"""

__version__ = "3.1.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_VEML6070.git"

from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const


# Set I2C addresses:
_VEML6070_ADDR_ARA = const(0x18 >> 1)
_VEML6070_ADDR_CMD = const(0x70 >> 1)
_VEML6070_ADDR_LOW = const(0x71 >> 1)
_VEML6070_ADDR_HIGH = const(0x73 >> 1)

# Integration Time dictionary. [0] is the byte setting; [1] is the risk
# level divisor.
_VEML6070_INTEGRATION_TIME = {
    "VEML6070_HALF_T": [0x00, 0],
    "VEML6070_1_T": [0x01, 1],
    "VEML6070_2_T": [0x02, 2],
    "VEML6070_4_T": [0x03, 4],
}

# UV Risk Level dictionary. [0],[1] are the lower and uppper bounds of the range
_VEML6070_RISK_LEVEL = {
    "LOW": [0, 560],
    "MODERATE": [561, 1120],
    "HIGH": [1121, 1494],
    "VERY HIGH": [1495, 2054],
    "EXTREME": [2055, 9999],
}


class VEML6070:
    """
    Driver base for the VEML6070 UV Light Sensor

    :param i2c_bus: The `busio.I2C` object to use. This is the only required parameter.
    :param str _veml6070_it: The integration time you'd like to set initially. Availble
                         options: ``VEML6070_HALF_T``, ``VEML6070_1_T``, ``VEML6070_2_T``, and
                         ``VEML6070_4_T``. The higher the '_x_' value, the more accurate
                         the reading is (at the cost of less samples per reading).
                         Defaults to ``VEML6070_1_T`` if parameter not passed. To change
                         setting after intialization, use
                         ``[veml6070].set_integration_time(new_it)``.
    :param bool ack: The inital setting of ``ACKnowledge`` on alert. Defaults to ``False``
                     if parameter not passed. To change setting after intialization,
                     use ``[veml6070].set_ack(new_ack)``.

    Example:

    .. code-block:: python

        from board import *
        import busio, veml6070, time

        with busio.I2C(SCL, SDA) as i2c:
            uv = veml6070.VEML6070(i2c, 'VEML6070_1_T', True)

            # take 10 readings
            for j in range(10):
                uv_raw = uv.uv_raw
                risk_level = uv.get_index(uv_raw)
                print('Reading: ', uv_raw, ' | Risk Level: ', risk_level)
                time.sleep(1)
    """

    def __init__(self, i2c_bus, _veml6070_it="VEML6070_1_T", ack=False):
        # Check if the IT is valid
        if _veml6070_it not in _VEML6070_INTEGRATION_TIME:
            raise ValueError(
                "Integration Time invalid. Valid values are: ",
                _VEML6070_INTEGRATION_TIME.keys(),
            )

        # Check if ACK is valid
        if ack not in (True, False):
            raise ValueError("ACK must be 'True' or 'False'.")

        # Passed checks; set self values
        self._ack = int(ack)
        self._ack_thd = 0x00
        self._it = _veml6070_it

        # Latch the I2C addresses
        self.i2c_cmd = I2CDevice(i2c_bus, _VEML6070_ADDR_CMD)
        self.i2c_low = I2CDevice(i2c_bus, _VEML6070_ADDR_LOW)
        self.i2c_high = I2CDevice(i2c_bus, _VEML6070_ADDR_HIGH)

        # Initialize the VEML6070
        ara_buf = bytearray(1)
        try:
            with I2CDevice(i2c_bus, _VEML6070_ADDR_ARA) as ara:
                ara.readinto(ara_buf)
        except ValueError:  # the ARA address is never valid? datasheet error?
            pass
        self.buf = bytearray(1)
        self.buf[0] = (
            self._ack << 5 | _VEML6070_INTEGRATION_TIME[self._it][0] << 2 | 0x02
        )
        with self.i2c_cmd as i2c_cmd:
            i2c_cmd.write(self.buf)

    @property
    def uv_raw(self):
        """
        Reads and returns the value of the UV intensity.
        """
        buffer = bytearray(2)
        with self.i2c_low as i2c_low:
            i2c_low.readinto(buffer, end=1)

        with self.i2c_high as i2c_high:
            i2c_high.readinto(buffer, start=1)

        return buffer[1] << 8 | buffer[0]

    @property
    def ack(self):
        """
        Turns on or off the ACKnowledge function of the sensor. The ACK function will send
        a signal to the host when the value of the sensed UV light changes beyond the
        programmed threshold.
        """
        return self._ack

    @ack.setter
    def ack(self, new_ack):
        if new_ack != bool(new_ack):
            raise ValueError("ACK must be 'True' or 'False'.")
        self._ack = int(new_ack)
        self.buf[0] = (
            self._ack << 5
            | self._ack_thd << 4
            | _VEML6070_INTEGRATION_TIME[self._it][0] << 2
            | 0x02
        )
        with self.i2c_cmd as i2c_cmd:
            i2c_cmd.write(self.buf)

    @property
    def ack_threshold(self):
        """
        The ACKnowledge Threshold, which alerts the host controller to value changes
        greater than the threshold. Available settings are: ``0`` = 102 steps; ``1`` = 145 steps.
        ``0`` is the default setting.
        """
        return self._ack_thd

    @ack_threshold.setter
    def ack_threshold(self, new_ack_thd):
        if new_ack_thd not in (0, 1):
            raise ValueError("ACK Threshold must be '0' or '1'.")
        self._ack_thd = int(new_ack_thd)
        self.buf[0] = (
            self._ack << 5
            | self._ack_thd << 4
            | _VEML6070_INTEGRATION_TIME[self._it][0] << 2
            | 0x02
        )
        with self.i2c_cmd as i2c_cmd:
            i2c_cmd.write(self.buf)

    @property
    def integration_time(self):
        """
        The Integration Time of the sensor, which is the refresh interval of the
        sensor. The higher the refresh interval, the more accurate the reading is (at
        the cost of less sampling). The available settings are: ``VEML6070_HALF_T``,
        ``VEML6070_1_T``, ``VEML6070_2_T``, ``VEML6070_4_T``.
        """
        return self._it

    @integration_time.setter
    def integration_time(self, new_it):
        if new_it not in _VEML6070_INTEGRATION_TIME:
            raise ValueError(
                "Integration Time invalid. Valid values are: ",
                _VEML6070_INTEGRATION_TIME.keys(),
            )

        self._it = new_it
        self.buf[0] = (
            self._ack << 5
            | self._ack_thd << 4
            | _VEML6070_INTEGRATION_TIME[new_it][0] << 2
            | 0x02
        )
        with self.i2c_cmd as i2c_cmd:
            i2c_cmd.write(self.buf)

    def sleep(self):
        """
        Puts the VEML6070 into sleep ('shutdown') mode. Datasheet claims a current draw
        of 1uA while in shutdown.
        """
        self.buf[0] = 0x03
        with self.i2c_cmd as i2c_cmd:
            i2c_cmd.write(self.buf)

    def wake(self):
        """
        Wakes the VEML6070 from sleep. ``[veml6070].uv_raw`` will also wake from sleep.
        """
        self.buf[0] = (
            self._ack << 5
            | self._ack_thd << 4
            | _VEML6070_INTEGRATION_TIME[self._it][0] << 2
            | 0x02
        )
        with self.i2c_cmd as i2c_cmd:
            i2c_cmd.write(self.buf)

    def get_index(self, _raw):
        """
        Calculates the UV Risk Level based on the captured UV reading. Requres the ``_raw``
        argument (from ``veml6070.uv_raw``). Risk level is available for Integration Times (IT)
        1, 2, & 4. The result is automatically scaled to the current IT setting.

            LEVEL*        UV Index
            =====         ========
            LOW             0-2
            MODERATE        3-5
            HIGH            6-7
            VERY HIGH       8-10
            EXTREME         >=11

        * Not to be considered as accurate condition reporting.
          Calculation is based on VEML6070 Application Notes:
          http://www.vishay.com/docs/84310/designingveml6070.pdf

        """

        # get the divisor for the current IT
        div = _VEML6070_INTEGRATION_TIME[self._it][1]
        if div == 0:
            raise ValueError(
                "[veml6070].get_index only available for Integration Times 1, 2, & 4.",
                "Use [veml6070].set_integration_time(new_it) to change the Integration Time.",
            )

        # adjust the raw value using the divisor, then loop through the Risk Level dict
        # to find which range the adjusted raw value is in.
        raw_adj = int(_raw / div)
        for levels in _VEML6070_RISK_LEVEL:
            tmp_range = range(
                _VEML6070_RISK_LEVEL[levels][0], _VEML6070_RISK_LEVEL[levels][1]
            )
            if raw_adj in tmp_range:
                risk = levels
                break

        return risk
