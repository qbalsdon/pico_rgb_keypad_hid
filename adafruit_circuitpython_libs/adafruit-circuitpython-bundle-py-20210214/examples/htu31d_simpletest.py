# SPDX-FileCopyrightText: Copyright (c) 2020 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import time
import busio
import board
import adafruit_htu31d

i2c = busio.I2C(board.SCL, board.SDA)
htu = adafruit_htu31d.HTU31D(i2c)
print("Found HTU31D with serial number", hex(htu.serial_number))

htu.heater = True
print("Heater is on?", htu.heater)
htu.heater = False
print("Heater is on?", htu.heater)

while True:
    temperature, relative_humidity = htu.measurements
    print("Temperature: %0.1f C" % temperature)
    print("Humidity: %0.1f %%" % relative_humidity)
    print("")
    time.sleep(1)
