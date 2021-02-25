# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

# VEML6070 Driver Example Code

import time
import busio
import board
import adafruit_veml6070

with busio.I2C(board.SCL, board.SDA) as i2c:
    uv = adafruit_veml6070.VEML6070(i2c)
    # Alternative constructors with parameters
    # uv = adafruit_veml6070.VEML6070(i2c, 'VEML6070_1_T')
    # uv = adafruit_veml6070.VEML6070(i2c, 'VEML6070_HALF_T', True)

    # take 10 readings
    for j in range(10):
        uv_raw = uv.uv_raw
        risk_level = uv.get_index(uv_raw)
        print("Reading: {0} | Risk Level: {1}".format(uv_raw, risk_level))
        time.sleep(1)
