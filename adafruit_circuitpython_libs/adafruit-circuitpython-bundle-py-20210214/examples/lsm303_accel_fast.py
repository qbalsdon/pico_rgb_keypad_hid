# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

""" Read data from the accelerometer and print it out, ASAP! """

import board
import busio

import adafruit_lsm303_accel

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_lsm303_accel.LSM303_Accel(i2c)
while True:
    accel_x, accel_y, accel_z = sensor.acceleration
    print("{0:10.3f} {1:10.3f} {2:10.3f}".format(accel_x, accel_y, accel_z))
