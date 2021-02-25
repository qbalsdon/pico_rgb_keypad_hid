# SPDX-FileCopyrightText: 2019 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_mcp4728`
================================================================================

Helper library for the Microchip MCP4728 I2C 12-bit Quad DAC


* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit's MCP4728 Breakout: https://adafruit.com/product/44XX

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards: https://circuitpython.org/downloads
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

__version__ = "1.1.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCP4728.git"

from struct import pack_into
from time import sleep
import adafruit_bus_device.i2c_device as i2c_device

_MCP4728_DEFAULT_ADDRESS = 0x60

_MCP4728_CH_A_MULTI_EEPROM = 0x50


class CV:
    """struct helper"""

    @classmethod
    def add_values(cls, value_tuples):
        "creates CV entires"
        cls.string = {}
        cls.lsb = {}

        for value_tuple in value_tuples:
            name, value, string, lsb = value_tuple
            setattr(cls, name, value)
            cls.string[value] = string
            cls.lsb[value] = lsb

    @classmethod
    def is_valid(cls, value):
        "Returns true if the given value is a member of the CV"
        return value in cls.string


class Vref(CV):
    """Options for ``vref``"""

    pass  # pylint: disable=unnecessary-pass


Vref.add_values(
    (
        ("VDD", 0, "VDD", None),
        ("INTERNAL", 1, "Internal 2.048V", None),
    )
)


class MCP4728:
    """Helper library for the Microchip MCP4728 I2C 12-bit Quad DAC.

    :param ~busio.I2C i2c_bus: The I2C bus the MCP4728 is connected to.
    :param address: The I2C slave address of the sensor

    """

    def __init__(self, i2c_bus, address=_MCP4728_DEFAULT_ADDRESS):

        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)

        raw_registers = self._read_registers()

        self.channel_a = Channel(self, self._cache_page(*raw_registers[0]), 0)
        self.channel_b = Channel(self, self._cache_page(*raw_registers[1]), 1)
        self.channel_c = Channel(self, self._cache_page(*raw_registers[2]), 2)
        self.channel_d = Channel(self, self._cache_page(*raw_registers[3]), 3)

    @staticmethod
    def _get_flags(high_byte):
        vref = (high_byte & 1 << 7) > 0
        gain = (high_byte & 1 << 4) > 0
        power_state = (high_byte & 0b011 << 5) >> 5
        return (vref, gain, power_state)

    @staticmethod
    def _cache_page(value, vref, gain, power_state):
        return {"value": value, "vref": vref, "gain": gain, "power_state": power_state}

    def _read_registers(self):
        buf = bytearray(24)

        with self.i2c_device as i2c:
            i2c.readinto(buf)

        # stride is 6 because we get 6 bytes for each channel; 3 for the output regs
        # and 3 for the eeprom. Here we only care about the output regoster so we throw out
        # the eeprom values as 'n/a'
        current_values = []
        # pylint:disable=unused-variable
        for header, high_byte, low_byte, na_1, na_2, na_3 in self._chunk(buf, 6):
            # pylint:enable=unused-variable
            value = (high_byte & 0b00001111) << 8 | low_byte
            vref, gain, power_state = self._get_flags(high_byte)
            current_values.append((value, vref, gain, power_state))

        return current_values

    def save_settings(self):
        """Saves the currently selected values, Vref, and gain selections for each channel
        to the EEPROM, setting them as defaults on power up"""
        byte_list = []
        byte_list += self._generate_bytes_with_flags(self.channel_a)
        byte_list += self._generate_bytes_with_flags(self.channel_b)
        byte_list += self._generate_bytes_with_flags(self.channel_c)
        byte_list += self._generate_bytes_with_flags(self.channel_d)
        self._write_multi_eeprom(byte_list)

    # TODO: add the ability to set an offset
    def _write_multi_eeprom(self, byte_list):
        buffer_list = [_MCP4728_CH_A_MULTI_EEPROM]
        buffer_list += byte_list

        buf = bytearray(buffer_list)

        with self.i2c_device as i2c:
            i2c.write(buf)

        sleep(0.015)  # the better to write you with

    def sync_vrefs(self):
        """Syncs the driver's vref state with the DAC"""
        gain_setter_command = 0b10000000
        gain_setter_command |= self.channel_a.vref << 3
        gain_setter_command |= self.channel_b.vref << 2
        gain_setter_command |= self.channel_c.vref << 1
        gain_setter_command |= self.channel_d.vref

        buf = bytearray(1)
        pack_into(">B", buf, 0, gain_setter_command)
        with self.i2c_device as i2c:
            i2c.write(buf)

    def sync_gains(self):
        """Syncs the driver's gain state with the DAC"""

        sync_setter_command = 0b11000000
        sync_setter_command |= self.channel_a.gain << 3
        sync_setter_command |= self.channel_b.gain << 2
        sync_setter_command |= self.channel_c.gain << 1
        sync_setter_command |= self.channel_d.gain

        buf = bytearray(1)
        pack_into(">B", buf, 0, sync_setter_command)

        with self.i2c_device as i2c:
            i2c.write(buf)

    def _set_value(self, channel):

        channel_bytes = self._generate_bytes_with_flags(channel)

        write_command_byte = 0b01000000  # 0 1 0 0 0 DAC1 DAC0 UDAC
        write_command_byte |= channel.channel_index << 1

        output_buffer = bytearray([write_command_byte])
        output_buffer.extend(channel_bytes)

        with self.i2c_device as i2c:
            i2c.write(output_buffer)

    @staticmethod
    def _generate_bytes_with_flags(channel):
        buf = bytearray(2)
        pack_into(">H", buf, 0, channel.raw_value)

        buf[0] |= channel.vref << 7
        buf[0] |= channel.gain << 4

        return buf

    @staticmethod
    def _chunk(big_list, chunk_size):
        """Divides a given list into `chunk_size` sized chunks"""
        for i in range(0, len(big_list), chunk_size):
            yield big_list[i : i + chunk_size]


class Channel:
    """An instance of a single channel for a multi-channel DAC.

    **All available channels are created automatically and should not be created by the user**"""

    def __init__(self, dac_instance, cache_page, index):
        self._vref = cache_page["vref"]
        self._gain = cache_page["gain"]
        self._raw_value = cache_page["value"]
        self._dac = dac_instance
        self.channel_index = index

    @property
    def normalized_value(self):
        """The DAC value as a floating point number in the range 0.0 to 1.0."""
        return self.raw_value / (2 ** 12 - 1)

    @normalized_value.setter
    def normalized_value(self, value):
        if value < 0.0 or value > 1.0:
            raise AttributeError("`normalized_value` must be between 0.0 and 1.0")

        self.raw_value = int(value * 4095.0)

    @property
    def value(self):
        """The 16-bit scaled current value for the channel. Note that the MCP4728 is a 12-bit piece
        so quantization errors will occour"""
        return self.normalized_value * (2 ** 16 - 1)

    @value.setter
    def value(self, value):
        if value < 0 or value > (2 ** 16 - 1):
            raise AttributeError(
                "`value` must be a 16-bit integer between 0 and %s" % (2 ** 16 - 1)
            )

        # Scale from 16-bit to 12-bit value (quantization errors will occur!).
        self.raw_value = value >> 4

    @property
    def raw_value(self):
        """The native 12-bit value used by the DAC"""
        return self._raw_value

    @raw_value.setter
    def raw_value(self, value):
        if value < 0 or value > (2 ** 12 - 1):
            raise AttributeError(
                "`raw_value` must be a 12-bit integer between 0 and %s" % (2 ** 12 - 1)
            )
        self._raw_value = value
        # disabling the protected access warning here because making it public would be
        # more confusing
        self._dac._set_value(self)  # pylint:disable=protected-access

    @property
    def gain(self):
        """Sets the gain of the channel if the Vref for the channel is ``Vref.INTERNAL``.
        **The gain setting has no effect if the Vref for the channel is `Vref.VDD`**.

        With gain set to 1, the output voltage goes from 0v to 2.048V. If a channe's gain is set
        to 2, the voltage goes from 0v to 4.096V. `gain` Must be 1 or 2"""
        return self._gain

    @gain.setter
    def gain(self, value):
        if not value in (1, 2):
            raise AttributeError("`gain` must be 1 or 2")
        self._gain = value - 1
        self._dac.sync_gains()

    @property
    def vref(self):
        """Sets the DAC's voltage reference source. Must be a ``VREF``"""
        return self._vref

    @vref.setter
    def vref(self, value):
        if not Vref.is_valid(value):
            raise AttributeError("range must be a `Vref`")
        self._vref = value
        self._dac.sync_vrefs()
