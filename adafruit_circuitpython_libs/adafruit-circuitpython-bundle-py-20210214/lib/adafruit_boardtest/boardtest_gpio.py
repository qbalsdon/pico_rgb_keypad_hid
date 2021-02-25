# SPDX-FileCopyrightText: 2018 Shawn Hymel for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_boardtest.boardtest_gpio`
====================================================
Toggles all available GPIO on a board. Verify their operation with an LED,
multimeter, another microcontroller, etc.

Run this script as its own main.py to individually run the test, or compile
with mpy-cross and call from separate test script.

* Author(s): Shawn Hymel for Adafruit Industries

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import time

import board
import digitalio
import supervisor

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BoardTest.git"

# Constants
LED_ON_DELAY_TIME = 0.2  # Seconds
LED_OFF_DELAY_TIME = 0.2  # Seconds
LED_PIN_NAMES = ["L", "LED", "RED_LED", "GREEN_LED", "BLUE_LED"]

# Test result strings
PASS = "PASS"
FAIL = "FAIL"
NA = "N/A"

# Determine if given value is a number
def _is_number(val):
    try:
        float(val)
        return True
    except ValueError:
        return False


# Release pins
def _deinit_pins(gpios):
    for g in gpios:
        g.deinit()


# Toggle IO pins while waiting for answer
def _toggle_wait(gpios):

    timestamp = time.monotonic()
    led_state = False
    print("Are the pins listed above toggling? [y/n]")
    while True:
        if led_state:
            if time.monotonic() > timestamp + LED_ON_DELAY_TIME:
                led_state = False
                timestamp = time.monotonic()
        else:
            if time.monotonic() > timestamp + LED_OFF_DELAY_TIME:
                led_state = True
                timestamp = time.monotonic()
        for gpio in gpios:
            gpio.value = led_state
        if supervisor.runtime.serial_bytes_available:
            answer = input()
            return bool(answer == "y")


def run_test(pins):

    """
    Toggles all available GPIO on and off repeatedly.

    :param list[str] pins: list of pins to run the test on
    :return: tuple(str, list[str]): test result followed by list of pins tested
    """

    # Create a list of analog GPIO pins
    analog_pins = [p for p in pins if p[0] == "A" and _is_number(p[1])]

    # Create a list of digital GPIO
    digital_pins = [p for p in pins if p[0] == "D" and _is_number(p[1])]

    # Toggle LEDs if we find any
    gpio_pins = analog_pins + digital_pins
    if gpio_pins:

        # Create a list of IO objects for us to toggle
        gpios = [digitalio.DigitalInOut(getattr(board, p)) for p in gpio_pins]

        # Print out the LEDs found
        print("GPIO pins found:", end=" ")
        for pin in gpio_pins:
            print(pin, end=" ")
        print("\n")

        # Set all IO to output
        for gpio in gpios:
            gpio.direction = digitalio.Direction.OUTPUT

        # Toggle pins while waiting for user to verify LEDs blinking
        result = _toggle_wait(gpios)

        # Release pins
        _deinit_pins(gpios)

        if result:
            return PASS, gpio_pins

        return FAIL, gpio_pins

    # Else (no pins found)
    print("No GPIO pins found")
    return NA, []


def _main():

    # List out all the pins available to us
    pins = list(dir(board))
    print()
    print("All pins found:", end=" ")

    # Print pins
    for pin in pins:
        print(pin, end=" ")
    print("\n")

    # Run test
    result = run_test(pins)
    print()
    print(result[0])
    print("Pins tested: " + str(result[1]))


# Execute only if run as main.py or code.py
if __name__ == "__main__":
    _main()
