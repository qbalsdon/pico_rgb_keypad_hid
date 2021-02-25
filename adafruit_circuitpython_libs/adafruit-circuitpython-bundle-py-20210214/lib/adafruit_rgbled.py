# SPDX-FileCopyrightText: 2019 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rgbled`
================================================================================

CircuitPython driver for RGB LEDs

* Author(s): Brent Rubell

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's SimpleIO library: https://github.com/adafruit/Adafruit_CircuitPython_SimpleIO
"""
from pulseio import PWMOut
from simpleio import map_range

__version__ = "1.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RGBLED.git"


class RGBLED:
    """
    Creates a RGBLED object given three physical pins or PWMOut objects.

    :param red_pin: The physical pin connected to a red LED anode.
    :type ~microcontroller.Pin: Microcontroller's red_pin.
    :type pulseio.PWMOut: PWMOut object associated with red_pin.
    :type PWMChannel: PCA9685 PWM channel associated with red_pin.
    :param green_pin: The physical pin connected to a green LED anode.
    :type ~microcontroller.Pin: Microcontroller's green_pin.
    :type pulseio.PWMOut: PWMOut object associated with green_pin.
    :type PWMChannel: PCA9685 PWM channel associated with green_pin.
    :param blue_pin: The physical pin connected to a blue LED anode.
    :type ~microcontroller.Pin: Microcontroller's blue_pin.
    :type pulseio.PWMOut: PWMOut object associated with blue_pin.
    :type PWMChannel: PCA9685 PWM channel associated with blue_pin.
    :param bool invert_pwm: False if the RGB LED is common cathode,
        true if the RGB LED is common anode.

    Example for setting a RGB LED using a RGB Tuple (Red, Green, Blue):

    .. code-block:: python

        import board
        import adafruit_rgbled

        RED_LED = board.D5
        GREEN_LED = board.D6
        BLUE_LED = board.D7

        # Create a RGB LED object
        led = adafruit_rgbled.RGBLED(RED_LED, BLUE_LED, GREEN_LED)
        led.color = (255, 0, 0)

    Example for setting a RGB LED using a 24-bit integer (hex syntax):

    .. code-block:: python

        import board
        import adafruit_rgbled

        RED_LED = board.D5
        GREEN_LED = board.D6
        BLUE_LED = board.D7

        # Create a RGB LED object
        led = adafruit_rgbled.RGBLED(RED_LED, BLUE_LED, GREEN_LED)
        led.color = 0x100000

    Example for setting a RGB LED using a ContextManager:

    .. code-block:: python

        import board
        import adafruit_rgbled
        with adafruit_rgbled.RGBLED(board.D5, board.D6, board.D7) as rgb_led:
            rgb_led.color = (255, 0, 0)

    Example for setting a common-anode RGB LED using a ContextManager:

    .. code-block:: python

        import board
        import adafruit_rgbled
        with adafruit_rgbled.RGBLED(board.D5, board.D6, board.D7, invert_pwm=True) as rgb_led:
            rgb_led.color = (0, 255, 0)

    """

    def __init__(self, red_pin, green_pin, blue_pin, invert_pwm=False):
        self._rgb_led_pins = [red_pin, green_pin, blue_pin]
        for i in range(len(self._rgb_led_pins)):
            if hasattr(self._rgb_led_pins[i], "frequency"):
                self._rgb_led_pins[i].duty_cycle = 0
            elif str(type(self._rgb_led_pins[i])) == "<class 'Pin'>":
                self._rgb_led_pins[i] = PWMOut(self._rgb_led_pins[i])
                self._rgb_led_pins[i].duty_cycle = 0
            else:
                raise TypeError("Must provide a pin, PWMOut, or PWMChannel.")
        self._invert_pwm = invert_pwm
        self._current_color = (0, 0, 0)
        self.color = self._current_color

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.deinit()

    def deinit(self):
        """Turn the LEDs off, deinit pwmout and release hardware resources."""
        for pin in self._rgb_led_pins:
            pin.deinit()  # pylint: disable=no-member
        self._current_color = (0, 0, 0)

    @property
    def color(self):
        """Returns the RGB LED's current color."""
        return self._current_color

    @color.setter
    def color(self, value):
        """Sets the RGB LED to a desired color.
        :param type value: RGB LED desired value - can be a RGB tuple or a 24-bit integer.
        """
        self._current_color = value
        if isinstance(value, tuple):
            for i in range(0, 3):
                color = int(map_range(value[i], 0, 255, 0, 65535))
                if self._invert_pwm:
                    color -= 65535
                self._rgb_led_pins[i].duty_cycle = abs(color)
        elif isinstance(value, int):
            if value >> 24:
                raise ValueError("Only bits 0->23 valid for integer input")
            r = value >> 16
            g = (value >> 8) & 0xFF
            b = value & 0xFF
            rgb = [r, g, b]
            for color in range(0, 3):
                rgb[color] = int(map_range(rgb[color], 0, 255, 0, 65535))
                if self._invert_pwm:
                    rgb[color] -= 65535
                self._rgb_led_pins[color].duty_cycle = abs(rgb[color])
        else:
            raise ValueError("Color must be a tuple or 24-bit integer value.")
