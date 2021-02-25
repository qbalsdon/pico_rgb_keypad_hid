# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import adafruit_tc74

i2c = board.I2C()

tc = adafruit_tc74.TC74(i2c)

while True:
    print(f"Temperature: {tc.temperature} C")
    time.sleep(0.5)
