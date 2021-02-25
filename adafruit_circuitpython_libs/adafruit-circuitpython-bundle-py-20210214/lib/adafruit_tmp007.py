# SPDX-FileCopyrightText: 2018 Jerry Needell for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_tmp007`
====================================================

CircuitPython driver for the TMP007 contactless IR thermometer

* Author(s): Jerry Needell

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

# imports

import time
from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice


__version__ = "2.1.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_TMP007.git"


# Default device I2C address.
_TMP007_I2CADDR = const(0x40)

# Register addresses.
_TMP007_CONFIG = const(0x02)
_TMP007_DEVID = const(0x1F)
_TMP007_VOBJ = const(0x0)
_TMP007_TAMB = const(0x01)
_TMP007_TOBJ = const(0x03)

# Config register values.
_TMP007_CFG_RESET = const(0x8000)
_TMP007_CFG_MODEON = const(0x7000)
CFG_1SAMPLE = const(0x0000)
CFG_2SAMPLE = const(0x0200)
CFG_4SAMPLE = const(0x0400)
CFG_8SAMPLE = const(0x0600)
CFG_16SAMPLE = const(0x0800)
_TMP007_CFG_DRDYEN = const(0x0100)
_TMP007_CFG_DRDY = const(0x0080)


class TMP007:
    """Class to represent an Adafruit TMP007 non-contact temperature measurement
    board.
    """

    # Class-level buffer for reading and writing data with the sensor.
    # This reduces memory allocations but means the code is not re-entrant or
    # thread safe!
    _BUFFER = bytearray(4)

    def __init__(self, i2c, address=_TMP007_I2CADDR, samplerate=CFG_16SAMPLE):
        """Initialize TMP007 device on the specified I2C address and bus number.
        Address defaults to 0x40 and bus number defaults to the appropriate bus
        for the hardware.
        Start taking temperature measurements.  Samplerate can be one of
        TMP007_CFG_1SAMPLE, TMP007_CFG_2SAMPLE, TMP007_CFG_4SAMPLE,
        TMP007_CFG_8SAMPLE, or TMP007_CFG_16SAMPLE.  The default is 16 samples
        for the highest resolution.  Returns True if the device is intialized,
        False otherwise.
        """
        self._device = I2CDevice(i2c, address)
        self._write_u16(_TMP007_CONFIG, _TMP007_CFG_RESET)
        time.sleep(0.5)
        if samplerate not in (
            CFG_1SAMPLE,
            CFG_2SAMPLE,
            CFG_4SAMPLE,
            CFG_8SAMPLE,
            CFG_16SAMPLE,
        ):
            raise ValueError(
                "Unexpected samplerate value! Must be one of: "
                "CFG_1SAMPLE, CFG_2SAMPLE, CFG_4SAMPLE, CFG_8SAMPLE, or CFG_16SAMPLE"
            )
        # Set configuration register to turn on chip, enable data ready output,
        # and start sampling at the specified rate.
        config = _TMP007_CFG_MODEON | _TMP007_CFG_DRDYEN | samplerate
        self._write_u16(_TMP007_CONFIG, config)
        # Check device ID match expected value.
        dev_id = self.read_register(_TMP007_DEVID)
        if dev_id != 0x78:
            raise RuntimeError("Init failed - Did not find TMP007")

    def sleep(self):
        """Put TMP007 into low power sleep mode.  No measurement data will be
        updated while in sleep mode.
        """
        control = self._read_u16(_TMP007_CONFIG)
        control &= ~(_TMP007_CFG_MODEON)
        self._write_u16(_TMP007_CONFIG, control)

    def wake(self):
        """Wake up TMP007 from low power sleep mode."""
        control = self._read_u16(_TMP007_CONFIG)
        control |= _TMP007_CFG_MODEON
        self._write_u16(_TMP007_CONFIG, control)

    @property
    def raw_voltage(self):
        """Read raw voltage from TMP007 sensor.  Meant to be used in the
        calculation of temperature values.
        """
        raw = self._read_u16(_TMP007_VOBJ)
        if raw > 32767:
            raw = (raw & 0x7FFF) - 32768
        return raw

    @property
    def raw_sensor_temperature(self):
        """Read raw die temperature from TMP007 sensor.  Meant to be used in the
        calculation of temperature values.
        """
        raw = self._read_u16(_TMP007_TAMB)
        return raw >> 2

    @property
    def die_temperature(self):
        """Read sensor die temperature and return its value in degrees celsius."""
        t_die = self.raw_sensor_temperature
        return t_die * 0.03125

    @property
    def temperature(self):
        """Read object temperature from TMP007 sensor."""
        raw = self._read_u16(_TMP007_TOBJ)
        if raw & 1:
            return -9999.0
        raw = raw >> 2
        return raw * 0.03125

    def read_register(self, register):
        """Read sensor Register."""
        return self._read_u16(register)

    def _read_u8(self, address):
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_end=1)
        return self._BUFFER[0]

    def _read_u16(self, address):
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            i2c.write_then_readinto(self._BUFFER, self._BUFFER, out_end=1, in_end=2)
        return self._BUFFER[0] << 8 | self._BUFFER[1]

    def _write_u8(self, address, val):
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = val & 0xFF
            i2c.write(self._BUFFER, end=2)

    def _write_u16(self, address, val):
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            self._BUFFER[1] = (val >> 8) & 0xFF
            self._BUFFER[2] = val & 0xFF
            i2c.write(self._BUFFER, end=3)

    @staticmethod
    def _read_bytes(device, address, count, buf):
        with device as i2c:
            buf[0] = address & 0xFF
            i2c.write_then_readinto(buf, buf, out_end=1, in_end=count)
