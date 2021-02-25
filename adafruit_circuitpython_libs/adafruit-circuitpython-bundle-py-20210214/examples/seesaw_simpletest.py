# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# Simple seesaw test using an LED attached to Pin 15.
#
# See the seesaw Learn Guide for wiring details:
# https://learn.adafruit.com/adafruit-seesaw-atsamd09-breakout?view=all#circuitpython-wiring-and-test
import time

from board import SCL, SDA
import busio
from adafruit_seesaw.seesaw import Seesaw

i2c_bus = busio.I2C(SCL, SDA)

ss = Seesaw(i2c_bus)

ss.pin_mode(15, ss.OUTPUT)

while True:
    ss.digital_write(15, True)  # turn the LED on (True is the voltage level)
    time.sleep(1)  # wait for a second
    ss.digital_write(15, False)  # turn the LED off by making the voltage LOW
    time.sleep(1)
