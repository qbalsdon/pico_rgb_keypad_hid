# SPDX-FileCopyrightText: 2019 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_vcnl4040`
================================================================================

A CircuitPython library for the VCNL4040 proximity and ambient light sensor.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

.. * `Adafruit VCNL4040 <https://www.adafruit.com/products>`_

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
from adafruit_register.i2c_bit import RWBit

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_VCNL4040.git"


class VCNL4040:  # pylint: disable=too-few-public-methods
    """Driver for the VCNL4040 proximity and ambient light sensor.

    :param busio.I2C i2c_bus: The I2C bus the VCNL4040 is connected to.

    """

    # Ambient light sensor integration times
    ALS_80MS = const(0x0)
    ALS_160MS = const(0x1)
    ALS_320MS = const(0x2)
    ALS_640MS = const(0x3)

    # Proximity sensor integration times
    PS_1T = const(0x0)
    PS_1_5T = const(0x1)
    PS_2T = const(0x2)
    PS_2_5T = const(0x3)
    PS_3T = const(0x4)
    PS_3_5T = const(0x5)
    PS_4T = const(0x6)
    PS_8T = const(0x7)

    # LED current settings
    LED_50MA = const(0x0)
    LED_75MA = const(0x1)
    LED_100MA = const(0x2)
    LED_120MA = const(0x3)
    LED_140MA = const(0x4)
    LED_160MA = const(0x5)
    LED_180MA = const(0x6)
    LED_200MA = const(0x7)

    # LED duty cycle settings
    LED_1_40 = const(0x0)
    LED_1_80 = const(0x1)
    LED_1_160 = const(0x2)
    LED_1_320 = const(0x3)

    # Proximity sensor interrupt enable/disable options
    PS_INT_DISABLE = const(0x0)
    PS_INT_CLOSE = const(0x1)
    PS_INT_AWAY = const(0x2)
    PS_INT_CLOSE_AWAY = const(0x3)

    # Offsets into interrupt status register for different types
    ALS_IF_L = const(0x0D)
    ALS_IF_H = const(0x0C)
    PS_IF_CLOSE = const(0x09)
    PS_IF_AWAY = const(0x08)

    # ID_LM - Device ID, address
    _device_id = UnaryStruct(0x0C, "<H")
    """The device ID."""

    # PS_Data_LM - PS output data
    proximity = ROUnaryStruct(0x08, "<H")
    """Proximity data.

    This example prints the proximity data. Move your hand towards the sensor to see the values
    change.

    .. code-block:: python

        import time
        import board
        import busio
        import adafruit_vcnl4040

        i2c = busio.I2C(board.SCL, board.SDA)
        sensor = adafruit_vcnl4040.VCNL4040(i2c)

        while True:
            print("Proximity:", sensor.proximity)
            time.sleep(0.1)
    """

    # PS_CONF1 - PS duty ratio, integration time, persistence, enable/disable
    # PS_CONF2 - PS output resolution selection, interrupt trigger method
    # PS_CONF3 - PS smart persistence, active force mode
    proximity_shutdown = RWBit(0x03, 0, register_width=2)
    """Proximity sensor shutdown. When ``True``, proximity data is disabled."""
    proximity_integration_time = RWBits(3, 0x03, 1, register_width=2)
    """Proximity sensor integration time setting. Integration times are 1T, 1.5T, 2T, 2.5T, 3T,
    3.5T, 4T, and 8T. Options are: PS_1T, PS_1_5T, PS_2T, PS_2_5T, PS_3T, PS_3_5T, PS_4T, PS_8T.
    """
    proximity_interrupt = RWBits(2, 0x03, 8, register_width=2)
    """Interrupt enable. Interrupt setting are close, away, close and away, or disabled. Options
    are: PS_INT_DISABLE, PS_INT_CLOSE, PS_INT_AWAY, PS_INT_CLOSE_AWAY."""
    proximity_bits = RWBit(0x03, 11, register_width=2)
    """Proximity data output setting. ``0`` when proximity sensor output is 12 bits, ``1`` when
    proximity sensor output is 16 bits."""

    # PS_THDL_LM - PS low interrupt threshold setting
    proximity_low_threshold = UnaryStruct(0x06, "<H")
    """Proximity sensor interrupt low threshold setting."""
    # PS_THDH_LM - PS high interrupt threshold setting
    proximity_high_threshold = UnaryStruct(0x07, "<H")
    """Proximity sensor interrupt high threshold setting."""

    interrupt_state = ROUnaryStruct(0x0B, "<H")

    # INT_FLAG - PS interrupt flag
    @property
    def proximity_high_interrupt(self):
        """If interrupt is set to ``PS_INT_CLOSE`` or ``PS_INT_CLOSE_AWAY``, trigger event when
        proximity rises above high threshold interrupt."""
        return self._get_and_clear_cached_interrupt_state(self.PS_IF_CLOSE)

    @property
    def proximity_low_interrupt(self):
        """If interrupt is set to ``PS_INT_AWAY`` or ``PS_INT_CLOSE_AWAY``, trigger event when
        proximity drops below low threshold."""
        return self._get_and_clear_cached_interrupt_state(self.PS_IF_AWAY)

    led_current = RWBits(3, 0x04, 8, register_width=2)
    """LED current selection setting, in mA. Options are LED_50MA, LED_75MA, LED_100MA, LED_120MA,
    LED_140MA, LED_160MA, LED_180MA, LED_200MA."""

    led_duty_cycle = RWBits(2, 0x03, 6, register_width=2)
    """Proximity sensor LED duty ratio setting. Ratios are 1/40, 1/80, 1/160, and 1/320. Options
    are: LED_1_40, LED_1_80, LED_1_160, LED_1_320."""

    light = ROUnaryStruct(0x09, "<H")
    """Raw ambient light data. The raw ambient light data which will change with integration time
    and gain settings changes. Use ``lux`` to get the correctly scaled value for the current
    integration time and gain settings
    """

    @property
    def lux(self):
        """Ambient light data in lux. Represents the raw sensor data scaled according to the current
        integration time and gain settings.

        This example prints the ambient light data. Cover the sensor to see the values change.

        .. code-block:: python

            import time
            import board
            import busio
            import adafruit_vcnl4040

            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = adafruit_vcnl4040.VCNL4040(i2c)

            while True:
                print("Ambient light: %.2f lux"%sensor.lux)
                time.sleep(0.1)
        """
        return self.light * (0.1 / (1 << self.light_integration_time))

    # ALS_CONF - ALS integration time, persistence, interrupt, function enable/disable
    light_shutdown = RWBit(0x00, 0, register_width=2)
    """Ambient light sensor shutdown. When ``True``, ambient light data is disabled."""

    _light_integration_time = RWBits(2, 0x00, 6, register_width=2)

    @property
    def light_integration_time(self):
        """Ambient light sensor integration time setting. Longer time has higher sensitivity.
        Can be: ALS_80MS, ALS_160MS, ALS_320MS or ALS_640MS.

        This example sets the ambient light integration time to 640ms and prints the ambient light
        sensor data.

        .. code-block:: python

            import time
            import board
            import busio
            import adafruit_vcnl4040

            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = adafruit_vcnl4040.VCNL4040(i2c)

            sensor.light_integration_time = sensor.ALS_640MS

            while True:
                print("Ambient light:", sensor.light)
        """
        return self._light_integration_time

    @light_integration_time.setter
    def light_integration_time(self, new_it):
        from time import sleep  # pylint: disable=import-outside-toplevel

        # IT values are in 0-3 -> 80-640ms
        old_it_ms = (8 << self._light_integration_time) * 10
        new_it_ms = (8 << new_it) * 10
        it_delay_seconds = (old_it_ms + new_it_ms + 1) * 0.001

        self._light_integration_time = new_it
        sleep(it_delay_seconds)

    light_interrupt = RWBit(0x00, 1, register_width=2)
    """Ambient light sensor interrupt enable. ``True`` to enable, and ``False`` to disable."""

    # ALS_THDL_LM - ALS low interrupt threshold setting
    light_low_threshold = UnaryStruct(0x02, "<H")
    """Ambient light interrupt low threshold."""
    # ALS_THDH_LM - ALS high interrupt threshold setting
    light_high_threshold = UnaryStruct(0x01, "<H")
    """Ambient light interrupt high threshold."""
    # INT_FLAG - ALS interrupt flag

    @property
    def light_high_interrupt(self):
        """High interrupt event. Triggered when ambient light value exceeds high threshold."""
        return self._get_and_clear_cached_interrupt_state(self.ALS_IF_H)

    @property
    def light_low_interrupt(self):
        """Low interrupt event. Triggered when ambient light value drops below low threshold."""
        return self._get_and_clear_cached_interrupt_state(self.ALS_IF_L)

    _raw_white = ROUnaryStruct(0x0A, "<H")

    @property
    def white(self):
        """White light data scaled according to the current integration time and gain settings.

        This example prints the white light data. Cover the sensor to see the values change.

        .. code-block:: python

            import time
            import board
            import busio
            import adafruit_vcnl4040

            i2c = busio.I2C(board.SCL, board.SDA)
            sensor = adafruit_vcnl4040.VCNL4040(i2c)

            while True:
                print("White light:", sensor.white)
                time.sleep(0.1)
        """
        return self._raw_white * (0.1 / (1 << self.light_integration_time))

    # PS_MS - White channel enable/disable, PS mode, PS protection setting, LED current
    # White_EN - PS_MS_H, 7th bit - White channel enable/disable
    white_shutdown = RWBit(0x04, 15, register_width=2)
    """White light channel shutdown. When ``True``, white light data is disabled."""

    def __init__(self, i2c, address=0x60):
        self.i2c_device = i2cdevice.I2CDevice(i2c, address)
        if self._device_id != 0x186:
            raise RuntimeError("Failed to find VCNL4040 - check wiring!")

        self.cached_interrupt_state = {
            self.ALS_IF_L: False,
            self.ALS_IF_H: False,
            self.PS_IF_CLOSE: False,
            self.PS_IF_AWAY: False,
        }

        self.proximity_shutdown = False
        self.light_shutdown = False
        self.white_shutdown = False

    def _update_interrupt_state(self):
        interrupts = [self.PS_IF_AWAY, self.PS_IF_CLOSE, self.ALS_IF_H, self.ALS_IF_L]
        new_interrupt_state = self.interrupt_state
        for interrupt in interrupts:
            new_state = new_interrupt_state & (1 << interrupt) > 0
            if new_state:
                self.cached_interrupt_state[interrupt] = new_state

    def _get_and_clear_cached_interrupt_state(self, interrupt_offset):
        self._update_interrupt_state()
        new_interrupt_state = self.cached_interrupt_state[interrupt_offset]
        self.cached_interrupt_state[interrupt_offset] = False

        return new_interrupt_state
