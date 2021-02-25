# SPDX-FileCopyrightText: 2019 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_tpa2016`
================================================================================

CircuitPython driver for TPA2016 Class D Amplifier.


* Author(s): Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* `Adafruit TPA2016 - I2C Control AGC <https://www.adafruit.com/product/1712>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

from micropython import const
import adafruit_bus_device.i2c_device as i2cdevice
from adafruit_register.i2c_bits import RWBits
from adafruit_register.i2c_bit import RWBit

__version__ = "1.1.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TPA2016.git"


class TPA2016:
    """Driver for the TPA2016 class D amplifier.

    :param busio.I2C i2c_bus: The I2C bus the TPA2016 is connected to.

    """

    # Compression ratio settings
    COMPRESSION_1_1 = const(0x0)  # Ratio 1:1
    COMPRESSION_2_1 = const(0x1)  # Ratio 2:1
    COMPRESSION_4_1 = const(0x2)  # Ratio 4:1
    COMPRESSION_8_1 = const(0x3)  # Ratio 8:1

    # NoiseGate threshold settings
    NOISE_GATE_1 = const(0x0)  # 1mV
    NOISE_GATE_4 = const(0x1)  # 4mV
    NOISE_GATE_10 = const(0x2)  # 10mV
    NOISE_GATE_20 = const(0x3)  # 20mV

    _attack_control = RWBits(6, 0x02, 0)
    _release_control = RWBits(6, 0x03, 0)
    _hold_time_control = RWBits(6, 0x04, 0)
    _fixed_gain_control = RWBits(6, 0x05, 0)
    _output_limiter_level = RWBits(5, 0x05, 0)
    _max_gain = RWBits(4, 0x07, 4)

    speaker_enable_r = RWBit(0x01, 7)
    """Enables right speaker. Defaults to enabled. Set to ``False`` to disable."""
    speaker_enable_l = RWBit(0x01, 6)
    """Enables left speaker. Defaults to enabled. Set to ``False`` to disable."""
    amplifier_shutdown = RWBit(0x01, 5)
    """Amplifier shutdown. Amplifier is disabled if ``True``. Defaults to ``False``. If ``True``,
    device is in software shutdown, e.g. control, bias and oscillator are inactive."""
    reset_fault_r = RWBit(0x01, 4)
    """Over-current event on right channel indicated by returning ``True``. Reset by setting to
    ``False``."""
    reset_Fault_l = RWBit(0x01, 3)
    """Over-current event on left channel indicated by returning ``True``. Reset by setting to
    ``False``."""
    reset_thermal = RWBit(0x01, 2)
    """Thermal software shutdown indicated by returning ``True``. Reset by setting to ``False``."""

    noise_gate_enable = RWBit(0x01, 0)
    """NoiseGate function enable. Enabled by default. Can only be enabled when compression ratio
    is NOT 1:1. To disable, set to ``False``."""
    output_limiter_disable = RWBit(0x06, 7)
    """

    Output limiter disable.

    Enabled by default when compression ratio is NOT 1:1. Can only be
    disabled if compression ratio is 1:1. To disable, set to ``True``.
    """

    noise_gate_threshold = RWBits(2, 0x06, 5)
    """
    Noise Gate threshold in mV.

    Noise gate settings are 1mV, 4mV, 10mV, and 20mV. Settings
    options are NOISE_GATE_1, NOISE_GATE_4, NOISE_GATE_10, NOISE_GATE_20. Only functional when
    compression ratio is NOT 1:1. Defaults to 4mV.

    This example sets the noise gate threshold to 10mV.

    .. code-block:: python

        import adafruit_tpa2016
        import busio
        import board

        i2c = busio.I2C(board.SCL, board.SDA)
        tpa = adafruit_tpa2016.TPA2016(i2c)

        tpa.noise_gate_threshold = tpa.NOISE_GATE_10

    """

    compression_ratio = RWBits(2, 0x07, 0)
    """
    The compression ratio.

    Ratio settings are: 1:1. 2:1, 4:1, 8:1. Settings options are:
    COMPRESSION_1_1, COMPRESSION_2_1, COMPRESSION_4_1, COMPRESSION_8_1. Defaults to 4:1.

    This example sets the compression ratio to 2:1.

    .. code-block:: python

        import adafruit_tpa2016
        import busio
        import board

        i2c = busio.I2C(board.SCL, board.SDA)
        tpa = adafruit_tpa2016.TPA2016(i2c)

        tpa.compression_ratio = tpa.COMPRESSION_2_1

    """

    def __init__(self, i2c_bus):
        self.i2c_device = i2cdevice.I2CDevice(i2c_bus, 0x58)

    @property
    def attack_time(self):
        """The attack time. This is the minimum time between gain decreases. Set to ``1`` - ``63``
        where 1 = 0.1067ms and the time increases 0.1067ms with each step, for a maximum of 6.722ms.
        Defaults to 5, or 0.5335ms.

        This example sets the attack time to 1, or 0.1067ms.

        .. code-block:: python

            import adafruit_tpa2016
            import busio
            import board

            i2c = busio.I2C(board.SCL, board.SDA)
            tpa = adafruit_tpa2016.TPA2016(i2c)

            tpa.attack_time = 1

        """
        return self._attack_control

    @attack_time.setter
    def attack_time(self, value):
        if 1 <= value <= 63:
            self._attack_control = value
        else:
            raise ValueError("Attack time must be 1 to 63!")

    @property
    def release_time(self):
        """The release time. This is the minimum time between gain increases. Set to ``1`` - ``63``
        where 1 = 0.0137ms, and the time increases 0.0137ms with each step, for a maximum of
        0.8631ms. Defaults to 11, or 0.1507ms.

        This example sets release time to 1, or 0.0137ms.

        .. code-block:: python

            import adafruit_tpa2016
            import busio
            import board

            i2c = busio.I2C(board.SCL, board.SDA)
            tpa = adafruit_tpa2016.TPA2016(i2c)

            tpa.release_time = 1

        """
        return self._release_control

    @release_time.setter
    def release_time(self, value):
        if 1 <= value <= 63:
            self._release_control = value
        else:
            raise ValueError("Release time must be 1 to 63!")

    @property
    def hold_time(self):
        """The hold time. This is the minimum time between attack and release. Set to ``0`` -
        ``63`` where 0 = disabled, and the time increases 0.0137ms with each step, for a maximum of
        0.8631ms. Defaults to 0, or disabled.

        This example sets hold time to 1, or 0.0137ms.

        .. code-block:: python

            import adafruit_tpa2016
            import busio
            import board

            i2c = busio.I2C(board.SCL, board.SDA)
            tpa = adafruit_tpa2016.TPA2016(i2c)

            tpa.hold_time = 1

        """
        return self._hold_time_control

    @hold_time.setter
    def hold_time(self, value):
        if 0 <= value <= 63:
            self._hold_time_control = value
        else:
            raise ValueError("Hold time must be 0 to 63!")

    @property
    def fixed_gain(self):
        """The fixed gain of the amplifier in dB. If compression is enabled, fixed gain is
        adjustable from ``–28`` to ``30``. If compression is disabled, fixed gain is adjustable
        from ``0`` to ``30``.

        The following example sets the fixed gain to -16dB.

        .. code-block:: python

            import adafruit_tpa2016
            import busio
            import board

            i2c = busio.I2C(board.SCL, board.SDA)
            tpa = adafruit_tpa2016.TPA2016(i2c)

            tpa.fixed_gain = -16

        """
        return self._fixed_gain_control

    @fixed_gain.setter
    def fixed_gain(self, value):
        if self.compression_ratio:
            if -28 <= value <= 30:
                ratio = value & 0x3F
                self._fixed_gain_control = ratio
            else:
                raise ValueError("Gain must be -28 to 30!")
        else:
            if 0 <= value <= 30:
                self._fixed_gain_control = value
            else:
                raise ValueError("Compression is disabled, gain must be 0 to 30!")

    @property
    def output_limiter_level(self):
        """The output limiter level in dBV. Must be between ``-6.5`` and ``9``, set in increments
        of 0.5."""
        return -6.5 + 0.5 * self._output_limiter_level

    @output_limiter_level.setter
    def output_limiter_level(self, value):
        if -6.5 <= value <= 9:
            output = int((value + 6.5) / 0.5)
            self._output_limiter_level = output
        else:
            raise ValueError("Output limiter level must be -6.5 to 9!")

    @property
    def max_gain(self):
        """The max gain in dB. Must be between ``18`` and ``30``."""
        return self._max_gain + 18

    @max_gain.setter
    def max_gain(self, value):
        if 18 <= value <= 30:
            max_value = value - 18
            self._max_gain = max_value
        else:
            raise ValueError("Max gain must be 18 to 30!")
