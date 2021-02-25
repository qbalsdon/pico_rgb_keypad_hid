# SPDX-FileCopyrightText: 2017 Tony DiCola for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_rfm69`
====================================================

CircuitPython RFM69 packet radio module. This supports basic RadioHead-compatible sending and
receiving of packets with RFM69 series radios (433/915Mhz).

.. warning:: This is NOT for LoRa radios!

.. note:: This is a 'best effort' at receiving data using pure Python code--there is not interrupt
    support so you might lose packets if they're sent too quickly for the board to process them.
    You will have the most luck using this in simple low bandwidth scenarios like sending and
    receiving a 60 byte packet at a time--don't try to receive many kilobytes of data at a time!

* Author(s): Tony DiCola, Jerry Needell

Implementation Notes
--------------------

**Hardware:**

* Adafruit `RFM69HCW Transceiver Radio Breakout - 868 or 915 MHz - RadioFruit
  <https://www.adafruit.com/product/3070>`_ (Product ID: 3070)

* Adafruit `RFM69HCW Transceiver Radio Breakout - 433 MHz - RadioFruit
  <https://www.adafruit.com/product/3071>`_ (Product ID: 3071)

* Adafruit `Feather M0 RFM69HCW Packet Radio - 868 or 915 MHz - RadioFruit
  <https://www.adafruit.com/product/3176>`_ (Product ID: 3176)

* Adafruit `Feather M0 RFM69HCW Packet Radio - 433 MHz - RadioFruit
  <https://www.adafruit.com/product/3177>`_ (Product ID: 3177)

* Adafruit `Radio FeatherWing - RFM69HCW 900MHz - RadioFruit
  <https://www.adafruit.com/product/3229>`_ (Product ID: 3229)

* Adafruit `Radio FeatherWing - RFM69HCW 433MHz - RadioFruit
  <https://www.adafruit.com/product/3230>`_ (Product ID: 3230)

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the ESP8622 and M0-based boards:
  https://github.com/adafruit/circuitpython/releases
* Adafruit's Bus Device library: https://github.com/adafruit/Adafruit_CircuitPython_BusDevice
"""
import time
import random

from micropython import const

import adafruit_bus_device.spi_device as spidev


__version__ = "2.1.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_RFM69.git"


# Internal constants:
_REG_FIFO = const(0x00)
_REG_OP_MODE = const(0x01)
_REG_DATA_MOD = const(0x02)
_REG_BITRATE_MSB = const(0x03)
_REG_BITRATE_LSB = const(0x04)
_REG_FDEV_MSB = const(0x05)
_REG_FDEV_LSB = const(0x06)
_REG_FRF_MSB = const(0x07)
_REG_FRF_MID = const(0x08)
_REG_FRF_LSB = const(0x09)
_REG_VERSION = const(0x10)
_REG_PA_LEVEL = const(0x11)
_REG_RX_BW = const(0x19)
_REG_AFC_BW = const(0x1A)
_REG_RSSI_VALUE = const(0x24)
_REG_DIO_MAPPING1 = const(0x25)
_REG_IRQ_FLAGS1 = const(0x27)
_REG_IRQ_FLAGS2 = const(0x28)
_REG_PREAMBLE_MSB = const(0x2C)
_REG_PREAMBLE_LSB = const(0x2D)
_REG_SYNC_CONFIG = const(0x2E)
_REG_SYNC_VALUE1 = const(0x2F)
_REG_PACKET_CONFIG1 = const(0x37)
_REG_FIFO_THRESH = const(0x3C)
_REG_PACKET_CONFIG2 = const(0x3D)
_REG_AES_KEY1 = const(0x3E)
_REG_TEMP1 = const(0x4E)
_REG_TEMP2 = const(0x4F)
_REG_TEST_PA1 = const(0x5A)
_REG_TEST_PA2 = const(0x5C)
_REG_TEST_DAGC = const(0x6F)

_TEST_PA1_NORMAL = const(0x55)
_TEST_PA1_BOOST = const(0x5D)
_TEST_PA2_NORMAL = const(0x70)
_TEST_PA2_BOOST = const(0x7C)

# The crystal oscillator frequency and frequency synthesizer step size.
# See the datasheet for details of this calculation.
_FXOSC = 32000000.0
_FSTEP = _FXOSC / 524288

# RadioHead specific compatibility constants.
_RH_BROADCAST_ADDRESS = const(0xFF)
# The acknowledgement bit in the FLAGS
# The top 4 bits of the flags are reserved for RadioHead. The lower 4 bits are reserved
# for application layer use.
_RH_FLAGS_ACK = const(0x80)
_RH_FLAGS_RETRY = const(0x40)

# User facing constants:
SLEEP_MODE = 0b000
STANDBY_MODE = 0b001
FS_MODE = 0b010
TX_MODE = 0b011
RX_MODE = 0b100

# Disable the silly too many instance members warning.  Pylint has no knowledge
# of the context and is merely guessing at the proper amount of members.  This
# is a complex chip which requires exposing many attributes and state.  Disable
# the warning to work around the error.
# pylint: disable=too-many-instance-attributes


class RFM69:
    """Interface to a RFM69 series packet radio.  Allows simple sending and
    receiving of wireless data at supported frequencies of the radio
    (433/915mhz).

    :param busio.SPI spi: The SPI bus connected to the chip.  Ensure SCK, MOSI, and MISO are
        connected.
    :param ~digitalio.DigitalInOut cs: A DigitalInOut object connected to the chip's CS/chip select
        line.
    :param ~digitalio.DigitalInOut reset: A DigitalInOut object connected to the chip's RST/reset
        line.
    :param int frequency: The center frequency to configure for radio transmission and reception.
        Must be a frequency supported by your hardware (i.e. either 433 or 915mhz).
    :param bytes sync_word: A byte string up to 8 bytes long which represents the syncronization
        word used by received and transmitted packets. Read the datasheet for a full understanding
        of this value! However by default the library will set a value that matches the RadioHead
        Arduino library.
    :param int preamble_length: The number of bytes to pre-pend to a data packet as a preamble.
        This is by default 4 to match the RadioHead library.
    :param bytes encryption_key: A 16 byte long string that represents the AES encryption key to use
        when encrypting and decrypting packets.  Both the transmitter and receiver MUST have the
        same key value! By default no encryption key is set or used.
    :param bool high_power: Indicate if the chip is a high power variant that supports boosted
        transmission power.  The default is True as it supports the common RFM69HCW modules sold by
        Adafruit.

    .. note:: The D0/interrupt line is currently unused by this module and can remain unconnected.

    Remember this library makes a best effort at receiving packets with pure Python code.  Trying
    to receive packets too quickly will result in lost data so limit yourself to simple scenarios
    of sending and receiving single packets at a time.

    Also note this library tries to be compatible with raw RadioHead Arduino library communication.
    This means the library sets up the radio modulation to match RadioHead's default of GFSK
    encoding, 250kbit/s bitrate, and 250khz frequency deviation. To change this requires explicitly
    setting the radio's bitrate and encoding register bits. Read the datasheet and study the init
    function to see an example of this--advanced users only! Advanced RadioHead features like
    address/node specific packets or "reliable datagram" delivery are supported however due to the
    limitations noted, "reliable datagram" is still subject to missed packets but with it, the
    sender is notified if a packe has potentially been missed.
    """

    # Global buffer for SPI commands.
    _BUFFER = bytearray(4)

    class _RegisterBits:
        # Class to simplify access to the many configuration bits avaialable
        # on the chip's registers.  This is a subclass here instead of using
        # a higher level module to increase the efficiency of memory usage
        # (all of the instances of this bit class will share the same buffer
        # used by the parent RFM69 class instance vs. each having their own
        # buffer and taking too much memory).

        # Quirk of pylint that it requires public methods for a class.  This
        # is a decorator class in Python and by design it has no public methods.
        # Instead it uses dunder accessors like get and set below.  For some
        # reason pylint can't figure this out so disable the check.
        # pylint: disable=too-few-public-methods

        # Again pylint fails to see the true intent of this code and warns
        # against private access by calling the write and read functions below.
        # This is by design as this is an internally used class.  Disable the
        # check from pylint.
        # pylint: disable=protected-access

        def __init__(self, address, *, offset=0, bits=1):
            assert 0 <= offset <= 7
            assert 1 <= bits <= 8
            assert (offset + bits) <= 8
            self._address = address
            self._mask = 0
            for _ in range(bits):
                self._mask <<= 1
                self._mask |= 1
            self._mask <<= offset
            self._offset = offset

        def __get__(self, obj, objtype):
            reg_value = obj._read_u8(self._address)
            return (reg_value & self._mask) >> self._offset

        def __set__(self, obj, val):
            reg_value = obj._read_u8(self._address)
            reg_value &= ~self._mask
            reg_value |= (val & 0xFF) << self._offset
            obj._write_u8(self._address, reg_value)

    # Control bits from the registers of the chip:
    data_mode = _RegisterBits(_REG_DATA_MOD, offset=5, bits=2)
    modulation_type = _RegisterBits(_REG_DATA_MOD, offset=3, bits=2)
    modulation_shaping = _RegisterBits(_REG_DATA_MOD, offset=0, bits=2)
    temp_start = _RegisterBits(_REG_TEMP1, offset=3)
    temp_running = _RegisterBits(_REG_TEMP1, offset=2)
    sync_on = _RegisterBits(_REG_SYNC_CONFIG, offset=7)
    sync_size = _RegisterBits(_REG_SYNC_CONFIG, offset=3, bits=3)
    aes_on = _RegisterBits(_REG_PACKET_CONFIG2, offset=0)
    pa_0_on = _RegisterBits(_REG_PA_LEVEL, offset=7)
    pa_1_on = _RegisterBits(_REG_PA_LEVEL, offset=6)
    pa_2_on = _RegisterBits(_REG_PA_LEVEL, offset=5)
    output_power = _RegisterBits(_REG_PA_LEVEL, offset=0, bits=5)
    rx_bw_dcc_freq = _RegisterBits(_REG_RX_BW, offset=5, bits=3)
    rx_bw_mantissa = _RegisterBits(_REG_RX_BW, offset=3, bits=2)
    rx_bw_exponent = _RegisterBits(_REG_RX_BW, offset=0, bits=3)
    afc_bw_dcc_freq = _RegisterBits(_REG_AFC_BW, offset=5, bits=3)
    afc_bw_mantissa = _RegisterBits(_REG_AFC_BW, offset=3, bits=2)
    afc_bw_exponent = _RegisterBits(_REG_AFC_BW, offset=0, bits=3)
    packet_format = _RegisterBits(_REG_PACKET_CONFIG1, offset=7, bits=1)
    dc_free = _RegisterBits(_REG_PACKET_CONFIG1, offset=5, bits=2)
    crc_on = _RegisterBits(_REG_PACKET_CONFIG1, offset=4, bits=1)
    crc_auto_clear_off = _RegisterBits(_REG_PACKET_CONFIG1, offset=3, bits=1)
    address_filter = _RegisterBits(_REG_PACKET_CONFIG1, offset=1, bits=2)
    mode_ready = _RegisterBits(_REG_IRQ_FLAGS1, offset=7)
    dio_0_mapping = _RegisterBits(_REG_DIO_MAPPING1, offset=6, bits=2)

    # pylint: disable=too-many-statements
    def __init__(
        self,
        spi,
        cs,
        reset,
        frequency,
        *,
        sync_word=b"\x2D\xD4",
        preamble_length=4,
        encryption_key=None,
        high_power=True,
        baudrate=2000000
    ):
        self._tx_power = 13
        self.high_power = high_power
        # Device support SPI mode 0 (polarity & phase = 0) up to a max of 10mhz.
        self._device = spidev.SPIDevice(spi, cs, baudrate=baudrate, polarity=0, phase=0)
        # Setup reset as a digital output that's low.
        self._reset = reset
        self._reset.switch_to_output(value=False)
        self.reset()  # Reset the chip.
        # Check the version of the chip.
        version = self._read_u8(_REG_VERSION)
        if version != 0x24:
            raise RuntimeError(
                "Failed to find RFM69 with expected version, check wiring!"
            )
        self.idle()  # Enter idle state.
        # Setup the chip in a similar way to the RadioHead RFM69 library.
        # Set FIFO TX condition to not empty and the default FIFO threshold to 15.
        self._write_u8(_REG_FIFO_THRESH, 0b10001111)
        # Configure low beta off.
        self._write_u8(_REG_TEST_DAGC, 0x30)
        # Disable boost.
        self._write_u8(_REG_TEST_PA1, _TEST_PA1_NORMAL)
        self._write_u8(_REG_TEST_PA2, _TEST_PA2_NORMAL)
        # Set the syncronization word.
        self.sync_word = sync_word
        self.preamble_length = preamble_length  # Set the preamble length.
        self.frequency_mhz = frequency  # Set frequency.
        self.encryption_key = encryption_key  # Set encryption key.
        # Configure modulation for RadioHead library GFSK_Rb250Fd250 mode
        # by default.  Users with advanced knowledge can manually reconfigure
        # for any other mode (consulting the datasheet is absolutely
        # necessary!).
        self.modulation_shaping = 0b01  # Gaussian filter, BT=1.0
        self.bitrate = 250000  # 250kbs
        self.frequency_deviation = 250000  # 250khz
        self.rx_bw_dcc_freq = 0b111  # RxBw register = 0xE0
        self.rx_bw_mantissa = 0b00
        self.rx_bw_exponent = 0b000
        self.afc_bw_dcc_freq = 0b111  # AfcBw register = 0xE0
        self.afc_bw_mantissa = 0b00
        self.afc_bw_exponent = 0b000
        self.packet_format = 1  # Variable length.
        self.dc_free = 0b10  # Whitening
        # Set transmit power to 13 dBm, a safe value any module supports.
        self.tx_power = 13

        # initialize last RSSI reading
        self.last_rssi = 0.0
        """The RSSI of the last received packet. Stored when the packet was received.
           This instantaneous RSSI value may not be accurate once the
           operating mode has been changed.
        """
        # initialize timeouts and delays delays
        self.ack_wait = 0.5
        """The delay time before attempting a retry after not receiving an ACK"""
        self.receive_timeout = 0.5
        """The amount of time to poll for a received packet.
           If no packet is received, the returned packet will be None
        """
        self.xmit_timeout = 2.0
        """The amount of time to wait for the HW to transmit the packet.
           This is mainly used to prevent a hang due to a HW issue
        """
        self.ack_retries = 5
        """The number of ACK retries before reporting a failure."""
        self.ack_delay = None
        """The delay time before attemting to send an ACK.
           If ACKs are being missed try setting this to .1 or .2.
        """
        # initialize sequence number counter for reliabe datagram mode
        self.sequence_number = 0
        # create seen Ids list
        self.seen_ids = bytearray(256)
        # initialize packet header
        # node address - default is broadcast
        self.node = _RH_BROADCAST_ADDRESS
        """The default address of this Node. (0-255).
           If not 255 (0xff) then only packets address to this node will be accepted.
           First byte of the RadioHead header.
        """
        # destination address - default is broadcast
        self.destination = _RH_BROADCAST_ADDRESS
        """The default destination address for packet transmissions. (0-255).
           If 255 (0xff) then any receiving node should accept the packet.
           Second byte of the RadioHead header.
        """
        # ID - contains seq count for reliable datagram mode
        self.identifier = 0
        """Automatically set to the sequence number when send_with_ack() used.
           Third byte of the RadioHead header.
        """
        # flags - identifies ack/reetry packet for reliable datagram mode
        self.flags = 0
        """Upper 4 bits reserved for use by Reliable Datagram Mode.
           Lower 4 bits may be used to pass information.
           Fourth byte of the RadioHead header.
        """

    # pylint: enable=too-many-statements

    # pylint: disable=no-member
    # Reconsider this disable when it can be tested.
    def _read_into(self, address, buf, length=None):
        # Read a number of bytes from the specified address into the provided
        # buffer.  If length is not specified (the default) the entire buffer
        # will be filled.
        if length is None:
            length = len(buf)
        with self._device as device:
            self._BUFFER[0] = address & 0x7F  # Strip out top bit to set 0
            # value (read).
            device.write(self._BUFFER, end=1)
            device.readinto(buf, end=length)

    def _read_u8(self, address):
        # Read a single byte from the provided address and return it.
        self._read_into(address, self._BUFFER, length=1)
        return self._BUFFER[0]

    def _write_from(self, address, buf, length=None):
        # Write a number of bytes to the provided address and taken from the
        # provided buffer.  If no length is specified (the default) the entire
        # buffer is written.
        if length is None:
            length = len(buf)
        with self._device as device:
            self._BUFFER[0] = (address | 0x80) & 0xFF  # Set top bit to 1 to
            # indicate a write.
            device.write(self._BUFFER, end=1)
            device.write(buf, end=length)  # send data

    def _write_u8(self, address, val):
        # Write a byte register to the chip.  Specify the 7-bit address and the
        # 8-bit value to write to that address.
        with self._device as device:
            self._BUFFER[0] = (address | 0x80) & 0xFF  # Set top bit to 1 to
            # indicate a write.
            self._BUFFER[1] = val & 0xFF
            device.write(self._BUFFER, end=2)

    def reset(self):
        """Perform a reset of the chip."""
        # See section 7.2.2 of the datasheet for reset description.
        self._reset.value = True
        time.sleep(0.0001)  # 100 us
        self._reset.value = False
        time.sleep(0.005)  # 5 ms

    def idle(self):
        """Enter idle standby mode (switching off high power amplifiers if necessary)."""
        # Like RadioHead library, turn off high power boost if enabled.
        if self._tx_power >= 18:
            self._write_u8(_REG_TEST_PA1, _TEST_PA1_NORMAL)
            self._write_u8(_REG_TEST_PA2, _TEST_PA2_NORMAL)
        self.operation_mode = STANDBY_MODE

    def sleep(self):
        """Enter sleep mode."""
        self.operation_mode = SLEEP_MODE

    def listen(self):
        """Listen for packets to be received by the chip.  Use :py:func:`receive` to listen, wait
        and retrieve packets as they're available.
        """
        # Like RadioHead library, turn off high power boost if enabled.
        if self._tx_power >= 18:
            self._write_u8(_REG_TEST_PA1, _TEST_PA1_NORMAL)
            self._write_u8(_REG_TEST_PA2, _TEST_PA2_NORMAL)
        # Enable payload ready interrupt for D0 line.
        self.dio_0_mapping = 0b01
        # Enter RX mode (will clear FIFO!).
        self.operation_mode = RX_MODE

    def transmit(self):
        """Transmit a packet which is queued in the FIFO.  This is a low level function for
        entering transmit mode and more.  For generating and transmitting a packet of data use
        :py:func:`send` instead.
        """
        # Like RadioHead library, turn on high power boost if enabled.
        if self._tx_power >= 18:
            self._write_u8(_REG_TEST_PA1, _TEST_PA1_BOOST)
            self._write_u8(_REG_TEST_PA2, _TEST_PA2_BOOST)
        # Enable packet sent interrupt for D0 line.
        self.dio_0_mapping = 0b00
        # Enter TX mode (will clear FIFO!).
        self.operation_mode = TX_MODE

    @property
    def temperature(self):
        """The internal temperature of the chip in degrees Celsius. Be warned this is not
        calibrated or very accurate.

        .. warning:: Reading this will STOP any receiving/sending that might be happening!
        """
        # Start a measurement then poll the measurement finished bit.
        self.temp_start = 1
        while self.temp_running > 0:
            pass
        # Grab the temperature value and convert it to Celsius.
        # This uses the same observed value formula from the Radiohead library.
        temp = self._read_u8(_REG_TEMP2)
        return 166.0 - temp

    @property
    def operation_mode(self):
        """The operation mode value.  Unless you're manually controlling the chip you shouldn't
        change the operation_mode with this property as other side-effects are required for
        changing logical modes--use :py:func:`idle`, :py:func:`sleep`, :py:func:`transmit`,
        :py:func:`listen` instead to signal intent for explicit logical modes.
        """
        op_mode = self._read_u8(_REG_OP_MODE)
        return (op_mode >> 2) & 0b111

    @operation_mode.setter
    def operation_mode(self, val):
        assert 0 <= val <= 4
        # Set the mode bits inside the operation mode register.
        op_mode = self._read_u8(_REG_OP_MODE)
        op_mode &= 0b11100011
        op_mode |= val << 2
        self._write_u8(_REG_OP_MODE, op_mode)
        # Wait for mode to change by polling interrupt bit.
        start = time.monotonic()
        while not self.mode_ready:
            if (time.monotonic() - start) >= 1:
                raise TimeoutError("Operation Mode failed to set.")

    @property
    def sync_word(self):
        """The synchronization word value.  This is a byte string up to 8 bytes long (64 bits)
        which indicates the synchronization word for transmitted and received packets. Any
        received packet which does not include this sync word will be ignored. The default value
        is 0x2D, 0xD4 which matches the RadioHead RFM69 library. Setting a value of None will
        disable synchronization word matching entirely.
        """
        # Handle when sync word is disabled..
        if not self.sync_on:
            return None
        # Sync word is not disabled so read the current value.
        sync_word_length = self.sync_size + 1  # Sync word size is offset by 1
        # according to datasheet.
        sync_word = bytearray(sync_word_length)
        self._read_into(_REG_SYNC_VALUE1, sync_word)
        return sync_word

    @sync_word.setter
    def sync_word(self, val):
        # Handle disabling sync word when None value is set.
        if val is None:
            self.sync_on = 0
        else:
            # Check sync word is at most 8 bytes.
            assert 1 <= len(val) <= 8
            # Update the value, size and turn on the sync word.
            self._write_from(_REG_SYNC_VALUE1, val)
            self.sync_size = len(val) - 1  # Again sync word size is offset by
            # 1 according to datasheet.
            self.sync_on = 1

    @property
    def preamble_length(self):
        """The length of the preamble for sent and received packets, an unsigned 16-bit value.
        Received packets must match this length or they are ignored! Set to 4 to match the
        RadioHead RFM69 library.
        """
        msb = self._read_u8(_REG_PREAMBLE_MSB)
        lsb = self._read_u8(_REG_PREAMBLE_LSB)
        return ((msb << 8) | lsb) & 0xFFFF

    @preamble_length.setter
    def preamble_length(self, val):
        assert 0 <= val <= 65535
        self._write_u8(_REG_PREAMBLE_MSB, (val >> 8) & 0xFF)
        self._write_u8(_REG_PREAMBLE_LSB, val & 0xFF)

    @property
    def frequency_mhz(self):
        """The frequency of the radio in Megahertz. Only the allowed values for your radio must be
        specified (i.e. 433 vs. 915 mhz)!
        """
        # FRF register is computed from the frequency following the datasheet.
        # See section 6.2 and FRF register description.
        # Read bytes of FRF register and assemble into a 24-bit unsigned value.
        msb = self._read_u8(_REG_FRF_MSB)
        mid = self._read_u8(_REG_FRF_MID)
        lsb = self._read_u8(_REG_FRF_LSB)
        frf = ((msb << 16) | (mid << 8) | lsb) & 0xFFFFFF
        frequency = (frf * _FSTEP) / 1000000.0
        return frequency

    @frequency_mhz.setter
    def frequency_mhz(self, val):
        assert 290 <= val <= 1020
        # Calculate FRF register 24-bit value using section 6.2 of the datasheet.
        frf = int((val * 1000000.0) / _FSTEP) & 0xFFFFFF
        # Extract byte values and update registers.
        msb = frf >> 16
        mid = (frf >> 8) & 0xFF
        lsb = frf & 0xFF
        self._write_u8(_REG_FRF_MSB, msb)
        self._write_u8(_REG_FRF_MID, mid)
        self._write_u8(_REG_FRF_LSB, lsb)

    @property
    def encryption_key(self):
        """The AES encryption key used to encrypt and decrypt packets by the chip. This can be set
        to None to disable encryption (the default), otherwise it must be a 16 byte long byte
        string which defines the key (both the transmitter and receiver must use the same key
        value).
        """
        # Handle if encryption is disabled.
        if self.aes_on == 0:
            return None
        # Encryption is enabled so read the key and return it.
        key = bytearray(16)
        self._read_into(_REG_AES_KEY1, key)
        return key

    @encryption_key.setter
    def encryption_key(self, val):
        # Handle if unsetting the encryption key (None value).
        if val is None:
            self.aes_on = 0
        else:
            # Set the encryption key and enable encryption.
            assert len(val) == 16
            self._write_from(_REG_AES_KEY1, val)
            self.aes_on = 1

    @property
    def tx_power(self):
        """The transmit power in dBm. Can be set to a value from -2 to 20 for high power devices
        (RFM69HCW, high_power=True) or -18 to 13 for low power devices. Only integer power
        levels are actually set (i.e. 12.5 will result in a value of 12 dBm).
        """
        # Follow table 10 truth table from the datasheet for determining power
        # level from the individual PA level bits and output power register.
        pa0 = self.pa_0_on
        pa1 = self.pa_1_on
        pa2 = self.pa_2_on
        if pa0 and not pa1 and not pa2:
            # -18 to 13 dBm range
            return -18 + self.output_power
        if not pa0 and pa1 and not pa2:
            # -2 to 13 dBm range
            return -18 + self.output_power
        if not pa0 and pa1 and pa2 and not self.high_power:
            # 2 to 17 dBm range
            return -14 + self.output_power
        if not pa0 and pa1 and pa2 and self.high_power:
            # 5 to 20 dBm range
            return -11 + self.output_power
        raise RuntimeError("Power amplifiers in unknown state!")

    @tx_power.setter
    def tx_power(self, val):
        val = int(val)
        # Determine power amplifier and output power values depending on
        # high power state and requested power.
        pa_0_on = 0
        pa_1_on = 0
        pa_2_on = 0
        output_power = 0
        if self.high_power:
            # Handle high power mode.
            assert -2 <= val <= 20
            if val <= 13:
                pa_1_on = 1
                output_power = val + 18
            elif 13 < val <= 17:
                pa_1_on = 1
                pa_2_on = 1
                output_power = val + 14
            else:  # power >= 18 dBm
                # Note this also needs PA boost enabled separately!
                pa_1_on = 1
                pa_2_on = 1
                output_power = val + 11
        else:
            # Handle non-high power mode.
            assert -18 <= val <= 13
            # Enable only power amplifier 0 and set output power.
            pa_0_on = 1
            output_power = val + 18
        # Set power amplifiers and output power as computed above.
        self.pa_0_on = pa_0_on
        self.pa_1_on = pa_1_on
        self.pa_2_on = pa_2_on
        self.output_power = output_power
        self._tx_power = val

    @property
    def rssi(self):
        """The received strength indicator (in dBm).
        May be inaccuate if not read immediatey. last_rssi contains the value read immediately
        receipt of the last packet.
        """
        # Read RSSI register and convert to value using formula in datasheet.
        return -self._read_u8(_REG_RSSI_VALUE) / 2.0

    @property
    def bitrate(self):
        """The modulation bitrate in bits/second (or chip rate if Manchester encoding is enabled).
        Can be a value from ~489 to 32mbit/s, but see the datasheet for the exact supported
        values.
        """
        msb = self._read_u8(_REG_BITRATE_MSB)
        lsb = self._read_u8(_REG_BITRATE_LSB)
        return _FXOSC / ((msb << 8) | lsb)

    @bitrate.setter
    def bitrate(self, val):
        assert (_FXOSC / 65535) <= val <= 32000000.0
        # Round up to the next closest bit-rate value with addition of 0.5.
        bitrate = int((_FXOSC / val) + 0.5) & 0xFFFF
        self._write_u8(_REG_BITRATE_MSB, bitrate >> 8)
        self._write_u8(_REG_BITRATE_LSB, bitrate & 0xFF)

    @property
    def frequency_deviation(self):
        """The frequency deviation in Hertz."""
        msb = self._read_u8(_REG_FDEV_MSB)
        lsb = self._read_u8(_REG_FDEV_LSB)
        return _FSTEP * ((msb << 8) | lsb)

    @frequency_deviation.setter
    def frequency_deviation(self, val):
        assert 0 <= val <= (_FSTEP * 16383)  # fdev is a 14-bit unsigned value
        # Round up to the next closest integer value with addition of 0.5.
        fdev = int((val / _FSTEP) + 0.5) & 0x3FFF
        self._write_u8(_REG_FDEV_MSB, fdev >> 8)
        self._write_u8(_REG_FDEV_LSB, fdev & 0xFF)

    def packet_sent(self):
        """Transmit status"""
        return (self._read_u8(_REG_IRQ_FLAGS2) & 0x8) >> 3

    def payload_ready(self):
        """Receive status"""
        return (self._read_u8(_REG_IRQ_FLAGS2) & 0x4) >> 2

    def send(
        self,
        data,
        *,
        keep_listening=False,
        destination=None,
        node=None,
        identifier=None,
        flags=None
    ):
        """Send a string of data using the transmitter.
        You can only send 60 bytes at a time
        (limited by chip's FIFO size and appended headers).
        This appends a 4 byte header to be compatible with the RadioHead library.
        The header defaults to using the initialized attributes:
        (destination,node,identifier,flags)
        It may be temporarily overidden via the kwargs - destination,node,identifier,flags.
        Values passed via kwargs do not alter the attribute settings.
        The keep_listening argument should be set to True if you want to start listening
        automatically after the packet is sent. The default setting is False.

        Returns: True if success or False if the send timed out.
        """
        # Disable pylint warning to not use length as a check for zero.
        # This is a puzzling warning as the below code is clearly the most
        # efficient and proper way to ensure a precondition that the provided
        # buffer be within an expected range of bounds.  Disable this check.
        # pylint: disable=len-as-condition
        assert 0 < len(data) <= 60
        # pylint: enable=len-as-condition
        self.idle()  # Stop receiving to clear FIFO and keep it clear.
        # Fill the FIFO with a packet to send.
        # Combine header and data to form payload
        payload = bytearray(5)
        payload[0] = 4 + len(data)
        if destination is None:  # use attribute
            payload[1] = self.destination
        else:  # use kwarg
            payload[1] = destination
        if node is None:  # use attribute
            payload[2] = self.node
        else:  # use kwarg
            payload[2] = node
        if identifier is None:  # use attribute
            payload[3] = self.identifier
        else:  # use kwarg
            payload[3] = identifier
        if flags is None:  # use attribute
            payload[4] = self.flags
        else:  # use kwarg
            payload[4] = flags
        payload = payload + data
        # Write payload to transmit fifo
        self._write_from(_REG_FIFO, payload)
        # Turn on transmit mode to send out the packet.
        self.transmit()
        # Wait for packet sent interrupt with explicit polling (not ideal but
        # best that can be done right now without interrupts).
        start = time.monotonic()
        timed_out = False
        while not timed_out and not self.packet_sent():
            if (time.monotonic() - start) >= self.xmit_timeout:
                timed_out = True
        # Listen again if requested.
        if keep_listening:
            self.listen()
        else:  # Enter idle mode to stop receiving other packets.
            self.idle()
        return not timed_out

    def send_with_ack(self, data):
        """Reliable Datagram mode:
        Send a packet with data and wait for an ACK response.
        The packet header is automatically generated.
        If enabled, the packet transmission will be retried on failure
        """
        if self.ack_retries:
            retries_remaining = self.ack_retries
        else:
            retries_remaining = 1
        got_ack = False
        self.sequence_number = (self.sequence_number + 1) & 0xFF
        while not got_ack and retries_remaining:
            self.identifier = self.sequence_number
            self.send(data, keep_listening=True)
            # Don't look for ACK from Broadcast message
            if self.destination == _RH_BROADCAST_ADDRESS:
                got_ack = True
            else:
                # wait for a packet from our destination
                ack_packet = self.receive(timeout=self.ack_wait, with_header=True)
                if ack_packet is not None:
                    if ack_packet[3] & _RH_FLAGS_ACK:
                        # check the ID
                        if ack_packet[2] == self.identifier:
                            got_ack = True
                            break
            # pause before next retry -- random delay
            if not got_ack:
                # delay by random amount before next try
                time.sleep(self.ack_wait + self.ack_wait * random.random())
            retries_remaining = retries_remaining - 1
            # set retry flag in packet header
            self.flags |= _RH_FLAGS_RETRY
        self.flags = 0  # clear flags
        return got_ack

    # pylint: disable=too-many-branches
    def receive(
        self, *, keep_listening=True, with_ack=False, timeout=None, with_header=False
    ):
        """Wait to receive a packet from the receiver. If a packet is found the payload bytes
        are returned, otherwise None is returned (which indicates the timeout elapsed with no
        reception).
        If keep_listening is True (the default) the chip will immediately enter listening mode
        after reception of a packet, otherwise it will fall back to idle mode and ignore any
        future reception.
        All packets must have a 4 byte header for compatibilty with the
        RadioHead library.
        The header consists of 4 bytes (To,From,ID,Flags). The default setting will  strip
        the header before returning the packet to the caller.
        If with_header is True then the 4 byte header will be returned with the packet.
        The payload then begins at packet[4].
        If with_ack is True, send an ACK after receipt (Reliable Datagram mode)
        """
        timed_out = False
        if timeout is None:
            timeout = self.receive_timeout
        if timeout is not None:
            # Wait for the payload_ready signal.  This is not ideal and will
            # surely miss or overflow the FIFO when packets aren't read fast
            # enough, however it's the best that can be done from Python without
            # interrupt supports.
            # Make sure we are listening for packets.
            self.listen()
            start = time.monotonic()
            timed_out = False
            while not timed_out and not self.payload_ready():
                if (time.monotonic() - start) >= timeout:
                    timed_out = True
        # Payload ready is set, a packet is in the FIFO.
        packet = None
        # save last RSSI reading
        self.last_rssi = self.rssi
        # Enter idle mode to stop receiving other packets.
        self.idle()
        if not timed_out:
            # Read the length of the FIFO.
            fifo_length = self._read_u8(_REG_FIFO)
            # Handle if the received packet is too small to include the 4 byte
            # RadioHead header and at least one byte of data --reject this packet and ignore it.
            if fifo_length > 0:  # read and clear the FIFO if anything in it
                packet = bytearray(fifo_length)
                self._read_into(_REG_FIFO, packet, fifo_length)

            if fifo_length < 5:
                packet = None
            else:
                if (
                    self.node != _RH_BROADCAST_ADDRESS
                    and packet[0] != _RH_BROADCAST_ADDRESS
                    and packet[0] != self.node
                ):
                    packet = None
                # send ACK unless this was an ACK or a broadcast
                elif (
                    with_ack
                    and ((packet[3] & _RH_FLAGS_ACK) == 0)
                    and (packet[0] != _RH_BROADCAST_ADDRESS)
                ):
                    # delay before sending Ack to give receiver a chance to get ready
                    if self.ack_delay is not None:
                        time.sleep(self.ack_delay)
                    # send ACK packet to sender (data is b'!')
                    self.send(
                        b"!",
                        destination=packet[1],
                        node=packet[0],
                        identifier=packet[2],
                        flags=(packet[3] | _RH_FLAGS_ACK),
                    )
                    # reject Retries if we have seen this idetifier from this source before
                    if (self.seen_ids[packet[1]] == packet[2]) and (
                        packet[3] & _RH_FLAGS_RETRY
                    ):
                        packet = None
                    else:  # save the packet identifier for this source
                        self.seen_ids[packet[1]] = packet[2]
                if (
                    not with_header and packet is not None
                ):  # skip the header if not wanted
                    packet = packet[4:]
        # Listen again if necessary and return the result packet.
        if keep_listening:
            self.listen()
        else:
            # Enter idle mode to stop receiving other packets.
            self.idle()
        return packet
