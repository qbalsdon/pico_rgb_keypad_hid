# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_msa301

i2c = busio.I2C(board.SCL, board.SDA)

msa = adafruit_msa301.MSA301(i2c)
while True:
    print("%f %f %f" % msa.acceleration)
    time.sleep(0.5)
