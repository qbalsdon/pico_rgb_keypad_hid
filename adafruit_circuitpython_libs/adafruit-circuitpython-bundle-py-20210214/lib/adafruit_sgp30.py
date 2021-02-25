# SPDX-FileCopyrightText: 2017 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_sgp30`
====================================================

I2C driver for SGP30 Sensirion VoC sensor

* Author(s): ladyada

Implementation Notes
--------------------

**Hardware:**

* Adafruit `SGP30 Air Quality Sensor Breakout - VOC and eCO2
  <https://www.adafruit.com/product/3709>`_ (Product ID: 3709)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
import time
from adafruit_bus_device.i2c_device import I2CDevice
from micropython import const

__version__ = "2.3.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SGP30.git"


_SGP30_DEFAULT_I2C_ADDR = const(0x58)
_SGP30_FEATURESETS = (0x0020, 0x0022)

_SGP30_CRC8_POLYNOMIAL = const(0x31)
_SGP30_CRC8_INIT = const(0xFF)
_SGP30_WORD_LEN = const(2)


class Adafruit_SGP30:
    """
    A driver for the SGP30 gas sensor.
    """

    def __init__(self, i2c, address=_SGP30_DEFAULT_I2C_ADDR):
        """Initialize the sensor, get the serial # and verify that we found a proper SGP30"""
        self._device = I2CDevice(i2c, address)

        # get unique serial, its 48 bits so we store in an array
        self.serial = self._i2c_read_words_from_cmd([0x36, 0x82], 0.01, 3)
        # get featureset
        featureset = self._i2c_read_words_from_cmd([0x20, 0x2F], 0.01, 1)
        if featureset[0] not in _SGP30_FEATURESETS:
            raise RuntimeError("SGP30 Not detected")
        self.iaq_init()

    @property
    # pylint: disable=invalid-name
    def TVOC(self):
        """Total Volatile Organic Compound in parts per billion."""
        return self.iaq_measure()[1]

    @property
    # pylint: disable=invalid-name
    def baseline_TVOC(self):
        """Total Volatile Organic Compound baseline value"""
        return self.get_iaq_baseline()[1]

    @property
    # pylint: disable=invalid-name
    def eCO2(self):
        """Carbon Dioxide Equivalent in parts per million"""
        return self.iaq_measure()[0]

    @property
    # pylint: disable=invalid-name
    def baseline_eCO2(self):
        """Carbon Dioxide Equivalent baseline value"""
        return self.get_iaq_baseline()[0]

    @property
    # pylint: disable=invalid-name
    def Ethanol(self):
        """Ethanol Raw Signal in ticks"""
        return self.raw_measure()[1]

    @property
    # pylint: disable=invalid-name
    def H2(self):
        """H2 Raw Signal in ticks"""
        return self.raw_measure()[0]

    def iaq_init(self):
        """Initialize the IAQ algorithm"""
        # name, command, signals, delay
        self._run_profile(["iaq_init", [0x20, 0x03], 0, 0.01])

    def iaq_measure(self):
        """Measure the eCO2 and TVOC"""
        # name, command, signals, delay
        return self._run_profile(["iaq_measure", [0x20, 0x08], 2, 0.05])

    def raw_measure(self):
        """Measure H2 and Ethanol (Raw Signals)"""
        # name, command, signals, delay
        return self._run_profile(["raw_measure", [0x20, 0x50], 2, 0.025])

    def get_iaq_baseline(self):
        """Retreive the IAQ algorithm baseline for eCO2 and TVOC"""
        # name, command, signals, delay
        return self._run_profile(["iaq_get_baseline", [0x20, 0x15], 2, 0.01])

    def set_iaq_baseline(self, eCO2, TVOC):  # pylint: disable=invalid-name
        """Set the previously recorded IAQ algorithm baseline for eCO2 and TVOC"""
        if eCO2 == 0 and TVOC == 0:
            raise RuntimeError("Invalid baseline")
        buffer = []
        for value in [TVOC, eCO2]:
            arr = [value >> 8, value & 0xFF]
            arr.append(self._generate_crc(arr))
            buffer += arr
        self._run_profile(["iaq_set_baseline", [0x20, 0x1E] + buffer, 0, 0.01])

    def set_iaq_humidity(self, gramsPM3):  # pylint: disable=invalid-name
        """Set the humidity in g/m3 for eCO2 and TVOC compensation algorithm"""
        tmp = int(gramsPM3 * 256)
        buffer = []
        for value in [tmp]:
            arr = [value >> 8, value & 0xFF]
            arr.append(self._generate_crc(arr))
            buffer += arr
        self._run_profile(["iaq_set_humidity", [0x20, 0x61] + buffer, 0, 0.01])

    # Low level command functions

    def _run_profile(self, profile):
        """Run an SGP 'profile' which is a named command set"""
        # pylint: disable=unused-variable
        name, command, signals, delay = profile
        # pylint: enable=unused-variable

        # print("\trunning profile: %s, command %s, %d, delay %0.02f" %
        #   (name, ["0x%02x" % i for i in command], signals, delay))
        return self._i2c_read_words_from_cmd(command, delay, signals)

    def _i2c_read_words_from_cmd(self, command, delay, reply_size):
        """Run an SGP command query, get a reply and CRC results if necessary"""
        with self._device:
            self._device.write(bytes(command))
            time.sleep(delay)
            if not reply_size:
                return None
            crc_result = bytearray(reply_size * (_SGP30_WORD_LEN + 1))
            self._device.readinto(crc_result)
            # print("\tRaw Read: ", crc_result)
            result = []
            for i in range(reply_size):
                word = [crc_result[3 * i], crc_result[3 * i + 1]]
                crc = crc_result[3 * i + 2]
                if self._generate_crc(word) != crc:
                    raise RuntimeError("CRC Error")
                result.append(word[0] << 8 | word[1])
            # print("\tOK Data: ", [hex(i) for i in result])
            return result

    # pylint: disable=no-self-use
    def _generate_crc(self, data):
        """8-bit CRC algorithm for checking data"""
        crc = _SGP30_CRC8_INIT
        # calculates 8-Bit checksum with given polynomial
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ _SGP30_CRC8_POLYNOMIAL
                else:
                    crc <<= 1
        return crc & 0xFF
