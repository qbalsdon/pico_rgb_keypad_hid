# SPDX-FileCopyrightText: 2017 Dean Miller for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`CCS811` - Adafruit CCS811 Air Quality Sensor Breakout - VOC and eCO2
======================================================================
This library supports the use of the CCS811 air quality sensor in CircuitPython.

Author(s): Dean Miller for Adafruit Industries

**Notes:**

#. `Datasheet
<https://cdn-learn.adafruit.com/assets/assets/000/044/636/original/CCS811_DS000459_2-00-1098798.pdf?1501602769>`_
"""
import time
import math
import struct

from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register import i2c_bit
from adafruit_register import i2c_bits

__version__ = "1.3.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_CCS811.git"


_ALG_RESULT_DATA = const(0x02)
_RAW_DATA = const(0x03)
_ENV_DATA = const(0x05)
_NTC = const(0x06)
_THRESHOLDS = const(0x10)

_BASELINE = const(0x11)

# _HW_ID = 0x20
# _HW_VERSION = 0x21
# _FW_BOOT_VERSION = 0x23
# _FW_APP_VERSION = 0x24
# _ERROR_ID = 0xE0

_SW_RESET = const(0xFF)

# _BOOTLOADER_APP_ERASE = 0xF1
# _BOOTLOADER_APP_DATA = 0xF2
# _BOOTLOADER_APP_VERIFY = 0xF3
# _BOOTLOADER_APP_START = 0xF4

DRIVE_MODE_IDLE = const(0x00)
DRIVE_MODE_1SEC = const(0x01)
DRIVE_MODE_10SEC = const(0x02)
DRIVE_MODE_60SEC = const(0x03)
DRIVE_MODE_250MS = const(0x04)

_HW_ID_CODE = const(0x81)
_REF_RESISTOR = const(100000)


class CCS811:
    """CCS811 gas sensor driver.

    :param ~busio.I2C i2c: The I2C bus.
    :param int addr: The I2C address of the CCS811.
    """

    # set up the registers
    error = i2c_bit.ROBit(0x00, 0)
    """True when an error has occured."""
    data_ready = i2c_bit.ROBit(0x00, 3)
    """True when new data has been read."""
    app_valid = i2c_bit.ROBit(0x00, 4)
    fw_mode = i2c_bit.ROBit(0x00, 7)

    hw_id = i2c_bits.ROBits(8, 0x20, 0)

    int_thresh = i2c_bit.RWBit(0x01, 2)
    interrupt_enabled = i2c_bit.RWBit(0x01, 3)
    drive_mode = i2c_bits.RWBits(3, 0x01, 4)

    temp_offset = 0.0
    """Temperature offset."""

    def __init__(self, i2c_bus, address=0x5A):
        self.i2c_device = I2CDevice(i2c_bus, address)

        # check that the HW id is correct
        if self.hw_id != _HW_ID_CODE:
            raise RuntimeError(
                "Device ID returned is not correct! Please check your wiring."
            )
        # try to start the app
        buf = bytearray(1)
        buf[0] = 0xF4
        with self.i2c_device as i2c:
            i2c.write(buf, end=1)
        time.sleep(0.1)

        # make sure there are no errors and we have entered application mode
        if self.error:
            raise RuntimeError(
                "Device returned a error! Try removing and reapplying power to "
                "the device and running the code again."
            )
        if not self.fw_mode:
            raise RuntimeError(
                "Device did not enter application mode! If you got here, there may "
                "be a problem with the firmware on your sensor."
            )

        self.interrupt_enabled = False

        # default to read every second
        self.drive_mode = DRIVE_MODE_1SEC

        self._eco2 = None  # pylint: disable=invalid-name
        self._tvoc = None  # pylint: disable=invalid-name

    @property
    def error_code(self):
        """Error code"""
        buf = bytearray(2)
        buf[0] = 0xE0
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        return buf[1]

    def _update_data(self):
        if self.data_ready:
            buf = bytearray(9)
            buf[0] = _ALG_RESULT_DATA
            with self.i2c_device as i2c:
                i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)

            self._eco2 = (buf[1] << 8) | (buf[2])
            self._tvoc = (buf[3] << 8) | (buf[4])

            if self.error:
                raise RuntimeError("Error:" + str(self.error_code))

    @property
    def baseline(self):
        """
        The propery reads and returns the current baseline value.
        The returned value is packed into an integer.
        Later the same integer can be used in order
        to set a new baseline.
        """
        buf = bytearray(3)
        buf[0] = _BASELINE
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)
        return struct.unpack("<H", buf[1:])[0]

    @baseline.setter
    def baseline(self, baseline_int):
        """
        The property lets you set a new baseline. As a value accepts
        integer which represents packed baseline 2 bytes value.
        """
        buf = bytearray(3)
        buf[0] = _BASELINE
        struct.pack_into("<H", buf, 1, baseline_int)
        with self.i2c_device as i2c:
            i2c.write(buf)

    @property
    def tvoc(self):  # pylint: disable=invalid-name
        """Total Volatile Organic Compound in parts per billion."""
        self._update_data()
        return self._tvoc

    @property
    def eco2(self):  # pylint: disable=invalid-name
        """Equivalent Carbon Dioxide in parts per million. Clipped to 400 to 8192ppm."""
        self._update_data()
        return self._eco2

    @property
    def temperature(self):
        """
        .. deprecated:: 1.1.5
           Hardware support removed by vendor

        Temperature based on optional thermistor in Celsius."""
        buf = bytearray(5)
        buf[0] = _NTC
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buf, buf, out_end=1, in_start=1)

        vref = (buf[1] << 8) | buf[2]
        vntc = (buf[3] << 8) | buf[4]

        # From ams ccs811 app note 000925
        # https://download.ams.com/content/download/9059/13027/version/1/file/CCS811_Doc_cAppNote-Connecting-NTC-Thermistor_AN000372_v1..pdf
        rntc = float(vntc) * _REF_RESISTOR / float(vref)

        ntc_temp = math.log(rntc / 10000.0)
        ntc_temp /= 3380.0
        ntc_temp += 1.0 / (25 + 273.15)
        ntc_temp = 1.0 / ntc_temp
        ntc_temp -= 273.15
        return ntc_temp - self.temp_offset

    def set_environmental_data(self, humidity, temperature):
        """Set the temperature and humidity used when computing eCO2 and TVOC values.

        :param int humidity: The current relative humidity in percent.
        :param float temperature: The current temperature in Celsius."""
        # Humidity is stored as an unsigned 16 bits in 1/512%RH. The default
        # value is 50% = 0x64, 0x00. As an example 48.5% humidity would be 0x61,
        # 0x00.
        humidity = int(humidity * 512)

        # Temperature is stored as an unsigned 16 bits integer in 1/512 degrees
        # there is an offset: 0 maps to -25C. The default value is 25C = 0x64,
        # 0x00. As an example 23.5% temperature would be 0x61, 0x00.
        temperature = int((temperature + 25) * 512)

        buf = bytearray(5)
        buf[0] = _ENV_DATA
        struct.pack_into(">HH", buf, 1, humidity, temperature)

        with self.i2c_device as i2c:
            i2c.write(buf)

    def set_interrupt_thresholds(self, low_med, med_high, hysteresis):
        """Set the thresholds used for triggering the interrupt based on eCO2.
        The interrupt is triggered when the value crossed a boundary value by the
        minimum hysteresis value.

        :param int low_med: Boundary between low and medium ranges
        :param int med_high: Boundary between medium and high ranges
        :param int hysteresis: Minimum difference between reads"""
        buf = bytearray(
            [
                _THRESHOLDS,
                ((low_med >> 8) & 0xF),
                (low_med & 0xF),
                ((med_high >> 8) & 0xF),
                (med_high & 0xF),
                hysteresis,
            ]
        )
        with self.i2c_device as i2c:
            i2c.write(buf)

    def reset(self):
        """Initiate a software reset."""
        # reset sequence from the datasheet
        seq = bytearray([_SW_RESET, 0x11, 0xE5, 0x72, 0x8A])
        with self.i2c_device as i2c:
            i2c.write(seq)
