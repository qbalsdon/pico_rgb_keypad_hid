# SPDX-FileCopyrightText: 2017 Radomir Dopieralski for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
``adafruit_si7021``
===================

This is a CircuitPython driver for the SI7021 temperature and humidity sensor.

* Author(s): Radomir Dopieralski, Chris Balmer, Ian Grant

Implementation Notes
--------------------

**Hardware:**

* Adafruit `Si7021 Temperature & Humidity Sensor Breakout Board
  <https://www.adafruit.com/product/3251>`_ (Product ID: 3251)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
try:
    import struct
except ImportError:
    import ustruct as struct

from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const

__version__ = "3.3.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SI7021.git"

HUMIDITY = const(0xF5)
TEMPERATURE = const(0xF3)
_RESET = const(0xFE)
_READ_USER1 = const(0xE7)
_USER1_VAL = const(0x3A)
_ID1_CMD = bytearray([0xFA, 0x0F])
_ID2_CMD = bytearray([0xFC, 0xC9])


def _crc(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc <<= 1
                crc ^= 0x131
            else:
                crc <<= 1
    return crc


def _convert_to_integer(bytes_to_convert):
    """Use bitwise operators to convert the bytes into integers."""
    integer = None
    for chunk in bytes_to_convert:
        if not integer:
            integer = chunk
        else:
            integer = integer << 8
            integer = integer | chunk
    return integer


def _get_device_identifier(identifier_byte):
    """
    Convert the identifier byte to a device identifier (model type).
    Values are based on the information from page 24 of the datasheet.
    """
    if identifier_byte in (0x00, 0xFF):
        identifier_string = "Engineering sample"
    elif identifier_byte == 0x0D:
        identifier_string = "Si7013"
    elif identifier_byte == 0x14:
        identifier_string = "Si7020"
    elif identifier_byte == 0x15:
        identifier_string = "Si7021"
    else:
        identifier_string = "Unknown"
    return identifier_string


class SI7021:
    """
    A driver for the SI7021 temperature and humidity sensor.

    :param i2c_bus: The `busio.I2C` object to use. This is the only required parameter.
    :param int address: (optional) The I2C address of the device.
    """

    def __init__(self, i2c_bus, address=0x40):
        self.i2c_device = I2CDevice(i2c_bus, address)
        self._command(_RESET)
        # Make sure the USER1 settings are correct.
        while True:
            # While restarting, the sensor doesn't respond to reads or writes.
            try:
                data = bytearray([_READ_USER1])
                with self.i2c_device as i2c:
                    i2c.write_then_readinto(data, data)
                value = data[0]
            except OSError:
                pass
            else:
                break
        if value != _USER1_VAL:
            raise RuntimeError("bad USER1 register (%x!=%x)" % (value, _USER1_VAL))
        self._measurement = 0

    def _command(self, command):
        with self.i2c_device as i2c:
            i2c.write(struct.pack("B", command))

    def _data(self):
        data = bytearray(3)
        data[0] = 0xFF
        while True:
            # While busy, the sensor doesn't respond to reads.
            try:
                with self.i2c_device as i2c:
                    i2c.readinto(data)
            except OSError:
                pass
            else:
                if data[0] != 0xFF:  # Check if read succeeded.
                    break
        value, checksum = struct.unpack(">HB", data)
        if checksum != _crc(data[:2]):
            raise ValueError("CRC mismatch")
        return value

    @property
    def relative_humidity(self):
        """The measured relative humidity in percent."""
        self.start_measurement(HUMIDITY)
        value = self._data()
        self._measurement = 0
        return min(100.0, value * 125.0 / 65536.0 - 6.0)

    @property
    def temperature(self):
        """The measured temperature in degrees Celcius."""
        self.start_measurement(TEMPERATURE)
        value = self._data()
        self._measurement = 0
        return value * 175.72 / 65536.0 - 46.85

    def start_measurement(self, what):
        """
        Starts a measurement.

        Starts a measurement of either ``HUMIDITY`` or ``TEMPERATURE``
        depending on the ``what`` argument. Returns immediately, and the
        result of the measurement can be retrieved with the
        ``temperature`` and ``relative_humidity`` properties. This way it
        will take much less time.

        This can be useful if you want to start the measurement, but don't
        want the call to block until the measurement is ready -- for instance,
        when you are doing other things at the same time.
        """
        if what not in (HUMIDITY, TEMPERATURE):
            raise ValueError()
        if not self._measurement:
            self._command(what)
        elif self._measurement != what:
            raise RuntimeError("other measurement in progress")
        self._measurement = what

    @property
    def serial_number(self):
        """The device's unique ID (serial number)."""
        return self._get_device_info()[0]

    @property
    def device_identifier(self):
        """A device identifier (model type) string."""
        return self._get_device_info()[1]

    def _get_device_info(self):
        """
        Get the serial number and the sensor identifier (model type).
        The identifier is part of the bytes returned for the serial number.
        Source: https://github.com/chrisbalmer/micropython-si7021
        """
        # Serial 1st half
        data = _ID1_CMD
        id1 = bytearray(8)
        with self.i2c_device as i2c:
            i2c.write_then_readinto(data, id1)
        # Serial 2nd half
        data = _ID2_CMD
        id2 = bytearray(6)
        with self.i2c_device as i2c:
            i2c.write_then_readinto(data, id2)
        # Combine the two halves
        combined_id = bytearray(
            [id1[0], id1[2], id1[4], id1[6], id2[0], id2[1], id2[3], id2[4]]
        )
        # Convert serial number and extract identifier part
        serial = _convert_to_integer(combined_id)
        identifier = _get_device_identifier(id2[0])
        return serial, identifier
