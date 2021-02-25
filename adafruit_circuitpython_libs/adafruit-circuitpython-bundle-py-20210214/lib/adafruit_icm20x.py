# SPDX-FileCopyrightText: 2020 Bryan Siepert for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_icm20x`
================================================================================

Library for the ST ICM20X Motion Sensor Family

* Author(s): Bryan Siepert

Implementation Notes
--------------------

**Hardware:**

* Adafruit's ICM20649 Breakout: https://adafruit.com/product/4464
* Adafruit's ICM20948 Breakout: https://adafruit.com/product/4554

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads


* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
* Adafruit's Register library: https://github.com/adafruit/Adafruit_CircuitPython_Register
"""

__version__ = "2.0.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ICM20X.git"
# Common imports; remove if unused or pylint will complain
from time import sleep
import adafruit_bus_device.i2c_device as i2c_device

from adafruit_register.i2c_struct import UnaryStruct, ROUnaryStruct, Struct
from adafruit_register.i2c_bit import RWBit, ROBit
from adafruit_register.i2c_bits import RWBits

_ICM20649_DEFAULT_ADDRESS = 0x68  # icm20649 default i2c address
_ICM20948_DEFAULT_ADDRESS = 0x69  # icm20649 default i2c address
_ICM20649_DEVICE_ID = 0xE1  # Correct content of WHO_AM_I register
_ICM20948_DEVICE_ID = 0xEA  # Correct content of WHO_AM_I register

# Functions using these bank-specific registers are responsible for ensuring
# that the correct bank is set
# Bank 0
_ICM20X_WHO_AM_I = 0x00  # device_id register
_ICM20X_REG_BANK_SEL = 0x7F  # register bank selection register
_ICM20X_PWR_MGMT_1 = 0x06  # primary power management register
_ICM20X_ACCEL_XOUT_H = 0x2D  # first byte of accel data
_ICM20X_GYRO_XOUT_H = 0x33  # first byte of accel data
_ICM20X_I2C_MST_STATUS = 0x17  # I2C Master Status bits
_ICM20948_EXT_SLV_SENS_DATA_00 = 0x3B

_ICM20X_USER_CTRL = 0x03  # User Control Reg. Includes I2C Master
_ICM20X_LP_CONFIG = 0x05  # Low Power config
_ICM20X_REG_INT_PIN_CFG = 0xF  # Interrupt config register
_ICM20X_REG_INT_ENABLE_0 = 0x10  # Interrupt enable register 0
_ICM20X_REG_INT_ENABLE_1 = 0x11  # Interrupt enable register 1

# Bank 2
_ICM20X_GYRO_SMPLRT_DIV = 0x00
_ICM20X_GYRO_CONFIG_1 = 0x01
_ICM20X_ACCEL_SMPLRT_DIV_1 = 0x10
_ICM20X_ACCEL_SMPLRT_DIV_2 = 0x11
_ICM20X_ACCEL_CONFIG_1 = 0x14


# Bank 3

_ICM20X_I2C_MST_ODR_CONFIG = 0x0  # Sets ODR for I2C master bus
_ICM20X_I2C_MST_CTRL = 0x1  # I2C master bus config
_ICM20X_I2C_MST_DELAY_CTRL = 0x2  # I2C master bus config
_ICM20X_I2C_SLV0_ADDR = 0x3  # Sets I2C address for I2C master bus slave 0
_ICM20X_I2C_SLV0_REG = 0x4  # Sets register address for I2C master bus slave 0
_ICM20X_I2C_SLV0_CTRL = 0x5  # Controls for I2C master bus slave 0
_ICM20X_I2C_SLV0_DO = 0x6  # Sets I2C master bus slave 0 data out

_ICM20X_I2C_SLV4_ADDR = 0x13  # Sets I2C address for I2C master bus slave 4
_ICM20X_I2C_SLV4_REG = 0x14  # Sets register address for I2C master bus slave 4
_ICM20X_I2C_SLV4_CTRL = 0x15  # Controls for I2C master bus slave 4
_ICM20X_I2C_SLV4_DO = 0x16  # Sets I2C master bus slave 4 data out
_ICM20X_I2C_SLV4_DI = 0x17  # Sets I2C master bus slave 4 data in

_ICM20X_UT_PER_LSB = 0.15  # mag data LSB value (fixed)
_ICM20X_RAD_PER_DEG = 0.017453293  # Degrees/s to rad/s multiplier

G_TO_ACCEL = 9.80665


class CV:
    """struct helper"""

    @classmethod
    def add_values(cls, value_tuples):
        """Add CV values to the class"""
        cls.string = {}
        cls.lsb = {}

        for value_tuple in value_tuples:
            name, value, string, lsb = value_tuple
            setattr(cls, name, value)
            cls.string[value] = string
            cls.lsb[value] = lsb

    @classmethod
    def is_valid(cls, value):
        """Validate that a given value is a member"""
        return value in cls.string


class AccelRange(CV):
    """Options for ``accelerometer_range``"""

    pass  # pylint: disable=unnecessary-pass


class GyroRange(CV):
    """Options for ``gyro_data_range``"""

    pass  # pylint: disable=unnecessary-pass


class GyroDLPFFreq(CV):
    """Options for ``gyro_dlpf_cutoff``"""

    pass  # pylint: disable=unnecessary-pass


class AccelDLPFFreq(CV):
    """Options for ``accel_dlpf_cutoff``"""

    pass  # pylint: disable=unnecessary-pass


class ICM20X:  # pylint:disable=too-many-instance-attributes
    """Library for the ST ICM-20X Wide-Range 6-DoF Accelerometer and Gyro Family


    :param ~busio.I2C i2c_bus: The I2C bus the ICM20X is connected to.
    :param address: The I2C slave address of the sensor

    """

    # Bank 0
    _device_id = ROUnaryStruct(_ICM20X_WHO_AM_I, ">B")
    _bank_reg = UnaryStruct(_ICM20X_REG_BANK_SEL, ">B")
    _reset = RWBit(_ICM20X_PWR_MGMT_1, 7)
    _sleep_reg = RWBit(_ICM20X_PWR_MGMT_1, 6)
    _low_power_en = RWBit(_ICM20X_PWR_MGMT_1, 5)
    _clock_source = RWBits(3, _ICM20X_PWR_MGMT_1, 0)

    _raw_accel_data = Struct(_ICM20X_ACCEL_XOUT_H, ">hhh")  # ds says LE :|
    _raw_gyro_data = Struct(_ICM20X_GYRO_XOUT_H, ">hhh")

    _lp_config_reg = UnaryStruct(_ICM20X_LP_CONFIG, ">B")

    _i2c_master_cycle_en = RWBit(_ICM20X_LP_CONFIG, 6)
    _accel_cycle_en = RWBit(_ICM20X_LP_CONFIG, 5)
    _gyro_cycle_en = RWBit(_ICM20X_LP_CONFIG, 4)

    # Bank 2
    _gyro_dlpf_enable = RWBits(1, _ICM20X_GYRO_CONFIG_1, 0)
    _gyro_range = RWBits(2, _ICM20X_GYRO_CONFIG_1, 1)
    _gyro_dlpf_config = RWBits(3, _ICM20X_GYRO_CONFIG_1, 3)

    _accel_dlpf_enable = RWBits(1, _ICM20X_ACCEL_CONFIG_1, 0)
    _accel_range = RWBits(2, _ICM20X_ACCEL_CONFIG_1, 1)
    _accel_dlpf_config = RWBits(3, _ICM20X_ACCEL_CONFIG_1, 3)

    # this value is a 12-bit register spread across two bytes, big-endian first
    _accel_rate_divisor = UnaryStruct(_ICM20X_ACCEL_SMPLRT_DIV_1, ">H")
    _gyro_rate_divisor = UnaryStruct(_ICM20X_GYRO_SMPLRT_DIV, ">B")
    AccelDLPFFreq.add_values(
        (
            (
                "DISABLED",
                -1,
                "Disabled",
                None,
            ),  # magical value that we will use do disable
            ("FREQ_246_0HZ_3DB", 1, 246.0, None),
            ("FREQ_111_4HZ_3DB", 2, 111.4, None),
            ("FREQ_50_4HZ_3DB", 3, 50.4, None),
            ("FREQ_23_9HZ_3DB", 4, 23.9, None),
            ("FREQ_11_5HZ_3DB", 5, 11.5, None),
            ("FREQ_5_7HZ_3DB", 6, 5.7, None),
            ("FREQ_473HZ_3DB", 7, 473, None),
        )
    )
    GyroDLPFFreq.add_values(
        (
            (
                "DISABLED",
                -1,
                "Disabled",
                None,
            ),  # magical value that we will use do disable
            ("FREQ_196_6HZ_3DB", 0, 196.6, None),
            ("FREQ_151_8HZ_3DB", 1, 151.8, None),
            ("FREQ_119_5HZ_3DB", 2, 119.5, None),
            ("FREQ_51_2HZ_3DB", 3, 51.2, None),
            ("FREQ_23_9HZ_3DB", 4, 23.9, None),
            ("FREQ_11_6HZ_3DB", 5, 11.6, None),
            ("FREQ_5_7HZ_3DB", 6, 5.7, None),
            ("FREQ_361_4HZ_3DB", 7, 361.4, None),
        )
    )

    @property
    def _bank(self):
        return self._bank_reg >> 4

    @_bank.setter
    def _bank(self, value):
        self._bank_reg = value << 4

    def __init__(self, i2c_bus, address):

        self.i2c_device = i2c_device.I2CDevice(i2c_bus, address)
        self._bank = 0
        if not self._device_id in [_ICM20649_DEVICE_ID, _ICM20948_DEVICE_ID]:
            raise RuntimeError("Failed to find an ICM20X sensor - check your wiring!")
        self.reset()
        self.initialize()

    def initialize(self):
        """Configure the sensors with the default settings. For use after calling `reset()`"""

        self._sleep = False
        self.accelerometer_range = AccelRange.RANGE_8G  # pylint: disable=no-member
        self.gyro_range = GyroRange.RANGE_500_DPS  # pylint: disable=no-member

        self.accelerometer_data_rate_divisor = 20  # ~53.57Hz
        self.gyro_data_rate_divisor = 10  # ~100Hz

    def reset(self):
        """Resets the internal registers and restores the default settings"""
        self._bank = 0

        sleep(0.005)
        self._reset = True
        sleep(0.005)
        while self._reset:
            sleep(0.005)

    @property
    def _sleep(self):
        self._bank = 0
        sleep(0.005)
        self._sleep_reg = False
        sleep(0.005)

    @_sleep.setter
    def _sleep(self, sleep_enabled):
        self._bank = 0
        sleep(0.005)
        self._sleep_reg = sleep_enabled
        sleep(0.005)

    @property
    def acceleration(self):
        """The x, y, z acceleration values returned in a 3-tuple and are in m / s ^ 2."""
        self._bank = 0
        raw_accel_data = self._raw_accel_data
        sleep(0.005)

        x = self._scale_xl_data(raw_accel_data[0])
        y = self._scale_xl_data(raw_accel_data[1])
        z = self._scale_xl_data(raw_accel_data[2])

        return (x, y, z)

    @property
    def gyro(self):
        """The x, y, z angular velocity values returned in a 3-tuple and are in degrees / second"""
        self._bank = 0
        raw_gyro_data = self._raw_gyro_data
        x = self._scale_gyro_data(raw_gyro_data[0])
        y = self._scale_gyro_data(raw_gyro_data[1])
        z = self._scale_gyro_data(raw_gyro_data[2])

        return (x, y, z)

    def _scale_xl_data(self, raw_measurement):
        sleep(0.005)
        return raw_measurement / AccelRange.lsb[self._cached_accel_range] * G_TO_ACCEL

    def _scale_gyro_data(self, raw_measurement):
        return (
            raw_measurement / GyroRange.lsb[self._cached_gyro_range]
        ) * _ICM20X_RAD_PER_DEG

    @property
    def accelerometer_range(self):
        """Adjusts the range of values that the sensor can measure, from +/- 4G to +/-30G
        Note that larger ranges will be less accurate. Must be an `AccelRange`"""
        return self._cached_accel_range

    @accelerometer_range.setter
    def accelerometer_range(self, value):  # pylint: disable=no-member
        if not AccelRange.is_valid(value):
            raise AttributeError("range must be an `AccelRange`")
        self._bank = 2
        sleep(0.005)
        self._accel_range = value
        sleep(0.005)
        self._cached_accel_range = value
        self._bank = 0

    @property
    def gyro_range(self):
        """Adjusts the range of values that the sensor can measure, from 500 Degrees/second to 4000
        degrees/s. Note that larger ranges will be less accurate. Must be a `GyroRange`"""
        return self._cached_gyro_range

    @gyro_range.setter
    def gyro_range(self, value):
        if not GyroRange.is_valid(value):
            raise AttributeError("range must be a `GyroRange`")

        self._bank = 2
        sleep(0.005)
        self._gyro_range = value
        sleep(0.005)
        self._cached_gyro_range = value
        self._bank = 0
        sleep(0.100)  # needed to let new range settle

    @property
    def accelerometer_data_rate_divisor(self):
        """The divisor for the rate at which accelerometer measurements are taken in Hz

        Note: The data rates are set indirectly by setting a rate divisor according to the
        following formula: ``accelerometer_data_rate = 1125/(1+divisor)``

        This function sets the raw rate divisor.
        """
        self._bank = 2
        raw_rate_divisor = self._accel_rate_divisor
        sleep(0.005)
        self._bank = 0
        # rate_hz = 1125/(1+raw_rate_divisor)
        return raw_rate_divisor

    @accelerometer_data_rate_divisor.setter
    def accelerometer_data_rate_divisor(self, value):
        # check that value <= 4095
        self._bank = 2
        sleep(0.005)
        self._accel_rate_divisor = value
        sleep(0.005)

    @property
    def gyro_data_rate_divisor(self):
        """The divisor for the rate at which gyro measurements are taken in Hz

        Note: The data rates are set indirectly by setting a rate divisor according to the
        following formula: ``gyro_data_rate = 1100/(1+divisor)``

        This function sets the raw rate divisor.
        """

        self._bank = 2
        raw_rate_divisor = self._gyro_rate_divisor
        sleep(0.005)
        self._bank = 0
        # rate_hz = 1100/(1+raw_rate_divisor)
        return raw_rate_divisor

    @gyro_data_rate_divisor.setter
    def gyro_data_rate_divisor(self, value):
        # check that value <= 255
        self._bank = 2
        sleep(0.005)
        self._gyro_rate_divisor = value
        sleep(0.005)

    def _accel_rate_calc(self, divisor):  # pylint:disable=no-self-use
        return 1125 / (1 + divisor)

    def _gyro_rate_calc(self, divisor):  # pylint:disable=no-self-use
        return 1100 / (1 + divisor)

    @property
    def accelerometer_data_rate(self):
        """The rate at which accelerometer measurements are taken in Hz

        Note: The data rates are set indirectly by setting a rate divisor according to the
        following formula: ``accelerometer_data_rate = 1125/(1+divisor)``

        This function does the math to find the divisor from a given rate but it will not be
        exactly as specified.
        """
        return self._accel_rate_calc(self.accelerometer_data_rate_divisor)

    @accelerometer_data_rate.setter
    def accelerometer_data_rate(self, value):
        if value < self._accel_rate_calc(4095) or value > self._accel_rate_calc(0):
            raise AttributeError(
                "Accelerometer data rate must be between 0.27 and 1125.0"
            )
        self.accelerometer_data_rate_divisor = value

    @property
    def gyro_data_rate(self):
        """The rate at which gyro measurements are taken in Hz

        Note: The data rates are set indirectly by setting a rate divisor according to the
        following formula: ``gyro_data_rate = 1100/(1+divisor)``
        This function does the math to find the divisor from a given rate but it will not
        be exactly as specified.
        """
        return self._gyro_rate_calc(self.gyro_data_rate_divisor)

    @gyro_data_rate.setter
    def gyro_data_rate(self, value):
        if value < self._gyro_rate_calc(4095) or value > self._gyro_rate_calc(0):
            raise AttributeError("Gyro data rate must be between 4.30 and 1100.0")

        divisor = round(((1125.0 - value) / value))
        self.gyro_data_rate_divisor = divisor

    @property
    def accel_dlpf_cutoff(self):
        """The cutoff frequency for the accelerometer's digital low pass filter. Signals
        above the given frequency will be filtered out. Must be an ``AccelDLPFCutoff``.
        Use AccelDLPFCutoff.DISABLED to disable the filter

        **Note** readings immediately following setting a cutoff frequency will be
        inaccurate due to the filter "warming up" """
        self._bank = 2
        return self._accel_dlpf_config

    @accel_dlpf_cutoff.setter
    def accel_dlpf_cutoff(self, cutoff_frequency):
        if not AccelDLPFFreq.is_valid(cutoff_frequency):
            raise AttributeError("accel_dlpf_cutoff must be an `AccelDLPFFreq`")
        self._bank = 2
        # check for shutdown
        if cutoff_frequency is AccelDLPFFreq.DISABLED:  # pylint: disable=no-member
            self._accel_dlpf_enable = False
            return
        self._accel_dlpf_enable = True
        self._accel_dlpf_config = cutoff_frequency

    @property
    def gyro_dlpf_cutoff(self):
        """The cutoff frequency for the gyro's digital low pass filter. Signals above the
        given frequency will be filtered out. Must be a ``GyroDLPFFreq``. Use
        GyroDLPFCutoff.DISABLED to disable the filter

        **Note** readings immediately following setting a cutoff frequency will be
        inaccurate due to the filter "warming up" """
        self._bank = 2
        return self._gyro_dlpf_config

    @gyro_dlpf_cutoff.setter
    def gyro_dlpf_cutoff(self, cutoff_frequency):
        if not GyroDLPFFreq.is_valid(cutoff_frequency):
            raise AttributeError("gyro_dlpf_cutoff must be a `GyroDLPFFreq`")
        self._bank = 2
        # check for shutdown
        if cutoff_frequency is GyroDLPFFreq.DISABLED:  # pylint: disable=no-member
            self._gyro_dlpf_enable = False
            return
        self._gyro_dlpf_enable = True
        self._gyro_dlpf_config = cutoff_frequency

    @property
    def _low_power(self):
        self._bank = 0
        return self._low_power_en

    @_low_power.setter
    def _low_power(self, enabled):
        self._bank = 0
        self._low_power_en = enabled


class ICM20649(ICM20X):
    """Library for the ST ICM-20649 Wide-Range 6-DoF Accelerometer and Gyro.

    :param ~busio.I2C i2c_bus: The I2C bus the ICM20649 is connected to.
    :param address: The I2C slave address of the sensor

    """

    def __init__(self, i2c_bus, address=_ICM20649_DEFAULT_ADDRESS):

        AccelRange.add_values(
            (
                ("RANGE_4G", 0, 4, 8192),
                ("RANGE_8G", 1, 8, 4096.0),
                ("RANGE_16G", 2, 16, 2048),
                ("RANGE_30G", 3, 30, 1024),
            )
        )

        GyroRange.add_values(
            (
                ("RANGE_500_DPS", 0, 500, 65.5),
                ("RANGE_1000_DPS", 1, 1000, 32.8),
                ("RANGE_2000_DPS", 2, 2000, 16.4),
                ("RANGE_4000_DPS", 3, 4000, 8.2),
            )
        )
        super().__init__(i2c_bus, address)


# https://www.y-ic.es/datasheet/78/SMDSW.020-2OZ.pdf page 19
_AK09916_WIA1 = 0x00
_AK09916_WIA2 = 0x01
_AK09916_ST1 = 0x10
_AK09916_HXL = 0x11
_AK09916_HXH = 0x12
_AK09916_HYL = 0x13
_AK09916_HYH = 0x14
_AK09916_HZL = 0x15
_AK09916_HZH = 0x16
_AK09916_ST2 = 0x18
_AK09916_CNTL2 = 0x31
_AK09916_CNTL3 = 0x32


class MagDataRate(CV):
    """Options for ``magnetometer_data_rate``"""

    pass  # pylint: disable=unnecessary-pass


class ICM20948(ICM20X):  # pylint:disable=too-many-instance-attributes
    """Library for the ST ICM-20948 Wide-Range 6-DoF Accelerometer and Gyro.

    :param ~busio.I2C i2c_bus: The I2C bus the ICM20948 is connected to.
    :param address: The I2C slave address of the sensor
    """

    _slave_finished = ROBit(_ICM20X_I2C_MST_STATUS, 6)

    # mag data is LE
    _raw_mag_data = Struct(_ICM20948_EXT_SLV_SENS_DATA_00, "<hhhh")

    _bypass_i2c_master = RWBit(_ICM20X_REG_INT_PIN_CFG, 1)
    _i2c_master_control = UnaryStruct(_ICM20X_I2C_MST_CTRL, ">B")
    _i2c_master_enable = RWBit(_ICM20X_USER_CTRL, 5)  # TODO: use this in sw reset
    _i2c_master_reset = RWBit(_ICM20X_USER_CTRL, 1)

    _slave0_addr = UnaryStruct(_ICM20X_I2C_SLV0_ADDR, ">B")
    _slave0_reg = UnaryStruct(_ICM20X_I2C_SLV0_REG, ">B")
    _slave0_ctrl = UnaryStruct(_ICM20X_I2C_SLV0_CTRL, ">B")
    _slave0_do = UnaryStruct(_ICM20X_I2C_SLV0_DO, ">B")

    _slave4_addr = UnaryStruct(_ICM20X_I2C_SLV4_ADDR, ">B")
    _slave4_reg = UnaryStruct(_ICM20X_I2C_SLV4_REG, ">B")
    _slave4_ctrl = UnaryStruct(_ICM20X_I2C_SLV4_CTRL, ">B")
    _slave4_do = UnaryStruct(_ICM20X_I2C_SLV4_DO, ">B")
    _slave4_di = UnaryStruct(_ICM20X_I2C_SLV4_DI, ">B")

    def __init__(self, i2c_bus, address=_ICM20948_DEFAULT_ADDRESS):
        AccelRange.add_values(
            (
                ("RANGE_2G", 0, 2, 16384),
                ("RANGE_4G", 1, 4, 8192),
                ("RANGE_8G", 2, 8, 4096.0),
                ("RANGE_16G", 3, 16, 2048),
            )
        )
        GyroRange.add_values(
            (
                ("RANGE_250_DPS", 0, 250, 131.0),
                ("RANGE_500_DPS", 1, 500, 65.5),
                ("RANGE_1000_DPS", 2, 1000, 32.8),
                ("RANGE_2000_DPS", 3, 2000, 16.4),
            )
        )

        # https://www.y-ic.es/datasheet/78/SMDSW.020-2OZ.pdf page 9
        MagDataRate.add_values(
            (
                ("SHUTDOWN", 0x0, "Shutdown", None),
                ("SINGLE", 0x1, "Single", None),
                ("RATE_10HZ", 0x2, 10, None),
                ("RATE_20HZ", 0x4, 20, None),
                ("RATE_50HZ", 0x6, 50, None),
                ("RATE_100HZ", 0x8, 100, None),
            )
        )
        super().__init__(i2c_bus, address)
        self._magnetometer_init()

    # A million thanks to the SparkFun folks for their library that I pillaged to write this method!
    # See their Python library here:
    # https://github.com/sparkfun/Qwiic_9DoF_IMU_ICM20948_Py
    @property
    def _mag_configured(self):
        success = False
        for _i in range(5):
            success = self._mag_id() is not None

            if success:
                return True
            self._reset_i2c_master()
            # i2c master stuck, try resetting
        return False

    def _reset_i2c_master(self):
        self._bank = 0
        self._i2c_master_reset = True

    def _magnetometer_enable(self):

        self._bank = 0
        sleep(0.100)
        self._bypass_i2c_master = False
        sleep(0.005)

        # no repeated start, i2c master clock = 345.60kHz
        self._bank = 3
        sleep(0.100)
        self._i2c_master_control = 0x17
        sleep(0.100)

        self._bank = 0
        sleep(0.100)
        self._i2c_master_enable = True
        sleep(0.020)

    def _magnetometer_init(self):
        self._magnetometer_enable()
        self.magnetometer_data_rate = (
            MagDataRate.RATE_100HZ  # pylint: disable=no-member
        )

        if not self._mag_configured:
            return False

        self._setup_mag_readout()

        return True

    # set up slave0 for reading into the bank 0 data registers
    def _setup_mag_readout(self):
        self._bank = 3
        self._slave0_addr = 0x8C
        sleep(0.005)
        self._slave0_reg = 0x11
        sleep(0.005)
        self._slave0_ctrl = 0x89  # enable
        sleep(0.005)

    def _mag_id(self):
        return self._read_mag_register(0x01)

    @property
    def magnetic(self):
        """The current magnetic field strengths onthe X, Y, and Z axes in uT (micro-teslas)"""

        self._bank = 0
        full_data = self._raw_mag_data
        sleep(0.005)

        x = full_data[0] * _ICM20X_UT_PER_LSB
        y = full_data[1] * _ICM20X_UT_PER_LSB
        z = full_data[2] * _ICM20X_UT_PER_LSB

        return (x, y, z)

    @property
    def magnetometer_data_rate(self):
        """The rate at which the magenetometer takes measurements to update its output registers"""
        # read mag DR register
        self._read_mag_register(_AK09916_CNTL2)

    @magnetometer_data_rate.setter
    def magnetometer_data_rate(self, mag_rate):
        # From https://www.y-ic.es/datasheet/78/SMDSW.020-2OZ.pdf page 9

        # "When user wants to change operation mode, transit to Power-down mode first and then
        # transit to other modes. After Power-down mode is set, at least 100 microsectons (Twait)
        # is needed before setting another mode"
        if not MagDataRate.is_valid(mag_rate):
            raise AttributeError("range must be an `MagDataRate`")
        self._write_mag_register(
            _AK09916_CNTL2, MagDataRate.SHUTDOWN  # pylint: disable=no-member
        )
        sleep(0.001)
        self._write_mag_register(_AK09916_CNTL2, mag_rate)

    def _read_mag_register(self, register_addr, slave_addr=0x0C):
        self._bank = 3

        slave_addr |= 0x80  # set top bit for read

        self._slave4_addr = slave_addr
        sleep(0.005)
        self._slave4_reg = register_addr
        sleep(0.005)
        self._slave4_ctrl = (
            0x80  # enable, don't raise interrupt, write register value, no delay
        )
        sleep(0.005)
        self._bank = 0

        finished = False
        for _i in range(100):
            finished = self._slave_finished
            if finished:  # bueno!
                break
            sleep(0.010)

        if not finished:
            return None

        self._bank = 3
        mag_register_data = self._slave4_di
        sleep(0.005)
        return mag_register_data

    def _write_mag_register(self, register_addr, value, slave_addr=0x0C):
        self._bank = 3

        self._slave4_addr = slave_addr
        sleep(0.005)
        self._slave4_reg = register_addr
        sleep(0.005)
        self._slave4_do = value
        sleep(0.005)
        self._slave4_ctrl = (
            0x80  # enable, don't raise interrupt, write register value, no delay
        )
        sleep(0.005)
        self._bank = 0

        finished = False
        for _i in range(100):
            finished = self._slave_finished
            if finished:  # bueno!
                break
            sleep(0.010)

        return finished
