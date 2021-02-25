# SPDX-FileCopyrightText: 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bd3491fs`
================================================================================

CircuitPython library for the Rohm BD3491FS Audio Processor


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* `Adafruit BD3491FS Breakout <https://www.adafruit.com/products>`_"

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

# imports

__version__ = "1.1.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BD3491FS.git"

from micropython import const
import adafruit_bus_device.i2c_device as i2cdevice
from adafruit_register.i2c_struct import UnaryStruct

_INPUT_SELECTOR = const(0x04)
_INPUT_GAIN = const(0x06)
_VOLUME_GAIN_CH1 = const(0x21)
_VOLUME_GAIN_CH2 = const(0x22)
_BASS_GAIN = const(0x51)
_TREBLE_GAIN = const(0x57)
_SURROUND_GAIN = const(0x78)
_SYSTEM_RESET = const(0xFE)


class Input:  # pylint: disable=too-few-public-methods,invalid-name
    """Options for ``active_input``

    +-----------------+------------------+
    | ``Input``       | Input Pair       |
    +=================+==================+
    | ``Input.A``     | Inputs A1 and A2 |
    +-----------------+------------------+
    | ``Input.B``     | Inputs B1 and B2 |
    +-----------------+------------------+
    | ``Input.C``     | Inputs C1 and C2 |
    +-----------------+------------------+
    | ``Input.D``     | Inputs D1 and D2 |
    +-----------------+------------------+
    | ``Input.E``     | Inputs E1 and E2 |
    +-----------------+------------------+
    | ``Input.F``     | Inputs F1 and F2 |
    +-----------------+------------------+
    | ``Input.SHORT`` | Short inputs     |
    +-----------------+------------------+
    | ``Input.MUTE``  | Mute all         |
    +-----------------+------------------+

    """

    A = const(0x00)
    B = const(0x01)
    C = const(0x02)
    D = const(0x03)
    E = const(0x04)
    F = const(0x06)
    SHORT = const(0x05)
    MUTE = const(0x07)


class Level:  # pylint: disable=too-few-public-methods
    """Options for ``imput_gain``

    +----------------------+-------+
    | ``Level``            | Value |
    +======================+=======+
    | ``Level.LEVEL_0DB``  | 0dB   |
    +----------------------+-------+
    | ``Level.LEVEL_2DB``  | 2dB   |
    +----------------------+-------+
    | ``Level.LEVEL_4DB``  | 4dB   |
    +----------------------+-------+
    | ``Level.LEVEL_6DB``  | 6dB   |
    +----------------------+-------+
    | ``Level.LEVEL_8DB``  | 8dB   |
    +----------------------+-------+
    | ``Level.LEVEL_10DB`` | 10dB  |
    +----------------------+-------+
    | ``Level.LEVEL_12DB`` | 12dB  |
    +----------------------+-------+
    | ``Level.LEVEL_14DB`` | 14dB  |
    +----------------------+-------+
    | ``Level.LEVEL_16DB`` | 16dB  |
    +----------------------+-------+
    | ``Level.LEVEL_20DB`` | 20dB  |
    +----------------------+-------+

    """

    LEVEL_0DB = const(0x00)
    LEVEL_2DB = const(0x01)
    LEVEL_4DB = const(0x02)
    LEVEL_6DB = const(0x03)
    LEVEL_8DB = const(0x04)
    LEVEL_10DB = const(0x05)
    LEVEL_12DB = const(0x06)
    LEVEL_14DB = const(0x07)
    LEVEL_16DB = const(0x08)
    LEVEL_20DB = const(0x0A)


class BD3491FS:  # pylint: disable=too-many-instance-attributes
    """Driver for the Rohm BD3491FS audio processor

    :param ~busio.I2C i2c_bus: The I2C bus the BD3491FS is connected to.
    """

    _input_selector = UnaryStruct(_INPUT_SELECTOR, "<B")
    _input_gain = UnaryStruct(_INPUT_GAIN, "<B")
    _ch1_attenuation = UnaryStruct(_VOLUME_GAIN_CH1, "<B")
    _ch2_attenuation = UnaryStruct(_VOLUME_GAIN_CH2, "<B")
    _system_reset = UnaryStruct(_SYSTEM_RESET, "<B")

    def __init__(self, i2c_bus):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, 0x41)
        self._current_active_input = 7  # mute
        self._current_input_gain = 0  # 0dB
        self._current_ch1_attenuation = 255  # muted
        self._current_ch2_attenuation = 255  # muted
        self.reset()

    def reset(self):
        """Reset the sensor, muting the input, reducting input gain to 0dB, and the output channnel
        attenuation to maximum"""
        self._reset = 0x81

    @property
    def active_input(self):
        """The currently selected input. Must be an ``Input``

        This example sets A1 and A2 to the active input pair.
        .. code-block:: python
        bd3491fs.active_input = adafruit_bd3491fs.Input.A
        """
        return self._current_active_input

    @active_input.setter
    def active_input(self, value):
        self._input_selector = value
        self._current_active_input = value

    @property
    def input_gain(self):
        """The gain applied to all inputs equally"
        This example sets the input gain to 10dB.
        .. code-block:: python
        bd3491fs.input_gain = adafruit_bd3491fs.Level.10_DB""
        """
        return self._current_input_gain

    @input_gain.setter
    def input_gain(self, value):
        allowed_gains = [0, 1, 2, 3, 4, 6, 8, 10]
        if not value in allowed_gains:
            raise ValueError("input gain must be one of 0, 2, 4, 6, 8, 12, 16, 20 dB")
        self._input_gain = value
        self._current_input_gain = value

    @property
    def channel_1_attenuation(self):
        """The attenuation applied to channel 1 of the currently selected input pair in -dB.
        Maximum is -87dB. To mute set to 255
        This example sets the attenuation for input channel 1 to -10dB.
        .. code-block:: python
        bd3491fs.channel_1_attenuation = 10""
        """
        return self._current_ch1_attenuation

    @channel_1_attenuation.setter
    def channel_1_attenuation(self, value):
        if (value < 0) or ((value > 87) and (value != 255)):
            raise ValueError("channel 1 attenuation must be from 0-87db")
        self._ch1_attenuation = value
        self._current_ch1_attenuation = value

    @property
    def channel_2_attenuation(self):
        """The attenuation applied to channel 2 of the currently selected input pair in -dB.
        Maximum is -87dB. To mute set to 255
        This example sets the attenuation for input channel 2 to -10dB.
        .. code-block:: python
        bd3491fs.channel_2_attenuation = 10""
        """
        return self._current_ch2_attenuation

    @channel_2_attenuation.setter
    def channel_2_attenuation(self, value):
        if (value < 0) or ((value > 87) and (value != 255)):
            raise ValueError("channel 2 attenuation must be from 0-87db")
        self._ch2_attenuation = value
        self._current_ch2_attenuation = value
