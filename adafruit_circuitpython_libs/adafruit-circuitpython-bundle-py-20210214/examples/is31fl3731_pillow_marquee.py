# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Example to scroll some text as a marquee

This example is for use on (Linux) computers that are using CPython with
Adafruit Blinka to support CircuitPython libraries. CircuitPython does
not support PIL/pillow (python imaging library)!

Author(s): Melissa LeBlanc-Williams for Adafruit Industries
"""

import board
from PIL import Image, ImageDraw, ImageFont
import adafruit_is31fl3731

SCROLLING_TEXT = "You can display a personal message here..."
BRIGHTNESS = 64  # Brightness can be between 0-255

i2c = board.I2C()

# uncomment line if you are using Adafruit 16x9 Charlieplexed PWM LED Matrix
# display = adafruit_is31fl3731.Matrix(i2c)
# uncomment line if you are using Adafruit 16x9 Charlieplexed PWM LED Matrix
display = adafruit_is31fl3731.CharlieBonnet(i2c)

# Load a font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)

# Create an image that contains the text
text_width, text_height = font.getsize(SCROLLING_TEXT)
text_image = Image.new("L", (text_width, text_height))
text_draw = ImageDraw.Draw(text_image)
text_draw.text((0, 0), SCROLLING_TEXT, font=font, fill=BRIGHTNESS)

# Create an image for the display
image = Image.new("L", (display.width, display.height))
draw = ImageDraw.Draw(image)

# Load the text in each frame
while True:
    for x in range(text_width + display.width):
        draw.rectangle((0, 0, display.width, display.height), outline=0, fill=0)
        image.paste(
            text_image, (display.width - x, display.height // 2 - text_height // 2 - 1)
        )
        display.image(image)
