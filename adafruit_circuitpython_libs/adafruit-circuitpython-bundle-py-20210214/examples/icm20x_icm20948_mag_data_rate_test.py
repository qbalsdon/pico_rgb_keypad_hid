# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# pylint: disable=no-member
import time
import board
import busio
from adafruit_icm20x import MagDataRate, ICM20948

cycles = 200
i2c = busio.I2C(board.SCL, board.SDA)
icm = ICM20948(i2c)

# Cycle between two data rates
# Best viewed in the Mu serial plotter where you can see how
# the data rate affects the resolution of the data
while True:
    icm.magnetometer_data_rate = MagDataRate.RATE_100HZ
    for i in range(cycles):
        print(icm.magnetic)
    time.sleep(0.3)
    icm.magnetometer_data_rate = MagDataRate.RATE_10HZ
    for i in range(cycles):
        print(icm.magnetic)
    time.sleep(0.3)
