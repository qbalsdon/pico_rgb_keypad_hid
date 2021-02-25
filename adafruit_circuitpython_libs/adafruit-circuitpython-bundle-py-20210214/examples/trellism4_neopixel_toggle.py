# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import adafruit_trellism4

trellis = adafruit_trellism4.TrellisM4Express()


def wheel(pos):
    if pos < 0 or pos > 255:
        return 0, 0, 0
    if pos < 85:
        return int(255 - pos * 3), int(pos * 3), 0
    if pos < 170:
        pos -= 85
        return 0, int(255 - pos * 3), int(pos * 3)
    pos -= 170
    return int(pos * 3), 0, int(255 - (pos * 3))


led_on = []

for x in range(trellis.pixels.width):
    led_on.append([])
    for y in range(trellis.pixels.height):
        led_on[x].append(False)

trellis.pixels.fill((0, 0, 0))

current_press = set()

while True:
    pressed = set(trellis.pressed_keys)

    for press in pressed - current_press:
        x, y = press

        if not led_on[x][y]:
            print("Turning on:", press)
            pixel_index = (x + (y * 8)) * 256 // 32
            trellis.pixels[x, y] = wheel(pixel_index & 255)
            led_on[x][y] = True

        else:
            print("Turning off:", press)
            trellis.pixels[x, y] = (0, 0, 0)
            led_on[x][y] = False

    current_press = pressed
