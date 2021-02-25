# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import busio
import board
import adafruit_is31fl3731

i2c = busio.I2C(board.SCL, board.SDA)

# array pattern in bits; top row-> bottom row, 8 bits in each row
an_arrow = bytearray((0x08, 0x0C, 0xFE, 0xFF, 0xFE, 0x0C, 0x08, 0x00, 0x00))

# initial display using Feather CharlieWing LED 15 x 7
display = adafruit_is31fl3731.CharlieWing(i2c)
# uncomment next line if you are using Adafruit 16x9 Charlieplexed PWM LED Matrix
# display = adafruit_is31fl3731.Matrix(i2c)
# uncomment line if you are using Adafruit 16x9 Charlieplexed PWM LED Matrix
# display = adafruit_is31fl3731.CharlieBonnet(i2c)
# initial display using Pimoroni Scroll Phat HD LED 17 x 7
# display = adafruit_is31fl3731.ScrollPhatHD(i2c)

# first load the frame with the arrows; moves the an_arrow to the right in each
# frame
display.sleep(True)  # turn display off while updating blink bits
display.fill(0)
for y in range(display.height):
    row = an_arrow[y]
    for x in range(8):
        bit = 1 << (7 - x) & row
        if bit:
            display.pixel(x + 4, y, 50, blink=True)

display.blink(1000)  # ranges from 270 to 2159; smaller the number to faster blink
display.sleep(False)  # turn display on
