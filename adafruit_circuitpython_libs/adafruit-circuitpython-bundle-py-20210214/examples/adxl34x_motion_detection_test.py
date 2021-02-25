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

accelerometer.enable_motion_detection()
# alternatively you can specify the threshold when you enable motion detection for more control:
# accelerometer.enable_motion_detection(threshold=10)

while True:
    print("%f %f %f" % accelerometer.acceleration)

    print("Motion detected: %s" % accelerometer.events["motion"])
    time.sleep(0.5)
