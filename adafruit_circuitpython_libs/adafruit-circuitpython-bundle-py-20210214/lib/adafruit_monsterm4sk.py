# SPDX-FileCopyrightText: Copyright (c) 2020 Foamyguy for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_monsterm4sk`
================================================================================

Helper library for the Monster M4sk device. Allows usage of screens and other built-in hardware.


* Author(s): Foamyguy

Implementation Notes
--------------------

**Hardware:**

* `MONSTER M4SK <https://www.adafruit.com/product/4343>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


# * Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
# * Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

# imports
import time
import board
import pulseio
import busio
import digitalio
from adafruit_seesaw.seesaw import Seesaw
import displayio
import touchio
from adafruit_st7789 import ST7789
import adafruit_lis3dh

__version__ = "0.1.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MONSTERM4SK.git"

# Seesaw pin numbers
SS_LIGHTSENSOR_PIN = 2  # "through-hole" light sensor near left eye
SS_VCCSENSOR_PIN = 3
SS_BACKLIGHT_PIN = 5  # left screen backlight
SS_TFTRESET_PIN = 8  # left screen reset

# buttons above left eye. Match silkscreen :)
SS_SWITCH1_PIN = 9
SS_SWITCH2_PIN = 10
SS_SWITCH3_PIN = 11


class MonsterM4sk:
    """Represents a single Monster M4sk

            The terms "left" and "right" are always used from the
            perspective of looking out of the mask.
            The right screen is the one USB port directly above it.
           """

    def __init__(self, i2c=None):
        """
            :param i2c: The I2C bus to use, will try board.I2C()
                if not supplied

        """
        displayio.release_displays()

        if i2c is None:
            i2c = board.I2C()

        # set up on-board seesaw
        self._ss = Seesaw(i2c)

        # set up seesaw pins
        self._ss.pin_mode(SS_TFTRESET_PIN, self._ss.OUTPUT)  # left sceen reset

        # buttons abolve left eye
        self._ss.pin_mode(SS_SWITCH1_PIN, self._ss.INPUT_PULLUP)
        self._ss.pin_mode(SS_SWITCH2_PIN, self._ss.INPUT_PULLUP)
        self._ss.pin_mode(SS_SWITCH3_PIN, self._ss.INPUT_PULLUP)

        # light sensor near left eye
        self._ss.pin_mode(SS_LIGHTSENSOR_PIN, self._ss.INPUT)

        # Manual reset for left screen
        self._ss.digital_write(SS_TFTRESET_PIN, False)
        time.sleep(0.01)
        self._ss.digital_write(SS_TFTRESET_PIN, True)
        time.sleep(0.01)

        # Left backlight pin, on the seesaw
        self._ss.pin_mode(SS_BACKLIGHT_PIN, self._ss.OUTPUT)
        # backlight on full brightness
        self._ss.analog_write(SS_BACKLIGHT_PIN, 255)

        # Left screen spi bus
        left_spi = busio.SPI(board.LEFT_TFT_SCK, MOSI=board.LEFT_TFT_MOSI)
        left_tft_cs = board.LEFT_TFT_CS
        left_tft_dc = board.LEFT_TFT_DC

        left_display_bus = displayio.FourWire(
            left_spi, command=left_tft_dc, chip_select=left_tft_cs  # Reset on Seesaw
        )

        self.left_display = ST7789(left_display_bus, width=240, height=240, rowstart=80)

        # right backlight on board
        self.right_backlight = pulseio.PWMOut(
            board.RIGHT_TFT_LITE, frequency=5000, duty_cycle=0
        )
        # full brightness
        self.right_backlight.duty_cycle = 65535

        # right display spi bus
        right_spi = busio.SPI(board.RIGHT_TFT_SCK, MOSI=board.RIGHT_TFT_MOSI)
        right_tft_cs = board.RIGHT_TFT_CS
        right_tft_dc = board.RIGHT_TFT_DC

        right_display_bus = displayio.FourWire(
            right_spi,
            command=right_tft_dc,
            chip_select=right_tft_cs,
            reset=board.RIGHT_TFT_RST,  # reset on board
        )

        self.right_display = ST7789(
            right_display_bus, width=240, height=240, rowstart=80
        )

        # setup accelerometer
        if i2c is not None:
            int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)
            try:
                self._accelerometer = adafruit_lis3dh.LIS3DH_I2C(
                    i2c, address=0x19, int1=int1
                )
            except ValueError:
                self._accelerometer = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)

        # touchio on nose
        self.nose = touchio.TouchIn(board.NOSE)

        # can be iffy, depending on environment and person.
        # User code can tweak if needed.
        self.nose.threshold = 180

    @property
    def acceleration(self):
        """Accelerometer data, +/- 2G sensitivity.

        This example initializes the mask and prints the accelerometer data.

        .. code-block:: python

            import adafruit_monsterm4sk
            mask = adafruit_monsterm4sk.MonsterM4sk(i2c=board.I2C())
            print(mask.acceleration)

        """
        return (
            self._accelerometer.acceleration
            if self._accelerometer is not None
            else None
        )

    @property
    def light(self):
        """Light sensor data.

        This example initializes the mask and prints the light sensor data.

        .. code-block:: python

                import adafruit_monsterm4sk
                mask = adafruit_monsterm4sk.MonsterM4sk(i2c=board.I2C())
                print(mask.light)

        """
        return self._ss.analog_read(SS_LIGHTSENSOR_PIN)

    @property
    def buttons(self):
        """Buttons dictionary.

        This example initializes the mask and prints when the S9 button
        is pressed down.

        .. code-block:: python

                import adafruit_monsterm4sk
                mask = adafruit_monsterm4sk.MonsterM4sk(i2c=board.I2C())

                while True:
                    if mask.buttons["S9"]:
                        print("Button S9 pressed!")

        """

        return {
            "S9": self._ss.digital_read(SS_SWITCH1_PIN) is False,
            "S10": self._ss.digital_read(SS_SWITCH2_PIN) is False,
            "S11": self._ss.digital_read(SS_SWITCH3_PIN) is False,
        }

    @property
    def boop(self):
        """Nose touch sense.

        This example initializes the mask and prints when the nose touch pad
        is being touched.

        .. code-block:: python

                import adafruit_monsterm4sk
                mask = adafruit_monsterm4sk.MonsterM4sk(i2c=board.I2C())

                while True:
                    if mask.boop:
                        print("Nose touched!")

        """
        return self.nose.value
