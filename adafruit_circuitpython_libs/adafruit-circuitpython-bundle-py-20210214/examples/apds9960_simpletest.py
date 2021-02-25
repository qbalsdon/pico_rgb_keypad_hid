# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from adafruit_apds9960.apds9960 import APDS9960

i2c = busio.I2C(board.SCL, board.SDA)
apds = APDS9960(i2c)

apds.enable_proximity = True

while True:
    print(apds.proximity)
    time.sleep(0.2)
