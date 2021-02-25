# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX as LSM6DS

# To use LSM6DS33, comment out the LSM6DSOX import line
# and uncomment the next line
# from adafruit_lsm6ds.lsm6ds33 import LSM6DS33 as LSM6DS

# To use ISM330DHCX, comment out the LSM6DSOX import line
# and uncomment the next line
# from adafruit_lsm6ds.lsm330dhcx import ISM330DHCX as LSM6DS

from adafruit_lis3mdl import LIS3MDL

accel_gyro = LSM6DS(board.I2C())
mag = LIS3MDL(board.I2C())

while True:
    acceleration = accel_gyro.acceleration
    gyro = accel_gyro.gyro
    magnetic = mag.magnetic
    print(
        "Acceleration: X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} m/s^2".format(*acceleration)
    )
    print("Gyro          X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} rad/s".format(*gyro))
    print("Magnetic      X:{0:7.2f}, Y:{1:7.2f}, Z:{2:7.2f} uT".format(*magnetic))
    print("")
    time.sleep(0.5)
