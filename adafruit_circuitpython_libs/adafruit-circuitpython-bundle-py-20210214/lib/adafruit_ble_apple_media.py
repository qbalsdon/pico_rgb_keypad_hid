# SPDX-FileCopyrightText: 2020 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_ble_apple_media`
================================================================================

Support for the Apple Media Service which provides media playback info and control.

Documented by Apple here:
https://developer.apple.com/library/archive/documentation/CoreBluetooth/Reference/AppleMediaService_Reference/Introduction/Introduction.html#//apple_ref/doc/uid/TP40014716-CH2-SW1

"""
import struct
import time

import _bleio

from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic, ComplexCharacteristic
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.services import Service

__version__ = "0.9.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_Apple_Media.git"

# Disable protected access checks since our private classes are tightly coupled.
# pylint: disable=protected-access


class _RemoteCommand(ComplexCharacteristic):
    """Endpoint for sending commands to a media player. The value read will list all available

    commands."""

    uuid = VendorUUID("9B3C81D8-57B1-4A8A-B8DF-0E56F7CA51C2")

    def __init__(self):
        super().__init__(
            properties=Characteristic.WRITE_NO_RESPONSE | Characteristic.NOTIFY,
            read_perm=Attribute.OPEN,
            write_perm=Attribute.OPEN,
            max_length=13,
            fixed_length=False,
        )

    def bind(self, service):
        """Binds the characteristic to the given Service."""
        bound_characteristic = super().bind(service)
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=1)


class _EntityUpdate(ComplexCharacteristic):
    """UTF-8 Encoded string characteristic."""

    uuid = VendorUUID("2F7CABCE-808D-411F-9A0C-BB92BA96C102")

    def __init__(self):
        super().__init__(
            properties=Characteristic.WRITE | Characteristic.NOTIFY,
            read_perm=Attribute.OPEN,
            write_perm=Attribute.OPEN,
            max_length=128,
            fixed_length=False,
        )

    def bind(self, service):
        """Binds the characteristic to the given Service."""
        bound_characteristic = super().bind(service)
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=8)


class _EntityAttribute(Characteristic):  # pylint: disable=too-few-public-methods
    """UTF-8 Encoded string characteristic."""

    uuid = VendorUUID("C6B2F38C-23AB-46D8-A6AB-A3A870BBD5D7")

    def __init__(self):
        super().__init__(
            properties=Characteristic.WRITE | Characteristic.READ,
            read_perm=Attribute.OPEN,
            write_perm=Attribute.OPEN,
            fixed_length=False,
        )


class _MediaAttribute:
    def __init__(self, entity_id, attribute_id):
        self.key = (entity_id, attribute_id)

    @staticmethod
    def _update(obj):
        if not obj._buffer:
            obj._buffer = bytearray(128)
        length_read = obj._entity_update.readinto(obj._buffer)
        if length_read > 0:
            if length_read < 4:
                raise RuntimeError("packet too short")
            # Even though flags is currently unused, if it were removed, it would cause there to be
            # too many values to unpack which would raise a ValueError
            (
                entity_id,
                attribute_id,
                flags,  # pylint: disable=unused-variable
            ) = struct.unpack_from("<BBB", obj._buffer)
            value = str(obj._buffer[3:length_read], "utf-8")
            obj._attribute_cache[(entity_id, attribute_id)] = value

    def __get__(self, obj, cls):
        self._update(obj)
        if self.key not in obj._attribute_cache:
            siblings = [self.key[1]]
            for k in obj._attribute_cache:
                if k[0] == self.key[0] and k[1] not in siblings:
                    siblings.append(k[1])
            buf = struct.pack("<B" + "B" * len(siblings), self.key[0], *siblings)
            obj._entity_update.write(buf)
            obj._attribute_cache[self.key] = None
            time.sleep(0.05)
            self._update(obj)
        return obj._attribute_cache[self.key]


class _MediaAttributePlaybackState:
    def __init__(self, playback_value):
        self._playback_value = playback_value

    def __get__(self, obj, cls):
        info = obj._playback_info
        if info:
            return int(info.split(",")[0]) == self._playback_value
        return False


class _MediaAttributePlaybackInfo:
    def __init__(self, position):
        self._position = position

    def __get__(self, obj, cls):
        info = obj._playback_info
        if info:
            return float(info.split(",")[self._position])
        return 0


class UnsupportedCommand(Exception):
    """Raised when the command isn't available with current media player app."""


class AppleMediaService(Service):
    """View and control currently playing media.

    Exact functionality varies with different media apps. For example, Spotify will include the
    album name and artist name in `title` when controlling playback on a remote device.
    `artist` includes a description of the remote playback.

    """

    uuid = VendorUUID("89D3502B-0F36-433A-8EF4-C502AD55F8DC")

    _remote_command = _RemoteCommand()
    _entity_update = _EntityUpdate()
    _entity_attribute = _EntityAttribute()

    player_name = _MediaAttribute(0, 0)
    """Name of the media player app"""
    _playback_info = _MediaAttribute(0, 1)
    paused = _MediaAttributePlaybackState(0)
    """True when playback is paused. False otherwise."""
    playing = _MediaAttributePlaybackState(1)
    """True when playback is playing. False otherwise."""
    rewinding = _MediaAttributePlaybackState(2)
    """True when playback is rewinding. False otherwise."""
    fast_forwarding = _MediaAttributePlaybackState(3)
    """True when playback is fast-forwarding. False otherwise."""
    playback_rate = _MediaAttributePlaybackInfo(1)
    """Playback rate as a decimal of normal speed."""
    elapsed_time = _MediaAttributePlaybackInfo(2)
    """Time elapsed in the current track. Not updated as the track plays. Use (the amount of time
       since read elapsed time) * `playback_rate` to estimate the current `elapsed_time`."""
    volume = _MediaAttribute(0, 2)
    """Current volume"""

    queue_index = _MediaAttribute(1, 0)
    """Current track's index in the queue."""
    queue_length = _MediaAttribute(1, 1)
    """Count of tracks in the queue."""
    shuffle_mode = _MediaAttribute(1, 2)
    """Current shuffle mode as an integer. Off (0), One (1), and All (2)"""
    repeat_mode = _MediaAttribute(1, 3)
    """Current repeat mode as an integer. Off (0), One (1), and All (2)"""

    artist = _MediaAttribute(2, 0)
    """Current track's artist name."""
    album = _MediaAttribute(2, 1)
    """Current track's album name."""
    title = _MediaAttribute(2, 2)
    """Current track's title."""
    duration = _MediaAttribute(2, 3)
    """Current track's duration as a string."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._buffer = None
        self._cmd = None
        self._register_buffer = None
        self._attribute_cache = {}
        self._supported_commands = []
        self._command_buffer = None

    def _send_command(self, command_id):
        if not self._command_buffer:
            self._command_buffer = bytearray(13)
        i = self._remote_command.readinto(  # pylint: disable=no-member
            self._command_buffer
        )
        if i > 0:
            self._supported_commands = list(self._command_buffer[:i])
        if command_id not in self._supported_commands:
            if not self._supported_commands:
                return
            raise UnsupportedCommand()
        if not self._cmd:
            self._cmd = bytearray(1)
        self._cmd[0] = command_id
        self._remote_command.write(self._cmd)  # pylint: disable=no-member

    def play(self):
        """Plays the current track. Does nothing if already playing."""
        self._send_command(0)

    def pause(self):
        """Pauses the current track. Does nothing if already paused."""
        self._send_command(1)

    def toggle_play_pause(self):
        """Plays the current track if it is paused. Otherwise it pauses the track."""
        self._send_command(2)

    def next_track(self):
        """Stops playing the current track and plays the next one."""
        self._send_command(3)

    def previous_track(self):
        """Stops playing the current track and plays the previous track."""
        self._send_command(4)

    def volume_up(self):
        """Increases the playback volume."""
        self._send_command(5)

    def volume_down(self):
        """Decreases the playback volume."""
        self._send_command(6)

    def advance_repeat_mode(self):
        """Advances the repeat mode. Modes are: Off, One and All"""
        self._send_command(7)

    def advance_shuffle_mode(self):
        """Advances the shuffle mode. Modes are: Off, One and All"""
        self._send_command(8)

    def skip_forward(self):
        """Skips forwards in the current track"""
        self._send_command(9)

    def skip_backward(self):
        """Skips backwards in the current track"""
        self._send_command(10)

    def like_track(self):
        """Likes the current track"""
        self._send_command(11)

    def dislike_track(self):
        """Dislikes the current track"""
        self._send_command(12)

    def bookmark_track(self):
        """Bookmarks the current track"""
        self._send_command(13)
