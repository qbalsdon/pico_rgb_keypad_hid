# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Example to utilize the Python Imaging Library (Pillow) and draw bitmapped text
to 8 frames and then run autoplay on those frames.

This example is for use on (Linux) computers that are using CPython with
Adafruit Blinka to support CircuitPython libraries. CircuitPython does
not support PIL/pillow (python imaging library)!

Author(s): Melissa LeBlanc-Williams for Adafruit Industries
"""

import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_is31fl3731

BRIGHTNESS = 32  # Brightness can be between 0-255

i2c = board.I2C()

# uncomment line if you are using Adafruit 16x9 Charlieplexed PWM LED Matrix
# display = adafruit_is31fl3731.Matrix(i2c)
# uncomment line if you are using Adafruit 16x9 Charlieplexed PWM LED Matrix
display = adafruit_is31fl3731.CharlieBonnet(i2c)

display.fill(0)

# 256 Color Grayscale Mode
image = Image.new("L", (display.width, display.height))
draw = ImageDraw.Draw(image)

# Load a font in 2 different sizes.
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)

# Load the text in each frame
for x in range(8):
    draw.rectangle((0, 0, display.width, display.height), outline=0, fill=0)
    draw.text((x + 1, -2), str(x + 1), font=font, fill=BRIGHTNESS)
    display.image(image, frame=x)

display.autoplay(delay=500)
