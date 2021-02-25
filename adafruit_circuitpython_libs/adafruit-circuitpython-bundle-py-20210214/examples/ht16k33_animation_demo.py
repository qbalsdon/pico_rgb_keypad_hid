# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
    Test script for display animations on an HT16K33 with alphanumeric display

    The display must be initialized with auto_write=False.
"""

from time import sleep
import board
import busio
from adafruit_ht16k33.segments import Seg14x4

#
#   Segment bits on the HT16K33 with alphanumeric display.
#
#   Add the values of the segments you need to create a bitmask
#

N = 16384
M = 8192
L = 4096
K = 2048
J = 1024
I = 512
H = 256
G2 = 128
G1 = 64
F = 32
E = 16
D = 8
C = 4
B = 2
A = 1

#   The number of seconds to delay between writing segments
DEFAULT_CHAR_DELAY_SEC = 0.2

#   The number of cycles to go for each animation
DEFAULT_CYCLES = 5

#   Brightness of the display (0 to 15)
DEFAULT_DISPLAY_BRIGHTNESS = 0.3

#   Initialize the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

#   Initialize the HT16K33 with alphanumeric display featherwing.
#
#   You MUST set auto_write=False
display = Seg14x4(i2c, auto_write=False)
display.brightness = DEFAULT_DISPLAY_BRIGHTNESS


def animate(digits, bitmasks, delay=DEFAULT_CHAR_DELAY_SEC, auto_write=True):
    """
    Main driver for all alphanumeric display animations (WIP!!!)
        Param: digits - a list of the digits to write to, in order, like [0, 1, 3]. The digits are
            0 to 3 starting at the left most digit.
        Param: bitmasks - a list of the bitmasks to write, in sequence, to the specified digits.
        Param: delay - The delay, in seconds (or fractions of), between writing bitmasks to a digit.
        Param: auto_write - Whether to actually write to the display immediately or not.

        Returns: Nothing
    """
    if not isinstance(digits, list):
        raise ValueError("The first parameter MUST be a list!")
    if not isinstance(bitmasks, list):
        raise ValueError("The second parameter MUST be a list!")
    if delay < 0:
        raise ValueError("The delay between frames must be positive!")
    for dig in digits:
        if not 0 <= dig <= 3:
            raise ValueError(
                "Digit value must be \
            an integer in the range: 0-3"
            )

        for bits in bitmasks:
            if not 0 <= bits <= 0xFFFF:
                raise ValueError(
                    "Bitmask value must be an \
                integer in the range: 0-65535"
                )

            display.set_digit_raw(dig, bits)

            if auto_write:
                display.show()
                sleep(delay)


def chase_forward_and_reverse(delay=DEFAULT_CHAR_DELAY_SEC, cycles=DEFAULT_CYCLES):
    cy = 0

    while cy < cycles:
        animate([0, 1, 2, 3], [A, 0], delay)
        animate([3], [B, C, D, 0], delay)
        animate([2, 1, 0], [D, 0], delay)
        animate([0], [E, F, H, G2, 0], delay)
        animate([1, 2], [G1, G2, 0], delay)
        animate([3], [G1, J, A, 0], delay)
        animate([2, 1], [A, 0], delay)
        animate([0], [A, F, E, D, 0], delay)
        animate([1, 2], [D, 0], delay)
        animate([3], [D, C, B, J, G1, 0], delay)
        animate([2, 1], [G2, G1, 0], delay)
        animate([0], [H, 0], delay)

        cy += 1


def prelude_to_spinners(delay=DEFAULT_CHAR_DELAY_SEC, cycles=DEFAULT_CYCLES):
    cy = 0
    auto_write = False

    while cy < cycles:
        animate([1, 2], [A], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0, 3], [A], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [A + F], 0, auto_write)
        animate([3], [A + B], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [A + E + F], 0, auto_write)
        animate([3], [A + B + C], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [A + D + E + F], 0, auto_write)
        animate([3], [A + B + C + D], 0, auto_write)
        display.show()
        sleep(delay)

        animate([1], [A + D], 0, auto_write)
        animate([2], [A + D], 0, auto_write)
        display.show()
        sleep(delay)

        animate([1], [A + D + M], 0, auto_write)
        animate([2], [A + D + K], 0, auto_write)
        display.show()
        sleep(delay)

        animate([1], [A + D + M + H], 0, auto_write)
        animate([2], [A + D + K + J], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [A + E + F + J + D], 0, auto_write)
        animate([3], [A + B + C + H + D], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [A + E + F + J + K + D], 0, auto_write)
        animate([3], [A + B + C + H + M + D], 0, auto_write)
        display.show()
        sleep(delay)

        display.fill(0)
        display.show()
        sleep(delay)

        cy += 1


def spinners(delay=DEFAULT_CHAR_DELAY_SEC, cycles=DEFAULT_CYCLES):
    cy = 0
    auto_write = False

    while cy < cycles:
        animate([0], [H + M], 0, auto_write)
        animate([1], [J + K], 0, auto_write)
        animate([2], [H + M], 0, auto_write)
        animate([3], [J + K], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [G1 + G2], 0, auto_write)
        animate([1], [G1 + G2], 0, auto_write)
        animate([2], [G1 + G2], 0, auto_write)
        animate([3], [G1 + G2], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [J + K], 0, auto_write)
        animate([1], [H + M], 0, auto_write)
        animate([2], [J + K], 0, auto_write)
        animate([3], [H + M], 0, auto_write)
        display.show()
        sleep(delay)

        cy += 1

    display.fill(0)


def enclosed_spinners(delay=DEFAULT_CHAR_DELAY_SEC, cycles=DEFAULT_CYCLES):
    cy = 0
    auto_write = False

    while cy < cycles:
        animate([0], [A + D + E + F + H + M], 0, auto_write)
        animate([1], [A + D + J + K], 0, auto_write)
        animate([2], [A + D + H + M], 0, auto_write)
        animate([3], [A + B + C + D + J + K], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [A + D + E + F + G1 + G2], 0, auto_write)
        animate([1], [A + D + G1 + G2], 0, auto_write)
        animate([2], [A + D + G1 + G2], 0, auto_write)
        animate([3], [A + B + C + D + G1 + G2], 0, auto_write)
        display.show()
        sleep(delay)

        animate([0], [A + D + E + F + J + K], 0, auto_write)
        animate([1], [A + D + H + M], 0, auto_write)
        animate([2], [A + D + J + K], 0, auto_write)
        animate([3], [A + B + C + D + H + M], 0, auto_write)
        display.show()
        sleep(delay)

        cy += 1

    display.fill(0)


def count_down():
    auto_write = False
    numbers = [
        [A + B + C + D + G1 + G2 + N],
        [A + B + D + E + G1 + G2 + N],
        [B + C + N],
    ]
    index = 0

    display.fill(0)

    while index < len(numbers):
        animate([index], numbers[index], 0, auto_write)
        display.show()
        sleep(1)
        display.fill(0)
        sleep(0.5)

        index += 1

    sleep(1)
    display.fill(0)


try:
    text = "Init"

    display.fill(1)
    display.show()
    sleep(1)
    display.fill(0)
    display.show()

    display.print(text)
    display.show()
    sleep(2)
    display.fill(0)
    display.show()
    sleep(1)

    count_down()
    sleep(0.2)

    text = "Go!!"

    display.print(text)
    display.show()
    sleep(1.5)
    display.fill(0)
    display.show()
    sleep(0.5)
    print()

    while True:
        #   Arrow
        print("Arrow")
        animate([0, 1, 2], [G1 + G2], 0.1)
        animate([3], [G1 + H + K], 0.1)
        sleep(1.0)
        display.fill(0)
        sleep(1.0)

        #   Flying
        print("Flying")
        cyc = 0

        while cyc < DEFAULT_CYCLES:
            animate([0], [H + J, G1 + G2, K + M, G1 + G2], DEFAULT_CHAR_DELAY_SEC)

            cyc += 1

        animate([0], [0])
        sleep(1.0)
        display.fill(0)
        sleep(1.0)

        #   Chase forward and reverse.
        print("Chase forward and reverse")
        chase_forward_and_reverse(0.01, 5)
        sleep(1.0)
        display.fill(0)
        sleep(1.0)

        #   Testing writing to more than one segment simultaneously
        print("Prelude to Spinners")
        prelude_to_spinners(0.1, 5)
        sleep(1.0)
        display.fill(0)
        display.show()
        sleep(1.0)

        print("Spinners")
        spinners(0.1, 20)
        sleep(1.0)
        display.fill(0)
        display.show()
        sleep(1.0)

        print("Enclosed Spinners")
        enclosed_spinners(0.1, 20)
        sleep(1.0)
        display.fill(0)
        display.show()
        sleep(1.0)

        print()
except KeyboardInterrupt:
    display.fill(0)
    display.show()
