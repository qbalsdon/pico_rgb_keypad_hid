# SPDX-FileCopyrightText: 2018 Brent Rubell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`ttn_as.py`
======================================================
AS920 The Things Network Frequency Plans
* Author(s): Brent Rubell
"""
TTN_FREQS = {
    0: (0xE6, 0xCC, 0xF4),  # 868.1 MHz
    1: (0xE6, 0xD9, 0xC0),  # 868.3 MHz
    2: (0xE6, 0x8C, 0xF3),  # 863.5 MHz
    3: (0xE6, 0x99, 0xC0),  # 867.1 MHz
    4: (0xE6, 0xA6, 0x8D),  # 867.3 MHz
    5: (0xE6, 0xB3, 0x5A),  # 867.5 MHz
    6: (0xE6, 0xC0, 0x27),  # 867.7 MHz
    7: (0xE6, 0x80, 0x27),
}  # 867.9 MHz
