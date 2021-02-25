# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_vl6180x`
====================================================

CircuitPython module for the VL6180X distance sensor.  See
examples/simpletest.py for a demo of the usage.

* Author(s): Tony DiCola

Implementation Notes
--------------------

**Hardware:**

* Adafruit `VL6180X Time of Flight Distance Ranging Sensor (VL6180)
  <https://www.adafruit.com/product/3316>`_ (Product ID: 3316)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
from micropython import const

import adafruit_bus_device.i2c_device as i2c_device


__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_VL6180X.git"


# Internal constants:
_VL6180X_DEFAULT_I2C_ADDR = const(0x29)
_VL6180X_REG_IDENTIFICATION_MODEL_ID = const(0x000)
_VL6180X_REG_SYSTEM_INTERRUPT_CONFIG = const(0x014)
_VL6180X_REG_SYSTEM_INTERRUPT_CLEAR = const(0x015)
_VL6180X_REG_SYSTEM_FRESH_OUT_OF_RESET = const(0x016)
_VL6180X_REG_SYSRANGE_START = const(0x018)
_VL6180X_REG_SYSALS_START = const(0x038)
_VL6180X_REG_SYSALS_ANALOGUE_GAIN = const(0x03F)
_VL6180X_REG_SYSALS_INTEGRATION_PERIOD_HI = const(0x040)
_VL6180X_REG_SYSALS_INTEGRATION_PERIOD_LO = const(0x041)
_VL6180X_REG_RESULT_ALS_VAL = const(0x050)
_VL6180X_REG_RESULT_RANGE_VAL = const(0x062)
_VL6180X_REG_RESULT_RANGE_STATUS = const(0x04D)
_VL6180X_REG_RESULT_INTERRUPT_STATUS_GPIO = const(0x04F)

# User-facing constants:
ALS_GAIN_1 = const(0x06)
ALS_GAIN_1_25 = const(0x05)
ALS_GAIN_1_67 = const(0x04)
ALS_GAIN_2_5 = const(0x03)
ALS_GAIN_5 = const(0x02)
ALS_GAIN_10 = const(0x01)
ALS_GAIN_20 = const(0x00)
ALS_GAIN_40 = const(0x07)

ERROR_NONE = const(0)
ERROR_SYSERR_1 = const(1)
ERROR_SYSERR_5 = const(5)
ERROR_ECEFAIL = const(6)
ERROR_NOCONVERGE = const(7)
ERROR_RANGEIGNORE = const(8)
ERROR_SNR = const(11)
ERROR_RAWUFLOW = const(12)
ERROR_RAWOFLOW = const(13)
ERROR_RANGEUFLOW = const(14)
ERROR_RANGEOFLOW = const(15)


class VL6180X:
    """Create an instance of the VL6180X distance sensor.  You must pass in
    the following parameters:

    :param i2c: An instance of the I2C bus connected to the sensor.

    Optionally you can specify:

    :param address: The I2C address of the sensor.  If not specified the sensor's
                    default value will be assumed.
    """

    def __init__(self, i2c, address=_VL6180X_DEFAULT_I2C_ADDR):
        self._device = i2c_device.I2CDevice(i2c, address)
        if self._read_8(_VL6180X_REG_IDENTIFICATION_MODEL_ID) != 0xB4:
            raise RuntimeError("Could not find VL6180X, is it connected and powered?")
        self._load_settings()
        self._write_8(_VL6180X_REG_SYSTEM_FRESH_OUT_OF_RESET, 0x00)

    @property
    def range(self):
        """Read the range of an object in front of sensor and return it in mm."""
        # wait for device to be ready for range measurement
        while not self._read_8(_VL6180X_REG_RESULT_RANGE_STATUS) & 0x01:
            pass
        # Start a range measurement
        self._write_8(_VL6180X_REG_SYSRANGE_START, 0x01)
        # Poll until bit 2 is set
        while not self._read_8(_VL6180X_REG_RESULT_INTERRUPT_STATUS_GPIO) & 0x04:
            pass
        # read range in mm
        range_ = self._read_8(_VL6180X_REG_RESULT_RANGE_VAL)
        # clear interrupt
        self._write_8(_VL6180X_REG_SYSTEM_INTERRUPT_CLEAR, 0x07)
        return range_

    def read_lux(self, gain):
        """Read the lux (light value) from the sensor and return it.  Must
        specify the gain value to use for the lux reading:
        - ALS_GAIN_1 = 1x
        - ALS_GAIN_1_25 = 1.25x
        - ALS_GAIN_1_67 = 1.67x
        - ALS_GAIN_2_5 = 2.5x
        - ALS_GAIN_5 = 5x
        - ALS_GAIN_10 = 10x
        - ALS_GAIN_20 = 20x
        - ALS_GAIN_40 = 40x
        """
        reg = self._read_8(_VL6180X_REG_SYSTEM_INTERRUPT_CONFIG)
        reg &= ~0x38
        reg |= 0x4 << 3  # IRQ on ALS ready
        self._write_8(_VL6180X_REG_SYSTEM_INTERRUPT_CONFIG, reg)
        # 100 ms integration period
        self._write_8(_VL6180X_REG_SYSALS_INTEGRATION_PERIOD_HI, 0)
        self._write_8(_VL6180X_REG_SYSALS_INTEGRATION_PERIOD_LO, 100)
        # analog gain
        if gain > ALS_GAIN_40:
            gain = ALS_GAIN_40
        self._write_8(_VL6180X_REG_SYSALS_ANALOGUE_GAIN, 0x40 | gain)
        # start ALS
        self._write_8(_VL6180X_REG_SYSALS_START, 0x1)
        # Poll until "New Sample Ready threshold event" is set
        while (
            (self._read_8(_VL6180X_REG_RESULT_INTERRUPT_STATUS_GPIO) >> 3) & 0x7
        ) != 4:
            pass
        # read lux!
        lux = self._read_16(_VL6180X_REG_RESULT_ALS_VAL)
        # clear interrupt
        self._write_8(_VL6180X_REG_SYSTEM_INTERRUPT_CLEAR, 0x07)
        lux *= 0.32  # calibrated count/lux
        if gain == ALS_GAIN_1:
            pass
        elif gain == ALS_GAIN_1_25:
            lux /= 1.25
        elif gain == ALS_GAIN_1_67:
            lux /= 1.76
        elif gain == ALS_GAIN_2_5:
            lux /= 2.5
        elif gain == ALS_GAIN_5:
            lux /= 5
        elif gain == ALS_GAIN_10:
            lux /= 10
        elif gain == ALS_GAIN_20:
            lux /= 20
        elif gain == ALS_GAIN_40:
            lux /= 20
        lux *= 100
        lux /= 100  # integration time in ms
        return lux

    @property
    def range_status(self):
        """Retrieve the status/error from a previous range read.  This will
        return a constant value such as:

        - ERROR_NONE - No error
        - ERROR_SYSERR_1 - System error 1 (see datasheet)
        - ERROR_SYSERR_5 - System error 5 (see datasheet)
        - ERROR_ECEFAIL - ECE failure
        - ERROR_NOCONVERGE - No convergence
        - ERROR_RANGEIGNORE - Outside range ignored
        - ERROR_SNR - Too much noise
        - ERROR_RAWUFLOW - Raw value underflow
        - ERROR_RAWOFLOW - Raw value overflow
        - ERROR_RANGEUFLOW - Range underflow
        - ERROR_RANGEOFLOW - Range overflow
        """
        return self._read_8(_VL6180X_REG_RESULT_RANGE_STATUS) >> 4

    def _load_settings(self):
        # private settings from page 24 of app note
        self._write_8(0x0207, 0x01)
        self._write_8(0x0208, 0x01)
        self._write_8(0x0096, 0x00)
        self._write_8(0x0097, 0xFD)
        self._write_8(0x00E3, 0x00)
        self._write_8(0x00E4, 0x04)
        self._write_8(0x00E5, 0x02)
        self._write_8(0x00E6, 0x01)
        self._write_8(0x00E7, 0x03)
        self._write_8(0x00F5, 0x02)
        self._write_8(0x00D9, 0x05)
        self._write_8(0x00DB, 0xCE)
        self._write_8(0x00DC, 0x03)
        self._write_8(0x00DD, 0xF8)
        self._write_8(0x009F, 0x00)
        self._write_8(0x00A3, 0x3C)
        self._write_8(0x00B7, 0x00)
        self._write_8(0x00BB, 0x3C)
        self._write_8(0x00B2, 0x09)
        self._write_8(0x00CA, 0x09)
        self._write_8(0x0198, 0x01)
        self._write_8(0x01B0, 0x17)
        self._write_8(0x01AD, 0x00)
        self._write_8(0x00FF, 0x05)
        self._write_8(0x0100, 0x05)
        self._write_8(0x0199, 0x05)
        self._write_8(0x01A6, 0x1B)
        self._write_8(0x01AC, 0x3E)
        self._write_8(0x01A7, 0x1F)
        self._write_8(0x0030, 0x00)
        # Recommended : Public registers - See data sheet for more detail
        self._write_8(0x0011, 0x10)  # Enables polling for 'New Sample ready'
        # when measurement completes
        self._write_8(0x010A, 0x30)  # Set the averaging sample period
        # (compromise between lower noise and
        # increased execution time)
        self._write_8(0x003F, 0x46)  # Sets the light and dark gain (upper
        # nibble). Dark gain should not be
        # changed.
        self._write_8(0x0031, 0xFF)  # sets the # of range measurements after
        # which auto calibration of system is
        # performed
        self._write_8(0x0040, 0x63)  # Set ALS integration time to 100ms
        self._write_8(0x002E, 0x01)  # perform a single temperature calibration
        # of the ranging sensor

        # Optional: Public registers - See data sheet for more detail
        self._write_8(0x001B, 0x09)  # Set default ranging inter-measurement
        # period to 100ms
        self._write_8(0x003E, 0x31)  # Set default ALS inter-measurement period
        # to 500ms
        self._write_8(0x0014, 0x24)  # Configures interrupt on 'New Sample
        # Ready threshold event'

    def _write_8(self, address, data):
        # Write 1 byte of data from the specified 16-bit register address.
        with self._device:
            self._device.write(bytes([(address >> 8) & 0xFF, address & 0xFF, data]))

    def _write_16(self, address, data):
        # Write a 16-bit big endian value to the specified 16-bit register
        # address.
        with self._device as i2c:
            i2c.write(
                bytes(
                    [
                        (address >> 8) & 0xFF,
                        address & 0xFF,
                        (data >> 8) & 0xFF,
                        data & 0xFF,
                    ]
                )
            )

    def _read_8(self, address):
        # Read and return a byte from the specified 16-bit register address.
        with self._device as i2c:
            result = bytearray(1)
            i2c.write(bytes([(address >> 8) & 0xFF, address & 0xFF]))
            i2c.readinto(result)
            return result[0]

    def _read_16(self, address):
        # Read and return a 16-bit unsigned big endian value read from the
        # specified 16-bit register address.
        with self._device as i2c:
            result = bytearray(2)
            i2c.write(bytes([(address >> 8) & 0xFF, address & 0xFF]))
            i2c.readinto(result)
            return (result[0] << 8) | result[1]
