# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Example for getting touch data from an FT6206 or FT6236 capacitive
touch driver, over I2C.  This version uses an interrupt to prevent
read errors from the FocalTouch chip.
"""

import time
import busio
import board
from digitalio import DigitalInOut, Direction
import adafruit_focaltouch


if hasattr(
    board, "SCL"
):  # if SCL and SDA pins are defined by the board definition, use them.
    SCL_pin = board.SCL
    SDA_pin = board.SDA
else:
    SCL_pin = board.IO42  # set to a pin that you want to use for SCL
    SDA_pin = board.IO41  # set to a pin that you want to use for SDA

IRQ_pin = board.IO39  # select a pin to connect to the display's interrupt pin ("IRQ")

i2c = busio.I2C(SCL_pin, SDA_pin)

# Setup the interrupt (IRQ) pin for input
irq = DigitalInOut(board.IO39)
irq.direction = Direction.INPUT

# Create library object (named "ft") using a Bus I2C port and using an interrupt pin (IRQ)
ft = adafruit_focaltouch.Adafruit_FocalTouch(i2c, debug=False, irq_pin=irq)


print("\n\nReady for touches...")

while True:
    # if the screen is being touched print the touches
    if ft.touched:
        print(ft.touches)
    else:
        print("no touch")

    time.sleep(0.05)
