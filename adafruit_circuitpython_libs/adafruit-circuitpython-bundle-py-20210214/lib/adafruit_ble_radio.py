# SPDX-FileCopyrightText: 2019 Nicholas H. Tollervey for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_radio`
================================================================================

Simple byte and string based inter-device communication via BLE.


* Author(s): Nicholas H.Tollervey for Adafruit Industries

**Hardware:**

   Adafruit Feather nRF52840 Express <https://www.adafruit.com/product/4062>
   Adafruit Circuit Playground Bluefruit <https://www.adafruit.com/product/4333>

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""
import time
import struct
from micropython import const
from adafruit_ble import BLERadio
from adafruit_ble.advertising import Advertisement, LazyObjectField
from adafruit_ble.advertising.standard import ManufacturerData


__version__ = "0.3.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Radio.git"


#: Maximum length of a message (in bytes).
MAX_LENGTH = 248

#: Amount of time to advertise a message (in seconds).
AD_DURATION = 0.5

_MANUFACTURING_DATA_ADT = const(0xFF)
_ADAFRUIT_COMPANY_ID = const(0x0822)
_RADIO_DATA_ID = const(0x0001)  # TODO: check this isn't already taken.


class _RadioAdvertisement(Advertisement):
    """Broadcast arbitrary bytes as a radio message."""

    match_prefixes = (struct.pack("<BH", 0xFF, _ADAFRUIT_COMPANY_ID),)
    manufacturer_data = LazyObjectField(
        ManufacturerData,
        "manufacturer_data",
        advertising_data_type=_MANUFACTURING_DATA_ADT,
        company_id=_ADAFRUIT_COMPANY_ID,
        key_encoding="<H",
    )

    @classmethod
    def matches(cls, entry):
        """Checks for ID matches"""
        if len(entry.advertisement_bytes) < 6:
            return False
        # Check the key position within the manufacturer data. We already know
        # prefix matches so we don't need to check it twice.
        return (
            struct.unpack_from("<H", entry.advertisement_bytes, 5)[0] == _RADIO_DATA_ID
        )

    @property
    def msg(self):
        """Raw radio data"""
        if _RADIO_DATA_ID not in self.manufacturer_data.data:
            return b""
        return self.manufacturer_data.data[_RADIO_DATA_ID]

    @msg.setter
    def msg(self, value):
        self.manufacturer_data.data[_RADIO_DATA_ID] = value


class Radio:
    """
    Represents a connection through which one can send or receive strings
    and bytes. The radio can be tuned to a specific channel upon initialisation
    or via the `configure` method.
    """

    def __init__(self, **args):
        """
        Takes the same configuration arguments as the `configure` method.
        """
        # For BLE related operations.
        self.ble = BLERadio()
        # The uid for outgoing message. Incremented by one on each send, up to
        # 255 when it's reset to 0.
        self.uid = 0
        # Contains timestamped message metadata to mitigate report of
        # receiving of duplicate messages within AD_DURATION time frame.
        self.msg_pool = set()
        # Handle user related configuration.
        self.configure(**args)

    def configure(self, channel=42):
        """
        Set configuration values for the radio.

        :param int channel: The channel (0-255) the radio is listening /
            broadcasting on.
        """
        if -1 < channel < 256:
            self._channel = channel
        else:
            raise ValueError("Channel must be in range 0-255")

    def send(self, message):
        """
        Send a message string on the channel to which the radio is
        broadcasting.

        :param str message: The message string to broadcast.
        """
        return self.send_bytes(message.encode("utf-8"))

    def send_bytes(self, message):
        """
        Send bytes on the channel to which the radio is broadcasting.

        :param bytes message: The bytes to broadcast.
        """
        # Ensure length of message.
        if len(message) > MAX_LENGTH:
            raise ValueError("Message too long (max length = {})".format(MAX_LENGTH))
        advertisement = _RadioAdvertisement()
        # Concatenate the bytes that make up the advertised message.
        advertisement.msg = struct.pack("<BB", self._channel, self.uid) + message

        self.uid = (self.uid + 1) % 255
        # Advertise (block) for AD_DURATION period of time.
        self.ble.start_advertising(advertisement)
        time.sleep(AD_DURATION)
        self.ble.stop_advertising()

    def receive(self):
        """
        Returns a message received on the channel on which the radio is
        listening.

        :return: A string representation of the received message, or else None.
        """
        msg = self.receive_full()
        if msg:
            return msg[0].decode("utf-8").replace("\x00", "")
        return None

    def receive_full(self):
        """
        Returns a tuple containing three values representing a message received
        on the channel on which the radio is listening. If no message was
        received then `None` is returned.

        The three values in the tuple represent:

        * the bytes received.
        * the RSSI (signal strength: 0 = max, -255 = min).
        * a microsecond timestamp: the value returned by time.monotonic() when
          the message was received.

        :return: A tuple representation of the received message, or else None.
        """
        try:
            for entry in self.ble.start_scan(
                _RadioAdvertisement, minimum_rssi=-255, timeout=1, extended=True
            ):
                # Extract channel and unique message ID bytes.
                chan, uid = struct.unpack("<BB", entry.msg[:2])
                if chan == self._channel:
                    now = time.monotonic()
                    addr = entry.address.address_bytes
                    # Ensure this message isn't a duplicate. Message metadata
                    # is a tuple of (now, chan, uid, addr), to (mostly)
                    # uniquely identify a specific message in a certain time
                    # window.
                    expired_metadata = set()
                    duplicate = False
                    for msg_metadata in self.msg_pool:
                        if msg_metadata[0] < now - AD_DURATION:
                            # Ignore expired entries and mark for removal.
                            expired_metadata.add(msg_metadata)
                        elif (chan, uid, addr) == msg_metadata[1:]:
                            # Ignore matched messages to avoid duplication.
                            duplicate = True
                    # Remove expired entries.
                    self.msg_pool = self.msg_pool - expired_metadata
                    if not duplicate:
                        # Add new message's metadata to the msg_pool and
                        # return it as a result.
                        self.msg_pool.add((now, chan, uid, addr))
                        msg = entry.msg[2:]
                        return (msg, entry.rssi, now)
        finally:
            self.ble.stop_scan()
        return None
