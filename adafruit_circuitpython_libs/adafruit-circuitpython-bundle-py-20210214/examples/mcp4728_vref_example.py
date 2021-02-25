# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

from time import sleep
import board
import busio
import adafruit_mcp4728

i2c = busio.I2C(board.SCL, board.SDA)
mcp4728 = adafruit_mcp4728.MCP4728(i2c)

FULL_VREF_RAW_VALUE = 4095

# pylint: disable=no-member
mcp4728.channel_a.raw_value = int(FULL_VREF_RAW_VALUE / 2)  # VDD/2
mcp4728.channel_a.vref = (
    adafruit_mcp4728.Vref.VDD
)  # sets the channel to scale between 0v and VDD

mcp4728.channel_b.raw_value = int(FULL_VREF_RAW_VALUE / 2)  # VDD/2
mcp4728.channel_b.vref = adafruit_mcp4728.Vref.INTERNAL
mcp4728.channel_b.gain = 1

mcp4728.channel_c.raw_value = int(FULL_VREF_RAW_VALUE / 2)  # VDD/2
mcp4728.channel_c.vref = adafruit_mcp4728.Vref.INTERNAL
mcp4728.channel_c.gain = 2

mcp4728.save_settings()

while True:
    sleep(1)
