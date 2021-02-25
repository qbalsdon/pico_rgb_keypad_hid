# SPDX-FileCopyrightText: 2018 Shawn Hymel for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_boardtest.boardtest_sd`
====================================================
Performs random writes and reads to SD card over SPI.

Run this script as its own main.py to individually run the test, or compile
with mpy-cross and call from separate test script.

* Author(s): Shawn Hymel for Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* `SD Card <https://www.adafruit.com/product/1294>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit CircuitPython SD card driver:
  https://github.com/adafruit/Adafruit_CircuitPython_SD

"""
import random

import board
import busio
import digitalio
import adafruit_sdcard
import storage

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BoardTest.git"

# Constants
MOSI_PIN_NAME = "SD_MOSI"
MISO_PIN_NAME = "SD_MISO"
SCK_PIN_NAME = "SD_SCK"
CS_PIN_NAME = "SD_CS"
FILENAME = "test.txt"  # File that will be written to
BAUD_RATE = 100000  # Bits per second
NUM_UART_BYTES = 40  # Number of bytes to transmit over UART
ASCII_MIN = 0x21  # '!' Lowest ASCII char in random range (inclusive)
ASCII_MAX = 0x7E  # '~' Highest ASCII char in random range (inclusive)

# Test result strings
PASS = "PASS"
FAIL = "FAIL"
NA = "N/A"


def run_test(
    pins,
    mosi_pin=MOSI_PIN_NAME,
    miso_pin=MISO_PIN_NAME,
    sck_pin=SCK_PIN_NAME,
    cs_pin=CS_PIN_NAME,
):

    """
    Performs random writes and reads to file on attached SD card.

    :param list[str] pins: list of pins to run the test on
    :param str mosi_pin: pin name of SPI MOSI
    :param str miso_pin: pin name of SPI MISO
    :param str sck_pin: pin name of SPI SCK
    :param str cs_pin: pin name of SPI CS
    :param str filename: name of file to use as test on SD card
    :return: tuple(str, list[str]): test result followed by list of pins tested
    """

    # Write characters to file on SD card and verify they were written
    if list(set(pins).intersection(set([mosi_pin, miso_pin, sck_pin]))):

        # Tell user to connect SD card
        print("Insert SD card into holder and connect SPI lines to holder.")
        print("Connect " + cs_pin + " to the CS (DAT3) pin on the SD " + "card holder.")
        print("WARNING: " + FILENAME + " will be created or overwritten.")
        print("Press enter to continue.")
        input()

        # Configure CS pin
        csel = digitalio.DigitalInOut(getattr(board, cs_pin))
        csel.direction = digitalio.Direction.OUTPUT
        csel.value = True

        # Set up SPI
        spi = busio.SPI(
            getattr(board, sck_pin),
            MOSI=getattr(board, mosi_pin),
            MISO=getattr(board, miso_pin),
        )

        # Try to connect to the card and mount the filesystem
        try:
            sdcard = adafruit_sdcard.SDCard(spi, csel)
            vfs = storage.VfsFat(sdcard)
            storage.mount(vfs, "/sd")
        except OSError:
            print("Could not mount SD card")
            return FAIL, [mosi_pin, miso_pin, sck_pin]

        # Generate test string
        test_str = ""
        for _ in range(NUM_UART_BYTES):
            test_str += chr(random.randint(ASCII_MIN, ASCII_MAX))

        # Write test string to a text file on the card
        try:
            with open("/sd/" + FILENAME, "w") as file:
                print("Writing:\t" + test_str)
                file.write(test_str)
        except OSError:
            print("Could not write to SD card")
            return FAIL, [mosi_pin, miso_pin, sck_pin]

        # Read from test file on the card
        read_str = ""
        try:
            with open("/sd/" + FILENAME, "r") as file:
                lines = file.readlines()
                for line in lines:
                    read_str += line
            print("Read:\t\t" + read_str)
        except OSError:
            print("Could not write to SD card")
            return FAIL, [mosi_pin, miso_pin, sck_pin]

        # Release SPI
        spi.deinit()

        # Compare strings
        if read_str == test_str:
            return PASS, [mosi_pin, miso_pin, sck_pin]

        return FAIL, [mosi_pin, miso_pin, sck_pin]

    # Else (no pins found)
    print("No SD card pins found")
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
