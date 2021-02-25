# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_icm20x

i2c = busio.I2C(board.SCL, board.SDA)
icm = adafruit_icm20x.ICM20649(i2c)

while True:
    print("Acceleration: X:%.2f, Y: %.2f, Z: %.2f m/s^2" % (icm.acceleration))
    print("Gyro X:%.2f, Y: %.2f, Z: %.2f rads/s" % (icm.gyro))
    print("")
    time.sleep(0.5)
