# SPDX-FileCopyrightText: 2020 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_broadcastnet`
================================================================================

Basic IOT over BLE advertisements.


* Author(s): Scott Shawcroft
"""

import struct
import os
import time
from micropython import const
import adafruit_ble
from adafruit_ble.advertising import Advertisement, LazyObjectField
from adafruit_ble.advertising.standard import ManufacturerData, ManufacturerDataField

__version__ = "0.10.4"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_BroadcastNet.git"

_ble = adafruit_ble.BLERadio()  # pylint: disable=invalid-name
_sequence_number = 0  # pylint: disable=invalid-name


def broadcast(measurement, *, broadcast_time=0.1, extended=False):
    """Broadcasts the given measurement for the given broadcast time. If extended is False and the
    measurement would be too long, it will be split into multiple measurements for transmission.
    """
    global _sequence_number  # pylint: disable=global-statement,invalid-name
    for submeasurement in measurement.split(252 if extended else 31):
        submeasurement.sequence_number = _sequence_number
        _ble.start_advertising(submeasurement, scan_response=None)
        time.sleep(broadcast_time)
        _ble.stop_advertising()
        _sequence_number = (_sequence_number + 1) % 256


# This line causes issues with Sphinx, so we won't run it in the CI
if not hasattr(os, "environ") or (
    "GITHUB_ACTION" not in os.environ and "READTHEDOCS" not in os.environ
):
    if _ble._adapter.address:  # pylint: disable=protected-access
        device_address = "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(  # pylint: disable=invalid-name
            *reversed(
                list(
                    _ble._adapter.address.address_bytes  # pylint: disable=protected-access
                )
            )
        )
    else:
        device_address = "000000000000"  # pylint: disable=invalid-name
        """Device address as a string."""

_MANUFACTURING_DATA_ADT = const(0xFF)
_ADAFRUIT_COMPANY_ID = const(0x0822)


class AdafruitSensorMeasurement(Advertisement):
    """A collection of sensor measurements."""

    # This prefix matches all
    match_prefixes = (
        # Matches the sequence number field header (length+ID)
        struct.pack(
            "<BHBH", _MANUFACTURING_DATA_ADT, _ADAFRUIT_COMPANY_ID, 0x03, 0x0003
        ),
    )

    manufacturer_data = LazyObjectField(
        ManufacturerData,
        "manufacturer_data",
        advertising_data_type=_MANUFACTURING_DATA_ADT,
        company_id=_ADAFRUIT_COMPANY_ID,
        key_encoding="<H",
    )

    sequence_number = ManufacturerDataField(0x0003, "<B")
    """Sequence number of the measurement. Used to detect missed packets."""

    acceleration = ManufacturerDataField(0x0A00, "<fff", ("x", "y", "z"))
    """Acceleration as (x, y, z) tuple of floats in meters per second per second."""

    magnetic = ManufacturerDataField(0x0A01, "<fff", ("x", "y", "z"))
    """Magnetism as (x, y, z) tuple of floats in micro-Tesla."""

    orientation = ManufacturerDataField(0x0A02, "<fff", ("x", "y", "z"))
    """Absolution orientation as (x, y, z) tuple of floats in degrees."""

    gyro = ManufacturerDataField(0x0A03, "<fff", ("x", "y", "z"))
    """Gyro motion as (x, y, z) tuple of floats in radians per second."""

    temperature = ManufacturerDataField(0x0A04, "<f")
    """Temperature as a float in degrees centigrade."""

    eCO2 = ManufacturerDataField(0x0A05, "<f")
    """Equivalent CO2 as a float in parts per million."""

    TVOC = ManufacturerDataField(0x0A06, "<f")
    """Total Volatile Organic Compounds as a float in parts per billion."""

    distance = ManufacturerDataField(0x0A07, "<f")
    """Distance as a float in centimeters."""

    light = ManufacturerDataField(0x0A08, "<f")
    """Brightness as a float without units."""

    lux = ManufacturerDataField(0x0A09, "<f")
    """Brightness as a float in SI lux."""

    pressure = ManufacturerDataField(0x0A0A, "<f")
    """Pressure as a float in hectopascals."""

    relative_humidity = ManufacturerDataField(0x0A0B, "<f")
    """Relative humidity as a float percentage."""

    current = ManufacturerDataField(0x0A0C, "<f")
    """Current as a float in milliamps."""

    voltage = ManufacturerDataField(0x0A0D, "<f")
    """Voltage as a float in Volts."""

    color = ManufacturerDataField(0x0A0E, "<f")
    """Color as RGB integer."""

    # alarm = ManufacturerDataField(0x0a0f, "<f")
    # """Alarm as a start date and time and recurrence period. Not supported."""

    # datetime = ManufacturerDataField(0x0a10, "<f")
    # """Date and time as a struct. Not supported."""

    duty_cycle = ManufacturerDataField(0x0A11, "<f")
    """16-bit PWM duty cycle. Independent of frequency."""

    frequency = ManufacturerDataField(0x0A12, "<f")
    """As integer Hertz"""

    value = ManufacturerDataField(0x0A13, "<f")
    """16-bit unit-less value. Used for analog values and for booleans."""

    weight = ManufacturerDataField(0x0A14, "<f")
    """Weight as a float in grams."""

    battery_voltage = ManufacturerDataField(0x0A15, "<H")
    """Battery voltage in millivolts. Saves two bytes over voltage and is more readable in bare
       packets."""

    def __init__(self, *, sequence_number=None):
        super().__init__()
        if sequence_number:
            self.sequence_number = sequence_number

    def __str__(self):
        parts = []
        for attr in dir(self.__class__):
            attribute_instance = getattr(self.__class__, attr)
            if issubclass(attribute_instance.__class__, ManufacturerDataField):
                value = getattr(self, attr)
                if value is not None:
                    parts.append("{}={}".format(attr, str(value)))
        return "<{} {} >".format(self.__class__.__name__, " ".join(parts))

    def __bytes__(self):
        """The raw packet bytes."""
        # Must reorder the ManufacturerData contents so the sequence number field is always first.
        # Necessary to ensure that match_prefixes works right to reconstruct on the receiver.
        self.data_dict[255].data.move_to_end(3, last=False)
        return super().__bytes__()

    def split(self, max_packet_size=31):
        """Split the measurement into multiple measurements with the given max_packet_size. Yields
        each submeasurement."""
        current_size = 8  # baseline for mfg data and sequence number
        if current_size + len(self.manufacturer_data) < max_packet_size:
            yield self
            return

        original_data = self.manufacturer_data.data
        submeasurement = None
        for key in original_data:
            value = original_data[key]
            entry_size = 2 + len(value)
            if not submeasurement or current_size + entry_size > max_packet_size:
                if submeasurement:
                    yield submeasurement
                submeasurement = self.__class__()
                current_size = 8
            submeasurement.manufacturer_data.data[key] = value
            current_size += entry_size

        if submeasurement:
            yield submeasurement

        return
