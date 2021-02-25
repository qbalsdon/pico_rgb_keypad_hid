# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
import adafruit_mpu6050

i2c = busio.I2C(board.SCL, board.SDA)
mpu = adafruit_mpu6050.MPU6050(i2c)
mpu.accelerometer_range = adafruit_mpu6050.Range.RANGE_2_G
mpu.gyro_range = adafruit_mpu6050.GyroRange.RANGE_250_DPS
while True:
    # this prints out all the values like a tuple which Mu's plotter prefer
    print("(%.2f, %.2f, %.2f " % (mpu.acceleration), end=", ")
    print("%.2f, %.2f, %.2f)" % (mpu.gyro))
    time.sleep(0.010)
