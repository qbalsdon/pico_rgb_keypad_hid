# SPDX-FileCopyrightText: 2019 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_veml7700`
================================================================================

CircuitPython driver for VEML7700 high precision I2C ambient light sensor.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit VEML7700 <https://www.adafruit.com/products>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

from micropython import const
import adafruit_bus_device.i2c_device as i2cdevice
from adafruit_register.i2c_struct import UnaryStruct, ROUnaryStruct
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_bit import RWBit, ROBit

__version__ = "1.1.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_VEML7700.git"


class VEML7700:
    """Driver for the VEML7700 ambient light sensor.

    :param busio.I2C i2c_bus: The I2C bus the VEML7700 is connected to.

    """

    # Ambient light sensor gain settings
    ALS_GAIN_1 = const(0x0)
    ALS_GAIN_2 = const(0x1)
    ALS_GAIN_1_8 = const(0x2)
    ALS_GAIN_1_4 = const(0x3)

    # Ambient light integration time settings

    ALS_25MS = const(0xC)
    ALS_50MS = const(0x8)
    ALS_100MS = const(0x0)
    ALS_200MS = const(0x1)
    ALS_400MS = const(0x2)
    ALS_800MS = const(0x3)

    # Gain value integers
    gain_values = {
        ALS_GAIN_2: 2,
        ALS_GAIN_1: 1,
        ALS_GAIN_1_4: 0.25,
        ALS_GAIN_1_8: 0.125,
    }

    # Integration time value integers
    integration_time_values = {
        ALS_25MS: 25,
        ALS_50MS: 50,
        ALS_100MS: 100,
        ALS_200MS: 200,
        ALS_400MS: 400,
        ALS_800MS: 800,
    }

    # ALS - Ambient light sensor high resolution output data
    light = ROUnaryStruct(0x04, "<H")
    """Ambient light data.

    This example prints the ambient light data. Cover the sensor to see the values change.

    .. code-block:: python

        import time
        import board
        import busio
        import adafruit_veml7700

        i2c = busio.I2C(board.SCL, board.SDA)
        veml7700 = adafruit_veml7700.VEML7700(i2c)

        while True:
            print("Ambient light:", veml7700.light)
            time.sleep(0.1)
    """

    # WHITE - White channel output data
    white = ROUnaryStruct(0x05, "<H")
    """White light data.

    This example prints the white light data. Cover the sensor to see the values change.

    .. code-block:: python

        import time
        import board
        import busio
        import adafruit_veml7700

        i2c = busio.I2C(board.SCL, board.SDA)
        veml7700 = adafruit_veml7700.VEML7700(i2c)

        while True:
            print("White light:", veml7700.white)
            time.sleep(0.1)
    """

    # ALS_CONF_0 - ALS gain, integration time, interrupt and shutdown.
    light_shutdown = RWBit(0x00, 0, register_width=2)
    """Ambient light sensor shutdown. When ``True``, ambient light sensor is disabled."""
    light_interrupt = RWBit(0x00, 1, register_width=2)
    """Enable interrupt. ``True`` to enable, ``False`` to disable."""
    light_gain = RWBits(2, 0x00, 11, register_width=2)
    """Ambient light gain setting. Gain settings are 2, 1, 1/4 and 1/8. Settings options are:
    ALS_GAIN_2, ALS_GAIN_1, ALS_GAIN_1_4, ALS_GAIN_1_8.

    This example sets the ambient light gain to 2 and prints the ambient light sensor data.

    .. code-block:: python

        import time
        import board
        import busio
        import adafruit_veml7700

        i2c = busio.I2C(board.SCL, board.SDA)
        veml7700 = adafruit_vcnl4040.VCNL4040(i2c)

        veml7700.light_gain = veml7700.ALS_GAIN_2

        while True:
            print("Ambient light:", veml7700.light)
            time.sleep(0.1)

    """
    light_integration_time = RWBits(4, 0x00, 6, register_width=2)
    """Ambient light integration time setting. Longer time has higher sensitivity. Can be:
    ALS_25MS, ALS_50MS, ALS_100MS, ALS_200MS, ALS_400MS, ALS_800MS.

    This example sets the ambient light integration time to 400ms and prints the ambient light
    sensor data.

    .. code-block:: python

        import time
        import board
        import busio
        import adafruit_veml7700

        i2c = busio.I2C(board.SCL, board.SDA)
        veml7700 = adafruit_vcnl4040.VCNL4040(i2c)

        veml7700.light_integration_time = veml7700.ALS_400MS

        while True:
            print("Ambient light:", veml7700.light)
            time.sleep(0.1)

    """

    # ALS_WH - ALS high threshold window setting
    light_high_threshold = UnaryStruct(0x01, "<H")
    """Ambient light sensor interrupt high threshold setting."""
    # ALS_WL - ALS low threshold window setting
    light_low_threshold = UnaryStruct(0x02, "<H")
    """Ambient light sensor interrupt low threshold setting."""
    # ALS_INT - ALS INT trigger event
    light_interrupt_high = ROBit(0x06, 14, register_width=2)
    """Ambient light high threshold interrupt flag. Triggered when high threshold exceeded."""
    light_interrupt_low = ROBit(0x06, 15, register_width=2)
    """Ambient light low threshold interrupt flag. Triggered when low threshold exceeded."""

    def __init__(self, i2c_bus, address=0x10):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, address)
        self.light_shutdown = False  # Enable the ambient light sensor

    def integration_time_value(self):
        """Integration time value in integer form. Used for calculating ``resolution``."""
        integration_time = self.light_integration_time
        return self.integration_time_values[integration_time]

    def gain_value(self):
        """Gain value in integer form. Used for calculating ``resolution``."""
        gain = self.light_gain
        return self.gain_values[gain]

    def resolution(self):
        """Calculate the ``resolution`` necessary to calculate lux. Based on integration time and
        gain settings."""
        resolution_at_max = 0.0036
        gain_max = 2
        integration_time_max = 800

        if (
            self.gain_value() == gain_max
            and self.integration_time_value() == integration_time_max
        ):
            return resolution_at_max
        return (
            resolution_at_max
            * (integration_time_max / self.integration_time_value())
            * (gain_max / self.gain_value())
        )

    @property
    def lux(self):
        """Light value in lux.

        This example prints the light data in lux. Cover the sensor to see the values change.

        .. code-block:: python

            import time
            import board
            import busio
            import adafruit_veml7700

            i2c = busio.I2C(board.SCL, board.SDA)
            veml7700 = adafruit_veml7700.VEML7700(i2c)

            while True:
                print("Lux:", veml7700.lux)
                time.sleep(0.1)
        """
        return self.resolution() * self.light
