# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_lis331

i2c = busio.I2C(board.SCL, board.SDA)
lis = adafruit_lis331.LIS331HH(i2c)

while True:
    print("Acceleration : X: %.2f, Y:%.2f, Z:%.2f ms^2" % lis.acceleration)
    time.sleep(0.1)
