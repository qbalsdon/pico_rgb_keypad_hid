# SPDX-FileCopyrightText: 2018 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

# pylint: disable=missing-docstring,invalid-name,too-many-public-methods

"""
`adafruit_seesaw.keypad`
====================================================
"""

try:
    from micropython import const
except ImportError:

    def const(x):
        return x


from adafruit_seesaw.seesaw import Seesaw

__version__ = "1.7.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_seesaw.git"

_KEYPAD_BASE = const(0x10)

_KEYPAD_STATUS = const(0x00)
_KEYPAD_EVENT = const(0x01)
_KEYPAD_INTENSET = const(0x02)
_KEYPAD_INTENCLR = const(0x03)
_KEYPAD_COUNT = const(0x04)
_KEYPAD_FIFO = const(0x10)

# pylint: disable=too-few-public-methods
class KeyEvent:
    """Holds information about a key event in its properties

    :param int num: The number of the key
    :param int edge: One of the EDGE propertes of `adafruit_seesaw.keypad.Keypad`
    """

    def __init__(self, num, edge):
        self.number = int(num)
        self.edge = int(edge)


# pylint: enable=too-few-public-methods


class Keypad(Seesaw):
    """On compatible SeeSaw devices, reads from a keypad.

    :param ~busio.I2C i2c_bus: Bus the SeeSaw is connected to
    :param int addr: I2C address of the SeeSaw device
    :param ~digitalio.DigitalInOut drdy: Pin connected to SeeSaw's 'ready' output"""

    #: Indicates that the key is currently pressed
    EDGE_HIGH = 0
    #: Indicates that the key is currently released
    EDGE_LOW = 1
    #: Indicates that the key was recently pressed
    EDGE_FALLING = 2
    #: Indicates that the key was recently released
    EDGE_RISING = 3

    def __init__(self, i2c_bus, addr=0x49, drdy=None):
        super().__init__(i2c_bus, addr, drdy)
        self._interrupt_enabled = False

    @property
    def interrupt_enabled(self):
        """Retrieve or set the interrupt enable flag"""
        return self._interrupt_enabled

    @interrupt_enabled.setter
    def interrupt_enabled(self, value):
        if value not in (True, False):
            raise ValueError("interrupt_enabled must be True or False")

        self._interrupt_enabled = value
        if value:
            self.write8(_KEYPAD_BASE, _KEYPAD_INTENSET, 1)
        else:
            self.write8(_KEYPAD_BASE, _KEYPAD_INTENCLR, 1)

    @property
    def count(self):
        """Retrieve or set the number of keys"""
        return self.read8(_KEYPAD_BASE, _KEYPAD_COUNT)

    # pylint: disable=unused-argument, no-self-use
    @count.setter
    def count(self, value):
        raise AttributeError("count is read only")

    # pylint: enable=unused-argument, no-self-use

    def set_event(self, key, edge, enable):
        """Control which kinds of events are set

        :param int key: The key number
        :param int edge: The type of event
        :param bool enable: True to enable the event, False to disable it"""

        if enable not in (True, False):
            raise ValueError("event enable must be True or False")
        if edge > 3 or edge < 0:
            raise ValueError("invalid edge")

        cmd = bytearray(2)
        cmd[0] = key
        cmd[1] = (1 << (edge + 1)) | enable

        self.write(_KEYPAD_BASE, _KEYPAD_EVENT, cmd)

    def read_keypad(self, num):
        """Read data from the keypad

        :param int num: The number of bytes to read"""
        ret = bytearray(num)
        self.read(_KEYPAD_BASE, _KEYPAD_FIFO, ret)
        return ret
