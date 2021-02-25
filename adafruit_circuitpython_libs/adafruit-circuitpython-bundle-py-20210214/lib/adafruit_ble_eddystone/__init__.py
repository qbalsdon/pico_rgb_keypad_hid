# The MIT License (MIT)
#
# Copyright (c) 2020 Scott Shawcroft for Adafruit Industries LLC
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
`adafruit_ble_eddystone`
================================================================================

CircuitPython BLE library for Google's open "physical web" Eddystone.

Documented by Google here: https://github.com/google/eddystone

"""

import struct

from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ServiceList, ServiceData
from adafruit_ble.uuid import StandardUUID

__version__ = "1.0.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Eddystone.git"


class _EddystoneService:
    """Placeholder service. Not implemented."""

    # pylint: disable=too-few-public-methods
    uuid = StandardUUID(0xFEAA)


class _EddystoneFrame(ServiceData):
    """Top level advertising data field that adds the field type to bytearrays set."""

    def __init__(self):
        super().__init__(_EddystoneService)

    def __get__(self, obj, cls):
        if obj is None:
            return self
        return super().__get__(obj, cls)[1:]

    def __set__(self, obj, value):
        # ServiceData requires a bytearray.
        return super().__set__(obj, bytearray(obj.frame_type) + value)


class EddystoneFrameBytes:
    """Extracts and manipulates a byte range from an EddystoneAdvertisement. For library use only.

       If length is None, then the byte range must be at the end of the frame.
    """

    def __init__(self, *, length=None, offset=0):
        self._length = length
        self._offset = offset

    def __get__(self, obj, cls):
        if obj is None:
            return self
        if self._length is not None:
            return obj.eddystone_frame[self._offset : self._offset + self._length]
        return obj.eddystone_frame[self._offset :]

    def __set__(self, obj, value):
        if self._length is not None:
            if self._length != len(value):
                raise ValueError("Value length does not match")
            obj.eddystone_frame[self._offset : self._offset + self._length] = value
        else:
            obj.eddystone_frame = obj.eddystone_frame[: self._offset] + value


class EddystoneFrameStruct(EddystoneFrameBytes):
    """Packs and unpacks a single value from a byte range. For library use only."""

    def __init__(self, fmt, *, offset=0):
        self._format = fmt
        super().__init__(offset=offset, length=struct.calcsize(self._format))

    def __get__(self, obj, cls):
        if obj is None:
            return self
        return struct.unpack(self._format, super().__get__(obj, cls))[0]

    def __set__(self, obj, value):
        super().__set__(obj, struct.pack(self._format, value))


class EddystoneAdvertisement(Advertisement):
    """Top level Eddystone advertisement that manages frame type. For library use only."""

    # Subclasses must provide `match_prefixes`.
    services = ServiceList(standard_services=[0x03], vendor_services=[0x07])
    eddystone_frame = _EddystoneFrame()

    def __init__(self, *, minimum_size=None):
        super().__init__()
        self.services.append(_EddystoneService)
        self.connectable = False
        self.flags.general_discovery = True
        self.flags.le_only = True
        # self.frame_type is defined by the subclass.
        if not self.eddystone_frame:
            self.eddystone_frame = bytearray(minimum_size)

    def __str__(self):
        parts = []
        for attr in dir(self.__class__):
            attribute_instance = getattr(self.__class__, attr)
            if issubclass(attribute_instance.__class__, EddystoneFrameBytes):
                value = getattr(self, attr)
                if value is not None:
                    if isinstance(value, memoryview):
                        value = bytes(value)
                    parts.append("{}={}".format(attr, repr(value)))
        return "<{} {} >".format(self.__class__.__name__, " ".join(parts))
