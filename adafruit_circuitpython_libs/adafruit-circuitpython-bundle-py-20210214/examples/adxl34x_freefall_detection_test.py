# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_adxl34x

i2c = busio.I2C(board.SCL, board.SDA)

# For ADXL343
accelerometer = adafruit_adxl34x.ADXL343(i2c)
# For ADXL345
# accelerometer = adafruit_adxl34x.ADXL345(i2c)

accelerometer.enable_freefall_detection()
# alternatively you can specify attributes when you enable freefall detection for more control:
# accelerometer.enable_freefall_detection(threshold=10,time=25)

while True:
    print("%f %f %f" % accelerometer.acceleration)

    print("Dropped: %s" % accelerometer.events["freefall"])
    time.sleep(0.5)
