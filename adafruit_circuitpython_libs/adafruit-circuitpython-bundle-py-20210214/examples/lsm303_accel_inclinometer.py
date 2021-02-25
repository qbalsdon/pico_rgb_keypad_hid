# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

""" Display inclination data five times per second """

import time
from math import atan2, degrees
import board
import busio
import adafruit_lsm303_accel


i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_lsm303_accel.LSM303_Accel(i2c)


def vector_2_degrees(x, y):
    angle = degrees(atan2(y, x))
    if angle < 0:
        angle += 360
    return angle


def get_inclination(_sensor):
    x, y, z = _sensor.acceleration
    return vector_2_degrees(x, z), vector_2_degrees(y, z)


while True:
    angle_xz, angle_yz = get_inclination(sensor)
    print("XZ angle = {:6.2f}deg   YZ angle = {:6.2f}deg".format(angle_xz, angle_yz))
    time.sleep(0.2)
