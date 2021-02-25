# The MIT License (MIT)
#
# Copyright (c) 2020 Dan Halbert for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""

`adafruit_ble_ibbq`
================================================================================

BLE iBBQ Multiple Probe Thermometers

* Author(s): Dan Halbert for Adafruit Industries

Implementation Notes
--------------------

iBBQ protocol information is from https://gist.github.com/uucidl/b9c60b6d36d8080d085a8e3310621d64.

**Hardware:**

InkBird and EasyBBQ (from PyleUSA) are brands that use the iBBQ protocol in their products.
"""

import struct

import _bleio
from adafruit_ble.attributes import Attribute
from adafruit_ble.services import Service
from adafruit_ble.uuid import StandardUUID
from adafruit_ble.characteristics import Characteristic, ComplexCharacteristic

__version__ = "1.2.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_iBBQ.git"


class _SettingsResult(ComplexCharacteristic):
    """Notify-only characteristic of results from SettingsData messages"""

    uuid = StandardUUID(0xFFF1)

    def __init__(self):
        super().__init__(properties=Characteristic.NOTIFY)

    def bind(self, service):
        """Bind to an IBBQService."""
        bound_characteristic = super().bind(service)
        bound_characteristic.set_cccd(notify=True)
        # Use a PacketBuffer that can store one packet to receive the data.
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=1)


class _RealtimeData(ComplexCharacteristic):
    """Notify-only characteristic of results from temperature probes"""

    uuid = StandardUUID(0xFFF4)

    def __init__(self):
        super().__init__(properties=Characteristic.NOTIFY)

    def bind(self, service):
        """Bind to an IBBQService."""
        bound_characteristic = super().bind(service)
        bound_characteristic.set_cccd(notify=True)
        # Use a PacketBuffer that can store one packet to receive the data.
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=1)


class IBBQService(Service):
    """Service for reading from an iBBQ thermometer.
    """

    _CREDENTIALS_MSG = b"\x21\x07\x06\x05\x04\x03\x02\x01\xb8\x22\x00\x00\x00\x00\x00"
    _REALTIME_DATA_ENABLE_MSG = b"\x0B\x01\x00\x00\x00\x00"
    _UNITS_FAHRENHEIT_MSG = b"\x02\x01\x00\x00\x00\x00"
    _UNITS_CELSIUS_MSG = b"\x02\x00\x00\x00\x00\x00"
    _REQUEST_BATTERY_LEVEL_MSG = b"\x08\x24\x00\x00\x00\x00"

    def __init__(self, service=None):
        super().__init__(service=service)
        # Defer creating buffers until needed, since MTU is not known yet.
        self._settings_result_buf = None
        self._realtime_data_buf = None

    uuid = StandardUUID(0xFFF0)

    settings_result = _SettingsResult()

    account_and_verify = Characteristic(
        uuid=StandardUUID(0xFFF2),
        properties=Characteristic.WRITE,
        read_perm=Attribute.NO_ACCESS,
    )
    """Send credentials to this characteristic."""

    # Not yet understood, not clear if available.
    # history_data = Characteristic(uuid=StandardUUID(0xFFF3),
    #                               properties=Characteristic.NOTIFY,
    #                               write_perm=Attribute.NO_ACCESS)

    realtime_data = _RealtimeData()
    """Real-time temperature values."""

    settings_data = Characteristic(
        uuid=StandardUUID(0xFFF5),
        properties=Characteristic.WRITE,
        read_perm=Attribute.NO_ACCESS,
    )
    """Send control messages here."""

    def init(self):
        """Perform initial "pairing", which is not regular BLE pairing."""
        self.account_and_verify = self._CREDENTIALS_MSG
        self.settings_data = self._REALTIME_DATA_ENABLE_MSG

    def display_fahrenheit(self):
        """Display temperatures on device in degrees Fahrenheit.

        Note: This does not change the units returned by `temperatures`.
        """
        self.settings_data = self._UNITS_FAHRENHEIT_MSG

    def display_celsius(self):
        """Display temperatures on device in degrees Celsius.

        Note: This does not change the units returned by `temperatures`.
        """
        self.settings_data = self._UNITS_CELSIUS_MSG

    @property
    def temperatures(self):
        """Return a tuple of temperatures for all the possible temperature probes on the device.
        Temperatures are in degrees Celsius. Unconnected probes return 0.0.
        """
        if self._realtime_data_buf is None:
            self._realtime_data_buf = bytearray(
                self.realtime_data.packet_size  # pylint: disable=no-member
            )
        data = self._realtime_data_buf
        length = self.realtime_data.readinto(data)  # pylint: disable=no-member
        if length > 0:
            return tuple(
                struct.unpack_from("<H", data, offset=offset)[0] / 10
                for offset in range(0, length, 2)
            )
        # No data.
        return None

    @property
    def battery_level(self):
        """Get current battery level in volts as ``(current_voltage, max_voltage)``.
        Results are approximate and may differ from the
        actual battery voltage by 0.1v or so.
        """
        if self._settings_result_buf is None:
            self._settings_result_buf = bytearray(
                self.settings_result.packet_size  # pylint: disable=no-member
            )

        self.settings_data = self._REQUEST_BATTERY_LEVEL_MSG
        results = self._settings_result_buf
        length = self.settings_result.readinto(results)  # pylint: disable=no-member
        if length >= 5:
            header, current_voltage, max_voltage = struct.unpack_from("<BHH", results)
            if header == 0x24:
                # Calibration was determined empirically, by comparing
                # the returned values with actual measurements of battery voltage,
                # on one sample each of two different products.
                return (
                    current_voltage / 2000 - 0.3,
                    (6550 if max_voltage == 0 else max_voltage) / 2000,
                )
        # Unexpected response or no data.
        return None
