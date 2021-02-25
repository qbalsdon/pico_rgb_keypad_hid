# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import board
import busio
import adafruit_mcp4728

i2c = busio.I2C(board.SCL, board.SDA)
mcp4728 = adafruit_mcp4728.MCP4728(i2c)

mcp4728.channel_a.value = 65535  # Voltage = VDD
mcp4728.channel_b.value = int(65535 / 2)  # VDD/2
mcp4728.channel_c.value = int(65535 / 4)  # VDD/4
mcp4728.channel_d.value = 0  # 0V
