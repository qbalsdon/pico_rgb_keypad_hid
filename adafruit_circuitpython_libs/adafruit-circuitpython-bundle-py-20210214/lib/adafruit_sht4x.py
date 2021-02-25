# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 ladyada for Adafruit
#
# SPDX-License-Identifier: MIT
"""
`adafruit_sht4x`
================================================================================

Python library for Sensirion SHT4x temperature and humidity sensors

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

Python library for Sensirion SHT4x temperature and humidity sensors

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice

"""

import time
import struct
import adafruit_bus_device.i2c_device as i2c_device
from micropython import const

__version__ = "1.0.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SHT4x.git"


_SHT4X_DEFAULT_ADDR = const(0x44)  # SHT4X I2C Address
_SHT4X_READSERIAL = const(0x89)  # Read Out of Serial Register
_SHT4X_SOFTRESET = const(0x94)  # Soft Reset


class CV:
    """struct helper"""

    @classmethod
    def add_values(cls, value_tuples):
        """Add CV values to the class"""
        cls.string = {}
        cls.delay = {}

        for value_tuple in value_tuples:
            name, value, string, delay = value_tuple
            setattr(cls, name, value)
            cls.string[value] = string
            cls.delay[value] = delay

    @classmethod
    def is_valid(cls, value):
        """Validate that a given value is a member"""
        return value in cls.string


class Mode(CV):
    """Options for ``power_mode``"""

    pass  # pylint: disable=unnecessary-pass


Mode.add_values(
    (
        ("NOHEAT_HIGHPRECISION", 0xFD, "No heater, high precision", 0.01),
        ("NOHEAT_MEDPRECISION", 0xF6, "No heater, med precision", 0.005),
        ("NOHEAT_LOWPRECISION", 0xE0, "No heater, low precision", 0.002),
        ("HIGHHEAT_1S", 0x39, "High heat, 1 second", 1.1),
        ("HIGHHEAT_100MS", 0x32, "High heat, 0.1 second", 0.11),
        ("MEDHEAT_1S", 0x2F, "Med heat, 1 second", 1.1),
        ("MEDHEAT_100MS", 0x24, "Med heat, 0.1 second", 0.11),
        ("LOWHEAT_1S", 0x1E, "Low heat, 1 second", 1.1),
        ("LOWHEAT_100MS", 0x15, "Low heat, 0.1 second", 0.11),
    )
)


class SHT4x:
    """
    A driver for the SHT4x temperature and humidity sensor.

    :param ~busio.I2C i2c_bus: The `busio.I2C` object to use. This is the only required parameter.

    """

    def __init__(self, i2c_bus):
        self.i2c_device = i2c_device.I2CDevice(i2c_bus, _SHT4X_DEFAULT_ADDR)
        self._buffer = bytearray(6)
        self.reset()
        self._mode = Mode.NOHEAT_HIGHPRECISION  # pylint: disable=no-member

    @property
    def serial_number(self):
        """The unique 32-bit serial number"""
        self._buffer[0] = _SHT4X_READSERIAL
        with self.i2c_device as i2c:
            i2c.write(self._buffer, end=1)
            time.sleep(0.01)
            i2c.readinto(self._buffer)

        ser1 = self._buffer[0:2]
        ser1_crc = self._buffer[2]
        ser2 = self._buffer[3:5]
        ser2_crc = self._buffer[5]

        # check CRC of bytes
        if ser1_crc != self._crc8(ser1) or ser2_crc != self._crc8(ser2):
            raise RuntimeError("Invalid CRC calculated")

        serial = (ser1[0] << 24) + (ser1[1] << 16) + (ser2[0] << 8) + ser2[1]
        return serial

    def reset(self):
        """Perform a soft reset of the sensor, resetting all settings to their power-on defaults"""
        self._buffer[0] = _SHT4X_SOFTRESET
        with self.i2c_device as i2c:
            i2c.write(self._buffer, end=1)
        time.sleep(0.001)

    @property
    def mode(self):
        """The current sensor reading mode (heater and precision)"""
        return self._mode

    @mode.setter
    def mode(self, new_mode):
        print(new_mode)
        if not Mode.is_valid(new_mode):
            raise AttributeError("mode must be a Mode")
        self._mode = new_mode

    @property
    def relative_humidity(self):
        """The current relative humidity in % rH"""
        return self.measurements[1]

    @property
    def temperature(self):
        """The current temperature in degrees celsius"""
        return self.measurements[0]

    @property
    def measurements(self):
        """both `temperature` and `relative_humidity`, read simultaneously"""

        temperature = None
        humidity = None
        command = self._mode

        with self.i2c_device as i2c:
            self._buffer[0] = command
            i2c.write(self._buffer, end=1)
            time.sleep(Mode.delay[self._mode])
            i2c.readinto(self._buffer)

        # separate the read data
        temp_data = self._buffer[0:2]
        temp_crc = self._buffer[2]
        humidity_data = self._buffer[3:5]
        humidity_crc = self._buffer[5]

        # check CRC of bytes
        if temp_crc != self._crc8(temp_data) or humidity_crc != self._crc8(
            humidity_data
        ):
            raise RuntimeError("Invalid CRC calculated")

        # decode data into human values:
        # convert bytes into 16-bit signed integer
        # convert the LSB value to a human value according to the datasheet
        temperature = struct.unpack_from(">H", temp_data)[0]
        temperature = -45.0 + 175.0 * temperature / 65535.0

        # repeat above steps for humidity data
        humidity = struct.unpack_from(">H", humidity_data)[0]
        humidity = -6.0 + 125.0 * humidity / 65535.0
        humidity = max(min(humidity, 100), 0)

        return (temperature, humidity)

    ## CRC-8 formula from page 14 of SHTC3 datasheet
    # https://media.digikey.com/pdf/Data%20Sheets/Sensirion%20PDFs/HT_DS_SHTC3_D1.pdf
    # Test data [0xBE, 0xEF] should yield 0x92

    @staticmethod
    def _crc8(buffer):
        crc = 0xFF
        for byte in buffer:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = crc << 1
        return crc & 0xFF  # return the bottom 8 bits
