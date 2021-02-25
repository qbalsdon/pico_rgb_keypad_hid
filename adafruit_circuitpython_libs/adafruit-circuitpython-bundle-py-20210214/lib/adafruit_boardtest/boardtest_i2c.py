# SPDX-FileCopyrightText: 2018 Shawn Hymel for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_boardtest.boardtest_i2c`
====================================================
Performs random writes and reads to I2C EEPROM.

Run this script as its own main.py to individually run the test, or compile
with mpy-cross and call from separate test script.

* Author(s): Shawn Hymel for Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* `Microchip AT24HC04B I2C EEPROM <https://www.digikey.com/product-detail/en/\
microchip-technology/AT24HC04B-PU/AT24HC04B-PU-ND/1886137>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import random
import time

import board
import busio

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BoardTest.git"

# Constants
SDA_PIN_NAME = "SDA"
SCL_PIN_NAME = "SCL"
NUM_I2C_TESTS = 10  # Number of times to write and read EEPROM values
EEPROM_I2C_MAX_ADDR = 255  # Self-imposed max memory address

# Microchip AT24HC04B EEPROM I2C address
EEPROM_I2C_ADDR = 0x50

# Test result strings
PASS = "PASS"
FAIL = "FAIL"
NA = "N/A"

# Open comms to I2C EEPROM by trying a write to memory address
def _eeprom_i2c_wait(i2c, i2c_addr, mem_addr, timeout=1.0):

    # Try to access the I2C EEPROM (it becomes unresonsive during a write)
    timestamp = time.monotonic()
    while time.monotonic() < timestamp + timeout:
        try:
            i2c.writeto(i2c_addr, bytearray([mem_addr]), end=1)
            return True
        except OSError:
            pass

    return False


# Write to address. Returns status (True for successful write, False otherwise)
def _eeprom_i2c_write_byte(i2c, i2c_addr, mem_addr, mem_data):

    # Make sure address is only one byte:
    if mem_addr > 255:
        return False

    # Make sure data is only one byte:
    if mem_data > 255:
        return False

    # Write data to memory at given address
    try:
        i2c.writeto(i2c_addr, bytearray([mem_addr, mem_data]))
    except OSError:
        return False

    return True


# Read from address. Returns tuple [status, result]
def _eeprom_i2c_read_byte(i2c, i2c_addr, mem_addr, timeout=1.0):

    # Make sure address is only one byte:
    if mem_addr > 255:
        return False, bytearray()

    # Try writing to address (EEPROM is unresponsive while writing)
    if not _eeprom_i2c_wait(i2c, i2c_addr, mem_addr, timeout):
        return False, bytearray()

    # Finish the read
    buf = bytearray(1)
    i2c.writeto_then_readfrom(i2c_addr, bytearray([mem_addr]), buf)

    return True, buf


def run_test(pins, sda_pin=SDA_PIN_NAME, scl_pin=SCL_PIN_NAME):

    """
    Performs random writes and reads to I2C EEPROM.

    :param list[str] pins: list of pins to run the test on
    :param str sda_pin: pin name of I2C SDA
    :param str scl_pin: pin name of I2C SCL
    :return: tuple(str, list[str]): test result followed by list of pins tested
    """

    # Write values to I2C EEPROM and verify the values match
    if list(set(pins).intersection(set([sda_pin, scl_pin]))):

        # Tell user to connect EEPROM chip
        print(
            "Connect a Microchip AT24HC04B EEPROM I2C chip. "
            + "Press enter to continue."
        )
        input()

        # Set up I2C
        i2c = busio.I2C(getattr(board, scl_pin), getattr(board, sda_pin))

        # Wait for I2C lock
        while not i2c.try_lock():
            pass

        # Pick a random address, write to it, read from it, and see if they match
        pass_test = True
        for _ in range(NUM_I2C_TESTS):

            # Randomly pick an address and a data value (one byte)
            mem_addr = random.randint(0, EEPROM_I2C_MAX_ADDR)
            mem_data = random.randint(0, 255)
            print("Address:\t" + hex(mem_addr))
            print("Writing:\t" + hex(mem_data))

            # Try writing this random value to the random address
            result = _eeprom_i2c_write_byte(i2c, EEPROM_I2C_ADDR, mem_addr, mem_data)
            if not result:
                print("FAIL: I2C could not communicate")
                pass_test = False
                break

            # Try reading the written value back from EEPROM
            result = _eeprom_i2c_read_byte(i2c, EEPROM_I2C_ADDR, mem_addr)
            print("Read:\t\t" + hex(result[1][0]))
            print()
            if not result[0]:
                print("FAIL: I2C could not communicate")
                pass_test = False
                break

            # Compare the read value to the original value
            if result[1][0] != mem_data:
                print("FAIL: Data does not match")
                pass_test = False
                break

        # Release I2C pins
        i2c.deinit()

        # Store results
        if pass_test:
            return PASS, [sda_pin, scl_pin]

        return FAIL, [sda_pin, scl_pin]

    # Else (no pins found)
    print("No I2C pins found")
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
