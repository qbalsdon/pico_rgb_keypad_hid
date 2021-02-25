# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_si4713`
====================================================

CircuitPython module for the SI4713 RDS FM transmitter.  See
examples/simpletest.py for a demo of the usage.  Based on the Arduino library
at: https://github.com/adafruit/Adafruit-Si4713-Library/

* Author(s): Tony DiCola
"""
import time

from micropython import const

try:
    import struct
except ImportError:
    import ustruct as struct

import adafruit_bus_device.i2c_device as i2c_device


__version__ = "1.2.5"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_SI4713.git"


# Internal constants:
_SI4710_ADDR0 = const(0x11)  # if SEN is = const(low)
_SI4710_ADDR1 = const(0x63)  # if SEN is high, default
_SI4710_STATUS_CTS = const(0x80)
_SI4710_CMD_POWER_UP = const(0x01)
_SI4710_CMD_GET_REV = const(0x10)
_SI4710_CMD_POWER_DOWN = const(0x11)
_SI4710_CMD_SET_PROPERTY = const(0x12)
_SI4710_CMD_GET_PROPERTY = const(0x13)
_SI4710_CMD_GET_INT_STATUS = const(0x14)
_SI4710_CMD_PATCH_ARGS = const(0x15)
_SI4710_CMD_PATCH_DATA = const(0x16)
_SI4710_CMD_TX_TUNE_FREQ = const(0x30)
_SI4710_CMD_TX_TUNE_POWER = const(0x31)
_SI4710_CMD_TX_TUNE_MEASURE = const(0x32)
_SI4710_CMD_TX_TUNE_STATUS = const(0x33)
_SI4710_CMD_TX_ASQ_STATUS = const(0x34)
_SI4710_CMD_TX_RDS_BUFF = const(0x35)
_SI4710_CMD_TX_RDS_PS = const(0x36)
_SI4710_CMD_TX_AGC_OVERRIDE = const(0x48)
_SI4710_CMD_GPO_CTL = const(0x80)
_SI4710_CMD_GPO_SET = const(0x81)
_SI4713_PROP_GPO_IEN = const(0x0001)
_SI4713_PROP_DIGITAL_INPUT_FORMAT = const(0x0101)
_SI4713_PROP_DIGITAL_INPUT_SAMPLE_RATE = const(0x0103)
_SI4713_PROP_REFCLK_FREQ = const(0x0201)
_SI4713_PROP_REFCLK_PRESCALE = const(0x0202)
_SI4713_PROP_TX_COMPONENT_ENABLE = const(0x2100)
_SI4713_PROP_TX_AUDIO_DEVIATION = const(0x2101)
_SI4713_PROP_TX_PILOT_DEVIATION = const(0x2102)
_SI4713_PROP_TX_RDS_DEVIATION = const(0x2103)
_SI4713_PROP_TX_LINE_LEVEL_INPUT_LEVEL = const(0x2104)
_SI4713_PROP_TX_LINE_INPUT_MUTE = const(0x2105)
_SI4713_PROP_TX_PREEMPHASIS = const(0x2106)
_SI4713_PROP_TX_PILOT_FREQUENCY = const(0x2107)
_SI4713_PROP_TX_ACOMP_ENABLE = const(0x2200)
_SI4713_PROP_TX_ACOMP_THRESHOLD = const(0x2201)
_SI4713_PROP_TX_ATTACK_TIME = const(0x2202)
_SI4713_PROP_TX_RELEASE_TIME = const(0x2203)
_SI4713_PROP_TX_ACOMP_GAIN = const(0x2204)
_SI4713_PROP_TX_LIMITER_RELEASE_TIME = const(0x2205)
_SI4713_PROP_TX_ASQ_INTERRUPT_SOURCE = const(0x2300)
_SI4713_PROP_TX_ASQ_LEVEL_LOW = const(0x2301)
_SI4713_PROP_TX_ASQ_DURATION_LOW = const(0x2302)
_SI4713_PROP_TX_AQS_LEVEL_HIGH = const(0x2303)
_SI4713_PROP_TX_AQS_DURATION_HIGH = const(0x2304)
_SI4713_PROP_TX_RDS_INTERRUPT_SOURCE = const(0x2C00)
_SI4713_PROP_TX_RDS_PI = const(0x2C01)
_SI4713_PROP_TX_RDS_PS_MIX = const(0x2C02)
_SI4713_PROP_TX_RDS_PS_MISC = const(0x2C03)
_SI4713_PROP_TX_RDS_PS_REPEAT_COUNT = const(0x2C04)
_SI4713_PROP_TX_RDS_MESSAGE_COUNT = const(0x2C05)
_SI4713_PROP_TX_RDS_PS_AF = const(0x2C06)
_SI4713_PROP_TX_RDS_FIFO_SIZE = const(0x2C07)


class SI4713:
    """SI4713 RDS FM transmitter.  Initialize by specifying:
     - i2c: The I2C bus connected to the board.

    Optionally specify:
     - address: The I2C address if it has been changed.
     - reset: A DigitalInOut instance connected to the board's reset line,
              this will be used to perform a soft reset when necessary.
     - timeout_s: The amount of time (in seconds) to wait for a command to
                  succeed.  If this timeout is exceed a runtime error is thrown.
    """

    # Class-level buffer to reduce allocations and heap fragmentation.
    # This is not thread-safe or re-entrant by design!
    _BUFFER = bytearray(10)

    def __init__(self, i2c, *, address=_SI4710_ADDR1, reset=None, timeout_s=0.1):
        self._timeout_s = timeout_s

        # Configure reset line if it was provided.
        self._reset = reset

        if self._reset is not None:
            self._reset.switch_to_output(value=True)

            # Toggle reset line low to reset the chip and then wait a bit for
            # startup - this is necessary before initializing as an i2c device
            # on at least the Raspberry Pi, and potentially elsewhere:
            self._reset.value = True
            time.sleep(0.01)
            self._reset.value = False
            time.sleep(0.01)
            self._reset.value = True
            time.sleep(0.25)

        self._device = i2c_device.I2CDevice(i2c, address)
        self.reset()
        # Check product ID.
        if self._get_product_number() != 13:
            raise RuntimeError("Failed to find SI4713, check wiring!")

    def _read_u8(self, address):
        # Read an 8-bit unsigned value from the specified 8-bit address.
        with self._device as i2c:
            self._BUFFER[0] = address & 0xFF
            # TODO: This is probably wrong and should be write_then_readinto to avoid a stop before
            # repeated start.
            i2c.write(self._BUFFER, end=1)
            i2c.readinto(self._BUFFER, end=1)
        return self._BUFFER[0]

    def _read_into(self, buf, count=None):
        # Read data directly from the I2C bus into the specified buffer.  If
        # count is not provided the buffer will be filled, otherwise count bytes
        # will be written to the buffer.
        if count is None:
            count = len(buf)
        with self._device as i2c:
            i2c.readinto(buf, end=count)

    def _write_from(self, buf, count=None):
        # Write a buffer of byte data to the chip.  If count is not specified
        # then the entire buffer is written, otherwise count bytes are written.
        # This function will wait to verify the command was successfully
        # sent/performed and if it fails to see success in the specified
        # timeout (100ms by default) it will throw an exception.
        if count is None:
            count = len(buf)
        # Send command.
        # TODO: This probably needs to be one write_then_readinto.
        with self._device as i2c:
            i2c.write(buf, end=count)
        # Poll the status bit waiting for success or throwing a timeout error.
        start = time.monotonic()
        while True:
            with self._device as i2c:
                i2c.readinto(self._BUFFER, end=1)
            if self._BUFFER[0] & _SI4710_STATUS_CTS > 0:
                return
            if time.monotonic() - start > self._timeout_s:
                raise RuntimeError("Timeout waiting for SI4723 response, check wiring!")

    def _set_property(self, prop, val):
        # Set a property of the SI4713 chip.  These are both 16-bit values.
        self._BUFFER[0] = _SI4710_CMD_SET_PROPERTY
        self._BUFFER[1] = 0
        self._BUFFER[2] = prop >> 8
        self._BUFFER[3] = prop & 0xFF
        self._BUFFER[4] = val >> 8
        self._BUFFER[5] = val & 0xFF
        self._write_from(self._BUFFER, count=6)

    def _get_product_number(self):
        # Retrieve the product number/ID value of the chip and return it.
        # First send a get revision command.
        self._BUFFER[0] = _SI4710_CMD_GET_REV
        self._BUFFER[1] = 0
        self._write_from(self._BUFFER, count=2)
        # Then read 9 bytes to get the response data and parse out pn.
        with self._device as i2c:
            i2c.readinto(self._BUFFER, end=9)
        return self._BUFFER[1]
        # Other potentially useful but unused data:
        # fw = (self._BUFFER[2] << 8) | self._BUFFER[3]
        # patch = (self._BUFFER[4] << 8) | self._BUFFER[5]
        # cmp = (self._BUFFER[6] << 8) | self._BUFFER[7]
        # rev = (self._BUFFER[8])

    def reset(self):
        """Perform a reset of the chip using the reset line.  Will also
        perform necessary chip power up procedures."""
        # Toggle reset low for a few milliseconds if the line was provided.
        if self._reset is not None:
            # Toggle reset line low for a few milliseconds to reset the chip.
            self._reset.value = True
            time.sleep(0.01)
            self._reset.value = False
            time.sleep(0.01)
            self._reset.value = True
        # Next perform all the chip power up procedures.
        self._BUFFER[0] = _SI4710_CMD_POWER_UP
        self._BUFFER[1] = 0x12
        # CTS interrupt disabled
        # GPO2 output disabled
        # Boot normally
        # xtal oscillator ENabled
        # FM transmit
        self._BUFFER[2] = 0x50  # analog input mode
        self._write_from(self._BUFFER, count=3)
        # configuration! see datasheet page 254
        # crystal is 32.768
        self._set_property(_SI4713_PROP_REFCLK_FREQ, 32768)
        # 74uS pre-emph (USA std)
        self._set_property(_SI4713_PROP_TX_PREEMPHASIS, 0)
        # max gain?
        self._set_property(_SI4713_PROP_TX_ACOMP_GAIN, 10)
        # turn on limiter and AGC
        self._set_property(_SI4713_PROP_TX_ACOMP_ENABLE, 0x0)

    @property
    def interrupt_status(self):
        """Read the interrupt bit status of the chip.  This will return a byte
        value with interrupt status bits as defined by the radio, see page
        11 of the AN332 programming guide:
        https://www.silabs.com/documents/public/application-notes/AN332.pdf
        """
        return self._read_u8(_SI4710_CMD_GET_INT_STATUS)

    def _poll_interrupt_status(self, expected):
        # Poll the interrupt status bit for an expected exact value.
        # Will throw an exception if the timeout is exceeded before the status
        # reaches the desired value.
        start = time.monotonic()
        while self.interrupt_status != expected:
            time.sleep(0.01)  # Short delay for other processing.
            if time.monotonic() - start > self._timeout_s:
                raise RuntimeError("Timeout waiting for SI4713 to respond!")

    def _tune_status(self):
        # Retrieve the tune status command values from the radio.  Will store
        # the raw result of the tune status command in self._BUFFER (see page
        # 22 of AN332).
        # Construct tune status command and send it.
        self._BUFFER[0] = _SI4710_CMD_TX_TUNE_STATUS
        self._BUFFER[1] = 0x01
        self._write_from(self._BUFFER, count=2)
        # Now read 8 bytes of response data.
        self._read_into(self._BUFFER, count=8)

    def _asq_status(self):
        # Retrieve the ASQ (audio signal quality) status from the chip.  Will
        # store the raw result of the ASQ status command in self._BUFFER (see
        # page 25 of AN332).
        # Construct ASQ status command and send it.
        self._BUFFER[0] = _SI4710_CMD_TX_ASQ_STATUS
        self._BUFFER[1] = 0x01
        self._write_from(self._BUFFER, count=2)
        # Now read 5 bytes of response data.
        self._read_into(self._BUFFER, count=5)

    @property
    def tx_frequency_khz(self):
        """Get and set the transmit frequency of the chip (in kilohertz).  See
        AN332 page 19 for a discussion of the constraints on this value, in
        particular only a multiple of 50khz can be specified, and the value
        must be between 76 and 108mhz.
        """
        self._tune_status()
        # Reconstruct frequency from tune status response.
        frequency = (self._BUFFER[2] << 8) | self._BUFFER[3]
        # Return result, scaling back to khz from 10's of khz.
        return frequency * 10

    @tx_frequency_khz.setter
    def tx_frequency_khz(self, val):
        assert 76000 <= val <= 108000
        assert (val % 50) == 0
        # Convert to units of 10khz that chip expects.
        val = (val // 10) & 0xFFFF
        # Construct tune command.
        self._BUFFER[0] = _SI4710_CMD_TX_TUNE_FREQ
        self._BUFFER[1] = 0
        self._BUFFER[2] = val >> 8
        self._BUFFER[3] = val & 0xFF
        self._write_from(self._BUFFER, count=4)
        # Wait for the CTS and tune complete bits to be set.
        self._poll_interrupt_status(0x81)

    @property
    def tx_power(self):
        """Get and set the transmit power in dBuV (decibel microvolts).  Can
        be a value within the range of 88-115, or 0 to indicate transmission
        power is disabled.  Setting this value assumes auto-tuning of antenna
        capacitance, see the set_tx_power_capacitance function for explicit
        control of setting both transmit power and capacitance if needed.
        """
        self._tune_status()
        # Reconstruct power from tune status response and return it.
        return self._BUFFER[5]

    def set_tx_power_capacitance(self, tx_power, capacitance):
        """Set both the transmit power (in dBuV, from 88-115) and antenna
        capacitance of the transmitter.  Capacitance is a value specified in
        pF from 0.25 to 47.75 (in 0.25 steps), or 0 to indicate automatic
        tuning. You typically don't need to use this function unless you want
        explicit control of tuning antenna capacitance, instead for simple
        transmit power changes use the tx_power property (which assumes
        automatic antenna capacitance).
        """
        # Validate tx power and capacitance are in allowed range.
        assert tx_power == 0 or (88 <= tx_power <= 115)
        assert capacitance == 0 or (0.25 <= capacitance <= 47.75)
        # Convert capacitance to 0.25 pF units that chip expects.
        capacitance = int(capacitance / 0.25)
        # Construct a tune power command and send it.
        self._BUFFER[0] = _SI4710_CMD_TX_TUNE_POWER
        self._BUFFER[1] = 0
        self._BUFFER[2] = 0
        self._BUFFER[3] = tx_power & 0xFF
        self._BUFFER[4] = capacitance & 0xFF
        self._write_from(self._BUFFER, count=5)

    @tx_power.setter
    def tx_power(self, val):
        # Assume automatic antenna capacitance tuning (0 value).
        self.set_tx_power_capacitance(val, 0)

    @property
    def tx_antenna_capacitance(self):
        """Read the transmit antenna capacitance in pico-Farads (pF).  Use the
        set_tx_power_capacitance function to change this value (must also
        change transmit power at the same time).  It's uncommon to adjust this
        beyond the automatic tuning option!
        """
        self._tune_status()
        # Reconstruct capacitance from tune status response and return it
        # (scaled appropriately for pF units).
        return self._BUFFER[6] * 0.25

    def received_noise_level(self, frequency_khz, antenna_capacitance=0):
        """Measure the received noise level for the specified frequency (in
        kilohertz, 76mhz - 108mhz and must be a multiple of 50) and return its
        value in units of dBuV (decibel microvolts).  Will use automatic
        antenna capacitance tuning by default, otherwise specify an antenna
        capacitance in pF from 0.25 to 47.75 (only steps of 0.25pF are
        supported).
        """
        # Validate frequency and capacitance.
        assert 76000 <= frequency_khz <= 108000
        assert (frequency_khz % 50) == 0
        assert antenna_capacitance == 0 or (0.25 <= antenna_capacitance <= 47.75)
        # Convert frequency and capacitance to units used by the chip.
        frequency_khz = (frequency_khz // 10) & 0xFFFF
        antenna_capacitance = int(antenna_capacitance / 0.25)
        # First send a read tune measure command to kick off the measurement.
        self._BUFFER[0] = _SI4710_CMD_TX_TUNE_MEASURE
        self._BUFFER[1] = 0
        self._BUFFER[2] = frequency_khz >> 8
        self._BUFFER[3] = frequency_khz & 0xFF
        self._BUFFER[4] = antenna_capacitance
        self._write_from(self._BUFFER, count=5)
        # Wait for CTS and tune measure complete bits to be set.
        self._poll_interrupt_status(0x81)
        # Finally make a request for tune status and grab the received noise
        # level value now that it's up to date.
        self._tune_status()
        return self._BUFFER[7]

    @property
    def input_level(self):
        """Read the input level of audio to the chip and return it in dBfs
        units.
        """
        # Perform ASQ request, then parse out 8 bit _signed_ input level value.
        self._asq_status()
        return struct.unpack("bbbbb", self._BUFFER[0:5])[4]

    @property
    def audio_signal_status(self):
        """Retrieve the ASQ or audio signal quality status value from the chip.
        This is a byte that indicates if the transmitted input audio signal is
        overmodulating (too high) or above/below input audio level thresholds.
        See page 25 of AN332 for more discussion of this value:
        https://www.silabs.com/documents/public/application-notes/AN332.pdf
        """
        # Perform ASQ request, the parse out the status byte.
        self._asq_status()
        return self._BUFFER[1]

    def gpio_control(self, gpio1=False, gpio2=False, gpio3=False):
        """Control the GPIO outputs of the chip.  Each gpio1, gpio2, gpio3
        parameter is a boolean that indicates if that GPIO channel
        (corresponding to GPIO1, GPIO2, GPIO3 of the chip respectively) is
        driven actively (True) or is high-impedence/off (False).  By default
        any unspecified GPIO is set to high-impedence/off unless otherwise
        provided.
        """
        # Construct GPIO control state and send a GPIO control command.
        control = 0x00
        if gpio1:
            control |= 0b00000010
        if gpio2:
            control |= 0b00000100
        if gpio3:
            control |= 0b00001000
        self._BUFFER[0] = _SI4710_CMD_GPO_CTL
        self._BUFFER[1] = control
        self._write_from(self._BUFFER, count=2)

    def gpio_set(self, gpio1=False, gpio2=False, gpio3=False):
        """Drive the GPIO outputs of the chip that are enabled with active
        output.  Each gpio1, gpio2, gpio3 parameter is a boolean that indicates
        if the associated GPIO (corresponding to GPIO1, GPIO2, GPIO3 of the
        chip respectively) is driven high (True) or low (False).  By default
        all GPIO are assumed to be set low (False) unless otherwise
        specified.  Note that you must first set GPIOs to active output with
        the gpio_control function to see their output physically change.
        """
        # Construct GPIO set command and send it.
        set_command = 0x00
        if gpio1:
            set_command |= 0b00000010
        if gpio2:
            set_command |= 0b00000100
        if gpio3:
            set_command |= 0b00001000
        self._BUFFER[0] = _SI4710_CMD_GPO_SET
        self._BUFFER[1] = set_command
        self._write_from(self._BUFFER, count=2)

    def _set_rds_station(self, station):
        # Set the RDS station broadcast value.
        station_length = len(station)
        assert 0 <= station_length <= 96
        # Fire off each 4 byte update of the station value.
        for i in range(0, station_length, 4):
            self._BUFFER[0] = _SI4710_CMD_TX_RDS_PS
            self._BUFFER[1] = i // 4
            self._BUFFER[2] = station[i] if i < station_length else 0x00
            self._BUFFER[3] = station[i + 1] if i + 1 < station_length else 0x00
            self._BUFFER[4] = station[i + 2] if i + 2 < station_length else 0x00
            self._BUFFER[5] = station[i + 3] if i + 3 < station_length else 0x00
            self._write_from(self._BUFFER, count=6)

    def _set_rds_buffer(self, rds_buffer):
        # Set the RDS buffer broadcast value.
        buf_length = len(rds_buffer)
        # 53 blocks in the circular buffer, each 2 bytes long.
        assert 0 <= buf_length <= 106
        # Fire off each 4 byte update of the station value.
        for i in range(0, buf_length, 4):
            self._BUFFER[0] = _SI4710_CMD_TX_RDS_BUFF
            self._BUFFER[1] = 0x06 if i == 0 else 0x04
            self._BUFFER[2] = 0x20
            self._BUFFER[3] = i // 4
            self._BUFFER[4] = rds_buffer[i] if i < buf_length else 0x00
            self._BUFFER[5] = rds_buffer[i + 1] if i + 1 < buf_length else 0x00
            self._BUFFER[6] = rds_buffer[i + 2] if i + 2 < buf_length else 0x00
            self._BUFFER[7] = rds_buffer[i + 3] if i + 3 < buf_length else 0x00
            self._write_from(self._BUFFER, count=8)

    rds_station = property(
        None,
        _set_rds_station,
        None,
        """Set the RDS broadcast station to the specified
                           byte string.  Can be at most 96 bytes long and will
                           be padded with blank spaces if less.
                           """,
    )

    rds_buffer = property(
        None,
        _set_rds_buffer,
        None,
        """Set the RDS broadcast buffer to the specified byte
                          string.  Can be at most 106 bytes long and will be
                          padded with blank spaces if less.
                          """,
    )

    def configure_rds(self, program_id, station=None, rds_buffer=None):
        """Configure and enable the RDS broadcast of the specified program ID.
        Program ID must be a 16-bit value that will be broacast on the RDS
        bands of the transmitter.  Specify optional station and RDS buffer
        strings that will be used to broadcast the station and currently
        playing song information, or later set the rds_station and
        rds_buffer to change these values too.  The station value is up to 96
        bytes long, and the buffer is up to 106 bytes long.  Note this will
        configure RDS properties of the chip for a typical North American RDS
        broadcast (deviation, mix, repeat, etc. parameters).
        """
        assert 0 <= program_id <= 65535
        # Set RDS parameters:
        # 66.25KHz (default is 68.25)
        self._set_property(_SI4713_PROP_TX_AUDIO_DEVIATION, 6625)
        # 2KHz (default)
        self._set_property(_SI4713_PROP_TX_RDS_DEVIATION, 200)
        # RDS IRQ
        self._set_property(_SI4713_PROP_TX_RDS_INTERRUPT_SOURCE, 0x0001)
        # program identifier
        self._set_property(_SI4713_PROP_TX_RDS_PI, program_id)
        # 50% mix (default)
        self._set_property(_SI4713_PROP_TX_RDS_PS_MIX, 0x03)
        # RDSD0 & RDSMS (default)
        self._set_property(_SI4713_PROP_TX_RDS_PS_MISC, 0x1808)
        # 3 repeats (default)
        self._set_property(_SI4713_PROP_TX_RDS_PS_REPEAT_COUNT, 3)
        self._set_property(_SI4713_PROP_TX_RDS_MESSAGE_COUNT, 1)
        # no AF
        self._set_property(_SI4713_PROP_TX_RDS_PS_AF, 0xE0E0)
        self._set_property(_SI4713_PROP_TX_RDS_FIFO_SIZE, 0)
        self._set_property(_SI4713_PROP_TX_COMPONENT_ENABLE, 0x0007)
        # Set station and buffer to initial values if specified.
        if station is not None:
            self._set_rds_station(station)
        if rds_buffer is not None:
            self._set_rds_buffer(rds_buffer)
