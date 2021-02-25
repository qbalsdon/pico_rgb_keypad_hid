# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import time
import board
from adafruit_lc709203f import LC709203F

print("LC709203F simple test")
print("Make sure LiPoly battery is plugged into the board!")

sensor = LC709203F(board.I2C())

print("IC version:", hex(sensor.ic_version))
while True:
    print(
        "Battery: %0.3f Volts / %0.1f %%" % (sensor.cell_voltage, sensor.cell_percent)
    )
    time.sleep(1)
