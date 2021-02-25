# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
import busio
from adafruit_apds9960.apds9960 import APDS9960
from adafruit_apds9960 import colorutility

i2c = busio.I2C(board.SCL, board.SDA)
apds = APDS9960(i2c)
apds.enable_color = True


while True:
    # create some variables to store the color data in

    # wait for color data to be ready
    while not apds.color_data_ready:
        time.sleep(0.005)

    # get the data and print the different channels
    r, g, b, c = apds.color_data
    print("red: ", r)
    print("green: ", g)
    print("blue: ", b)
    print("clear: ", c)

    print("color temp {}".format(colorutility.calculate_color_temperature(r, g, b)))
    print("light lux {}".format(colorutility.calculate_lux(r, g, b)))
    time.sleep(0.5)
