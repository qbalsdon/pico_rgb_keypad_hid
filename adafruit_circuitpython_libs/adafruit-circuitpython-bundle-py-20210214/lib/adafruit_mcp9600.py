# SPDX-FileCopyrightText: 2019 Dan Cogliano for Adafruit Industries
# SPDX-FileCopyrightText: 2021 kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_mcp9600`
================================================================================

CircuitPython driver for the MCP9600 thermocouple I2C amplifier


* Author(s): Dan Cogliano, Kattni Rembor

Implementation Notes
--------------------

**Hardware:**

* Adafruit MCP9600 I2C Thermocouple Amplifier:
  https://www.adafruit.com/product/4101

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""

from struct import unpack
from micropython import const
from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_struct import UnaryStruct
from adafruit_register.i2c_bits import RWBits, ROBits
from adafruit_register.i2c_bit import RWBit, ROBit

__version__ = "1.1.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_MCP9600.git"

_DEFAULT_ADDRESS = const(0x67)

_REGISTER_HOT_JUNCTION = const(0x00)
_REGISTER_DELTA_TEMP = const(0x01)
_REGISTER_COLD_JUNCTION = const(0x02)
_REGISTER_THERM_CFG = const(0x05)
_REGISTER_VERSION = const(0x20)


class MCP9600:
    """Interface to the MCP9600 thermocouple amplifier breakout"""

    # Shutdown mode options
    NORMAL = 0b00
    SHUTDOWN = 0b01
    BURST = 0b10

    # Burst mode sample options
    BURST_SAMPLES_1 = 0b000
    BURST_SAMPLES_2 = 0b001
    BURST_SAMPLES_4 = 0b010
    BURST_SAMPLES_8 = 0b011
    BURST_SAMPLES_16 = 0b100
    BURST_SAMPLES_32 = 0b101
    BURST_SAMPLES_64 = 0b110
    BURST_SAMPLES_128 = 0b111

    # Alert temperature monitor options
    AMBIENT = 1
    THERMOCOUPLE = 0

    # Temperature change type to trigger alert. Rising is heating up. Falling is cooling down.
    RISING = 1
    FALLING = 0

    # Alert output options
    ACTIVE_HIGH = 1
    ACTIVE_LOW = 0

    # Alert mode options
    INTERRUPT = 1  # Interrupt clear option must be set when using this mode!
    COMPARATOR = 0

    # Ambient (cold-junction) temperature sensor resolution options
    AMBIENT_RESOLUTION_0_0625 = 0  # 0.0625 degrees Celsius
    AMBIENT_RESOLUTION_0_25 = 1  # 0.25 degrees Celsius

    # STATUS - 0x4
    burst_complete = RWBit(0x4, 7)
    """Burst complete."""
    temperature_update = RWBit(0x4, 6)
    """Temperature update."""
    input_range = ROBit(0x4, 4)
    """Input range."""
    alert_1 = ROBit(0x4, 0)
    """Alert 1 status."""
    alert_2 = ROBit(0x4, 1)
    """Alert 2 status."""
    alert_3 = ROBit(0x4, 2)
    """Alert 3 status."""
    alert_4 = ROBit(0x4, 3)
    """Alert 4 status."""
    # Device Configuration - 0x6
    ambient_resolution = RWBit(0x6, 7)
    """Ambient (cold-junction) temperature resolution. Options are ``AMBIENT_RESOLUTION_0_0625``
    (0.0625 degrees Celsius) or ``AMBIENT_RESOLUTION_0_25`` (0.25 degrees Celsius)."""
    burst_mode_samples = RWBits(3, 0x6, 2)
    """The number of samples taken during a burst in burst mode. Options are ``BURST_SAMPLES_1``,
    ``BURST_SAMPLES_2``, ``BURST_SAMPLES_4``, ``BURST_SAMPLES_8``, ``BURST_SAMPLES_16``,
    ``BURST_SAMPLES_32``, ``BURST_SAMPLES_64``, ``BURST_SAMPLES_128``."""
    shutdown_mode = RWBits(2, 0x6, 0)
    """Shutdown modes. Options are ``NORMAL``, ``SHUTDOWN``, and ``BURST``."""
    # Alert 1 Configuration - 0x8
    _alert_1_interrupt_clear = RWBit(0x8, 7)
    _alert_1_monitor = RWBit(0x8, 4)
    _alert_1_temp_direction = RWBit(0x8, 3)
    _alert_1_state = RWBit(0x8, 2)
    _alert_1_mode = RWBit(0x8, 1)
    _alert_1_enable = RWBit(0x8, 0)
    # Alert 2 Configuration - 0x9
    _alert_2_interrupt_clear = RWBit(0x9, 7)
    _alert_2_monitor = RWBit(0x9, 4)
    _alert_2_temp_direction = RWBit(0x9, 3)
    _alert_2_state = RWBit(0x9, 2)
    _alert_2_mode = RWBit(0x9, 1)
    _alert_2_enable = RWBit(0x9, 0)
    # Alert 3 Configuration - 0xa
    _alert_3_interrupt_clear = RWBit(0xA, 7)
    _alert_3_monitor = RWBit(0xA, 4)
    _alert_3_temp_direction = RWBit(0xA, 3)
    _alert_3_state = RWBit(0xA, 2)
    _alert_3_mode = RWBit(0xA, 1)
    _alert_3_enable = RWBit(0xA, 0)
    # Alert 4 Configuration - 0xb
    _alert_4_interrupt_clear = RWBit(0xB, 7)
    _alert_4_monitor = RWBit(0xB, 4)
    _alert_4_temp_direction = RWBit(0xB, 3)
    _alert_4_state = RWBit(0xB, 2)
    _alert_4_mode = RWBit(0xB, 1)
    _alert_4_enable = RWBit(0xB, 0)
    # Alert 1 Hysteresis - 0xc
    _alert_1_hysteresis = UnaryStruct(0xC, ">H")
    # Alert 2 Hysteresis - 0xd
    _alert_2_hysteresis = UnaryStruct(0xD, ">H")
    # Alert 3 Hysteresis - 0xe
    _alert_3_hysteresis = UnaryStruct(0xE, ">H")
    # Alert 4 Hysteresis - 0xf
    _alert_4_hysteresis = UnaryStruct(0xF, ">H")
    # Alert 1 Limit - 0x10
    _alert_1_temperature_limit = UnaryStruct(0x10, ">H")
    # Alert 2 Limit - 0x11
    _alert_2_limit = UnaryStruct(0x11, ">H")
    # Alert 3 Limit - 0x12
    _alert_3_limit = UnaryStruct(0x12, ">H")
    # Alert 4 Limit - 0x13
    _alert_4_limit = UnaryStruct(0x13, ">H")
    # Device ID/Revision - 0x20
    _device_id = ROBits(8, 0x20, 8, register_width=2, lsb_first=False)
    _revision_id = ROBits(8, 0x20, 0, register_width=2)

    types = ("K", "J", "T", "N", "S", "E", "B", "R")

    def __init__(self, i2c, address=_DEFAULT_ADDRESS, tctype="K", tcfilter=0):
        self.buf = bytearray(3)
        self.i2c_device = I2CDevice(i2c, address)
        self.type = tctype
        # is this a valid thermocouple type?
        if tctype not in MCP9600.types:
            raise Exception("invalid thermocouple type ({})".format(tctype))
        # filter is from 0 (none) to 7 (max), can limit spikes in
        # temperature readings
        tcfilter = min(7, max(0, tcfilter))
        ttype = MCP9600.types.index(tctype)

        self.buf[0] = _REGISTER_THERM_CFG
        self.buf[1] = tcfilter | (ttype << 4)
        with self.i2c_device as tci2c:
            tci2c.write(self.buf, end=2)
        if self._device_id != 0x40:
            raise RuntimeError("Failed to find MCP9600 - check wiring!")

    def alert_config(
        self,
        *,
        alert_number,
        alert_temp_source,
        alert_temp_limit,
        alert_hysteresis,
        alert_temp_direction,
        alert_mode,
        alert_state
    ):
        """Configure a specified alert pin. Alert is enabled by default when alert is configured.
        To disable an alert pin, use ``alert_disable``.

        :param int alert_number: The alert pin number. Must be 1-4.
        :param alert_temp_source: The temperature source to monitor for the alert. Options are:
                                  ``THERMOCOUPLE`` (hot-junction) or ``AMBIENT`` (cold-junction).
                                  Temperatures are in Celsius.
        :param float alert_temp_limit: The temperature in degrees Celsius at which the alert should
                                       trigger. For rising temperatures, the alert will trigger when
                                       the temperature rises above this limit. For falling
                                       temperatures, the alert will trigger when the temperature
                                       falls below this limit.
        :param float alert_hysteresis: The alert hysteresis range. Must be 0-255 degrees Celsius.
                                       For rising temperatures, the hysteresis is below alert limit.
                                       For falling temperatures, the hysteresis is above alert
                                       limit. See data-sheet for further information.
        :param alert_temp_direction: The direction the temperature must change to trigger the alert.
                                     Options are ``RISING`` (heating up) or ``FALLING`` (cooling
                                     down).
        :param alert_mode: The alert mode. Options are ``COMPARATOR`` or ``INTERRUPT``. In
                           comparator mode, the pin will follow the alert, so if the temperature
                           drops, for example, the alert pin will go back low. In interrupt mode,
                           by comparison, once the alert goes off, you must manually clear it. If
                           setting mode to ``INTERRUPT``, use ``alert_interrupt_clear`` to clear the
                           interrupt flag.
        :param alert_state: Alert pin output state. Options are ``ACTIVE_HIGH`` or ``ACTIVE_LOW``.


        For example, to configure alert 1:

        .. code-block:: python

            import board
            import busio
            import digitalio
            import adafruit_mcp9600

            i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
            mcp = adafruit_mcp9600.MCP9600(i2c)
            alert_1 = digitalio.DigitalInOut(board.D5)
            alert_1.switch_to_input()

            mcp.alert_config(alert_number=1, alert_temp_source=mcp.THERMOCOUPLE,
                             alert_temp_limit=25, alert_hysteresis=0,
                             alert_temp_direction=mcp.RISING, alert_mode=mcp.COMPARATOR,
                             alert_state=mcp.ACTIVE_LOW)

        """
        if alert_number not in (1, 2, 3, 4):
            raise ValueError("Alert pin number must be 1-4.")
        if not 0 <= alert_hysteresis < 256:
            raise ValueError("Hysteresis value must be 0-255.")
        setattr(self, "_alert_%d_monitor" % alert_number, alert_temp_source)
        setattr(
            self,
            "_alert_%d_temperature_limit" % alert_number,
            int(alert_temp_limit / 0.0625),
        )
        setattr(self, "_alert_%d_hysteresis" % alert_number, alert_hysteresis)
        setattr(self, "_alert_%d_temp_direction" % alert_number, alert_temp_direction)
        setattr(self, "_alert_%d_mode" % alert_number, alert_mode)
        setattr(self, "_alert_%d_state" % alert_number, alert_state)
        setattr(self, "_alert_%d_enable" % alert_number, True)

    def alert_disable(self, alert_number):
        """Configuring an alert using ``alert_config()`` enables the specified alert by default.
        Use ``alert_disable`` to disable an alert pin.

        :param int alert_number: The alert pin number. Must be 1-4.

        """
        if alert_number not in (1, 2, 3, 4):
            raise ValueError("Alert pin number must be 1-4.")
        setattr(self, "_alert_%d_enable" % alert_number, False)

    def alert_interrupt_clear(self, alert_number, interrupt_clear=True):
        """Turns off the alert flag in the MCP9600, and clears the pin state (not used if the alert
        is in comparator mode). Required when ``alert_mode`` is ``INTERRUPT``.

        :param int alert_number: The alert pin number. Must be 1-4.
        :param bool interrupt_clear: The bit to write the interrupt state flag

        """
        if alert_number not in (1, 2, 3, 4):
            raise ValueError("Alert pin number must be 1-4.")
        setattr(self, "_alert_%d_interrupt_clear" % alert_number, interrupt_clear)

    @property
    def version(self):
        """ MCP9600 chip version """
        data = self._read_register(_REGISTER_VERSION, 2)
        return unpack(">xH", data)[0]

    @property
    def ambient_temperature(self):
        """ Cold junction/ambient/room temperature in Celsius """
        data = self._read_register(_REGISTER_COLD_JUNCTION, 2)
        value = unpack(">xH", data)[0] * 0.0625
        if data[1] & 0x80:
            value -= 4096
        return value

    @property
    def temperature(self):
        """ Hot junction temperature in Celsius """
        data = self._read_register(_REGISTER_HOT_JUNCTION, 2)
        value = unpack(">xH", data)[0] * 0.0625
        if data[1] & 0x80:
            value -= 4096
        return value

    @property
    def delta_temperature(self):
        """ Delta temperature in Celsius """
        data = self._read_register(_REGISTER_DELTA_TEMP, 2)
        value = unpack(">xH", data)[0] * 0.0625
        if data[1] & 0x80:
            value -= 4096
        return value

    def _read_register(self, reg, count=1):
        self.buf[0] = reg
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.buf, self.buf, out_end=count, in_start=1)
        return self.buf
