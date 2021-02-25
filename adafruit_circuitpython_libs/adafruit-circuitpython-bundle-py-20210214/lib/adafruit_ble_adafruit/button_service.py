# SPDX-FileCopyrightText: 2020 Dan Halbert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_adafruit.button_service`
================================================================================

BLE access to buttons and switches.

* Author(s): Dan Halbert
"""
__version__ = "1.2.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Adafruit.git"

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint32Characteristic
from adafruit_ble_adafruit.adafruit_service import AdafruitService


class ButtonService(AdafruitService):
    """Status of buttons and switches on the board."""

    uuid = AdafruitService.adafruit_service_uuid(0x600)
    pressed = Uint32Characteristic(
        uuid=AdafruitService.adafruit_service_uuid(0x601),
        properties=(Characteristic.READ | Characteristic.NOTIFY),
        read_perm=Attribute.OPEN,
        write_perm=Attribute.NO_ACCESS,
    )
    """
    bit 0: slide switch: 1 for left; 0 for right
    bit 1: 1 if button A is pressed
    bit 2: 1 if button B is pressed
    other bits are available for future buttons and switches
    """
    measurement_period = AdafruitService.measurement_period_charac(0)
    """Initially 0: send notification only on changes. -1 means stop reading."""

    def set_pressed(self, switch, button_a, button_b):
        """Update the pressed value all at once."""
        pressed = 0
        if switch:
            pressed |= 0x1
        if button_a:
            pressed |= 0x2
        if button_b:
            pressed |= 0x4
        if pressed != self.pressed:
            self.pressed = pressed

    @property
    def switch(self):
        """``True`` when the slide switch is set to the left; ``False`` when to the right."""
        return bool(self.pressed & 0x1)

    @property
    def button_a(self):
        """``True`` when Button A is pressed."""
        return bool(self.pressed & 0x2)

    @property
    def button_b(self):
        """``True`` when Button B is pressed."""
        return bool(self.pressed & 0x4)
