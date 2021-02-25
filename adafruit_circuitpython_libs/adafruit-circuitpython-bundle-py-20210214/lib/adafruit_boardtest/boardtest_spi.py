# SPDX-FileCopyrightText: 2018 Shawn Hymel for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_boardtest.boardtest_spi`
====================================================
Performs random writes and reads to SPI EEPROM.

Run this script as its own main.py to individually run the test, or compile
with mpy-cross and call from separate test script.

* Author(s): Shawn Hymel for Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

* `Microchip 25AA040A SPI EEPROM <https://www.digikey.com/product-detail/en/\
microchip-technology/25AA040A-I-P/25AA040A-I-P-ND/1212469>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library:
  https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

import random
import time

import board
import digitalio
import busio

__version__ = "1.2.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BoardTest.git"

# Constants
MOSI_PIN_NAME = "MOSI"
MISO_PIN_NAME = "MISO"
SCK_PIN_NAME = "SCK"
CS_PIN_NAME = "D2"
BAUD_RATE = 100000  # Bits per second
NUM_SPI_TESTS = 10  # Number of times to write and read EEPROM values

# Microchip 25AA040A EEPROM SPI commands and bits
EEPROM_SPI_WRSR = 0x01
EEPROM_SPI_WRITE = 0x02
EEPROM_SPI_READ = 0x03
EEPROM_SPI_WRDI = 0x04
EEPROM_SPI_RDSR = 0x05
EEPROM_SPI_WREN = 0x06
EEPROM_SPI_WIP_BIT = 0
EEPROM_SPI_MAX_ADDR = 255  # Self-imposed max memory address
EEPROM_I2C_MAX_ADDR = 255  # Self-imposed max memory address

# Test result strings
PASS = "PASS"
FAIL = "FAIL"
NA = "N/A"

# Wait for WIP bit to go low
def _eeprom_spi_wait(spi, csel, timeout=1.0):

    # Continually read from STATUS register
    timestamp = time.monotonic()
    while time.monotonic() < timestamp + timeout:

        # Perfrom RDSR operation
        csel.value = False
        result = bytearray(1)
        spi.write(bytearray([EEPROM_SPI_RDSR]))
        spi.readinto(result)
        csel.value = True

        # Mask out and compare WIP bit
        if (result[0] & (1 << EEPROM_SPI_WIP_BIT)) == 0:
            return True

    return False


# Write to address. Returns status (True for successful write, False otherwise)
def _eeprom_spi_write_byte(spi, csel, address, data, timeout=1.0):

    # Make sure address is only one byte:
    if address > 255:
        return False

    # Make sure data is only one byte:
    if data > 255:
        return False

    # Wait for WIP to be low
    if not _eeprom_spi_wait(spi, csel, timeout):
        return False

    # Enable writing
    csel.value = False
    spi.write(bytearray([EEPROM_SPI_WREN]))
    csel.value = True

    # Write to address
    csel.value = False
    spi.write(bytearray([EEPROM_SPI_WRITE, address, data]))
    csel.value = True

    return True


# Read from address. Returns tuple [status, result]
def _eeprom_spi_read_byte(spi, csel, address, timeout=1.0):

    # Make sure address is only one byte:
    if address > 255:
        return False, bytearray()

    # Wait for WIP to be low
    if not _eeprom_spi_wait(spi, csel, timeout):
        return False, bytearray()

    # Read byte from address
    csel.value = False
    result = bytearray(1)
    spi.write(bytearray([EEPROM_SPI_READ, address]))
    spi.readinto(result)
    csel.value = True

    return True, result


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
    :return: tuple(str, list[str]): test result followed by list of pins tested
    """

    # Write values to SPI EEPROM and verify the values match
    if list(set(pins).intersection(set([mosi_pin, miso_pin, sck_pin]))):

        # Tell user to connect EEPROM chip
        print("Connect a Microchip 25AA040A EEPROM SPI chip.")
        print("Connect " + cs_pin + " to the CS pin on the 25AA040.")
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

        # Wait for SPI lock
        while not spi.try_lock():
            pass
        spi.configure(baudrate=BAUD_RATE, phase=0, polarity=0)

        # Pick a random address, write to it, read from it, and see if they match
        pass_test = True
        for _ in range(NUM_SPI_TESTS):

            # Randomly pick an address and a data value (one byte)
            mem_addr = random.randint(0, EEPROM_SPI_MAX_ADDR)
            mem_data = random.randint(0, 255)
            print("Address:\t" + hex(mem_addr))
            print("Writing:\t" + hex(mem_data))

            # Try writing this random value to the random address
            result = _eeprom_spi_write_byte(spi, csel, mem_addr, mem_data)
            if not result:
                print("FAIL: SPI could not communicate")
                pass_test = False
                break

            # Try reading the written value back from EEPRom
            result = _eeprom_spi_read_byte(spi, csel, mem_addr)
            print("Read:\t\t" + hex(result[1][0]))
            print()
            if not result[0]:
                print("FAIL: SPI could not communicate")
                pass_test = False
                break

            # Compare the read value to the original value
            if result[1][0] != mem_data:
                print("FAIL: Data does not match")
                pass_test = False
                break

        # Release SPI pins
        spi.deinit()

        # Return results
        if pass_test:
            return PASS, [mosi_pin, miso_pin, sck_pin]

        return FAIL, [mosi_pin, miso_pin, sck_pin]

    # Else (no pins found)
    print("No SPI pins found")
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
