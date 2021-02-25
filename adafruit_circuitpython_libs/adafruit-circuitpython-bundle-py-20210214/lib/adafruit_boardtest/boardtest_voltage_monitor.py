# SPDX-FileCopyrightText: 2018 Shawn Hymel for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_boardtest.boardtest_voltage_monitor`
====================================================
Prints out the measured voltage on any onboard voltage/battery monitor pins.
Note that some boards have an onboard voltage divider to decrease the voltage
to these pins.

Run this script as its own main.py to individually run the test, or compile
with mpy-cross and call from separate test script.

* Author(s): Shawn Hymel for Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* `Multimeter <https://www.adafruit.com/product/2034>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import board
import analogio

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BoardTest.git"

# Constants
VOLTAGE_MONITOR_PIN_NAMES = ["VOLTAGE_MONITOR", "BATTERY"]
ANALOG_REF = 3.3  # Reference analog voltage
ANALOGIN_BITS = 16  # ADC resolution (bits) for CircuitPython

# Test result strings
PASS = "PASS"
FAIL = "FAIL"
NA = "N/A"


def run_test(pins):

    """
    Prints out voltage on the battery monitor or voltage monitor pin.

    :param list[str] pins: list of pins to run the test on
    :return: tuple(str, list[str]): test result followed by list of pins tested
    """

    # Look for pins with battery monitoring names
    monitor_pins = list(set(pins).intersection(set(VOLTAGE_MONITOR_PIN_NAMES)))

    # Print out voltage found on these pins
    if monitor_pins:

        # Print out the monitor pins found
        print("Voltage monitor pins found:", end=" ")
        for pin in monitor_pins:
            print(pin, end=" ")
        print("\n")

        # Print out the voltage found on each pin
        for pin in monitor_pins:
            monitor = analogio.AnalogIn(getattr(board, pin))
            voltage = (monitor.value * ANALOG_REF) / (2 ** ANALOGIN_BITS)
            print(pin + ": {:.2f}".format(voltage) + " V")
            monitor.deinit()
        print()

        # Ask the user to check these voltages
        print("Use a multimeter to verify these voltages.")
        print(
            "Note that some battery monitor pins might have onboard "
            + "voltage dividers."
        )
        print("Do the values look reasonable? [y/n]")
        if input() == "y":
            return PASS, monitor_pins

        return FAIL, monitor_pins

    # Else (no pins found)
    print("No battery monitor pins found")
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
