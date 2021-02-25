# SPDX-FileCopyrightText: 2020 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bitmap_font.pcf`
====================================================

Loads PCF format fonts.

* Author(s): Jeff Epler

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

from collections import namedtuple
import gc
import struct

from fontio import Glyph
from .glyph_cache import GlyphCache

_PCF_PROPERTIES = 1 << 0
_PCF_ACCELERATORS = 1 << 1
_PCF_METRICS = 1 << 2
_PCF_BITMAPS = 1 << 3
_PCF_INK_METRICS = 1 << 4
_PCF_BDF_ENCODINGS = 1 << 5
_PCF_SWIDTHS = 1 << 6
_PCF_GLYPH_NAMES = 1 << 7
_PCF_BDF_ACCELERATORS = 1 << 8

_PCF_DEFAULT_FORMAT = 0x00000000
_PCF_INKBOUNDS = 0x00000200
_PCF_ACCEL_W_INKBOUNDS = 0x00000100
_PCF_COMPRESSED_METRICS = 0x00000100

_PCF_GLYPH_PAD_MASK = 3 << 0  # See the bitmap table for explanation */
_PCF_BYTE_MASK = 1 << 2  # If set then Most Sig Byte First */
_PCF_BIT_MASK = 1 << 3  # If set then Most Sig Bit First */
_PCF_SCAN_UNIT_MASK = 3 << 4

# https://fontforge.org/docs/techref/pcf-format.html

Table = namedtuple("Table", ("format", "size", "offset"))
Metrics = namedtuple(
    "Metrics",
    (
        "left_side_bearing",
        "right_side_bearing",
        "character_width",
        "character_ascent",
        "character_descent",
        "character_attributes",
    ),
)
Accelerators = namedtuple(
    "Accelerators",
    (
        "no_overlap",
        "constant_metrics",
        "terminal_font",
        "constant_width",
        "ink_inside",
        "ink_metrics",
        "draw_direction",
        "font_ascent",
        "font_descent",
        "max_overlap",
        "minbounds",
        "maxbounds",
        "ink_minbounds",
        "ink_maxbounds",
    ),
)
Encoding = namedtuple(
    "Encoding", ("min_byte2", "max_byte2", "min_byte1", "max_byte1", "default_char")
)
Bitmap = namedtuple("Bitmap", ("glyph_count", "bitmap_sizes"))


class PCF(GlyphCache):
    """Loads glyphs from a PCF file in the given bitmap_class."""

    def __init__(self, f, bitmap_class):
        super().__init__()
        self.file = f
        self.name = f
        f.seek(0)
        self.buffer = bytearray(1)
        self.bitmap_class = bitmap_class
        _, table_count = self._read("<4sI")
        self.tables = {}
        for _ in range(table_count):
            type_, format_, size, offset = self._read("<IIII")
            self.tables[type_] = Table(format_, size, offset)

        bitmap_format = self.tables[_PCF_BITMAPS].format
        if bitmap_format != 0xE:
            raise NotImplementedError("Unsupported format %s" % bitmap_format)

        self._accel = self._read_accelerator_tables()
        self._encoding = self._read_encoding_table()
        self._bitmaps = self._read_bitmap_table()

        self._ascent = self._accel.font_ascent
        self._descent = self._accel.font_descent

        minbounds = self._accel.ink_minbounds
        maxbounds = self._accel.ink_maxbounds
        width = maxbounds.right_side_bearing - minbounds.left_side_bearing
        height = maxbounds.character_ascent + maxbounds.character_descent

        self._bounding_box = (
            width,
            height,
            minbounds.left_side_bearing,
            -maxbounds.character_descent,
        )

    @property
    def ascent(self):
        """The number of pixels above the baseline of a typical ascender"""
        return self._ascent

    @property
    def descent(self):
        """The number of pixels below the baseline of a typical descender"""
        return self._descent

    def get_bounding_box(self):
        """Return the maximum glyph size as a 4-tuple of: width, height, x_offset, y_offset"""
        return self._bounding_box

    def _read(self, format_):
        size = struct.calcsize(format_)
        if size != len(self.buffer):
            self.buffer = bytearray(size)
        self.file.readinto(self.buffer)
        return struct.unpack_from(format_, self.buffer)

    def _seek_table(self, table):
        self.file.seek(table.offset)
        (format_,) = self._read("<I")

        if format_ & _PCF_BYTE_MASK == 0:
            raise RuntimeError("Only big endian supported")

        return format_

    def _read_encoding_table(self):
        encoding = self.tables[_PCF_BDF_ENCODINGS]
        self._seek_table(encoding)

        return Encoding(*self._read(">hhhhh"))

    def _read_bitmap_table(self):
        bitmaps = self.tables[_PCF_BITMAPS]
        format_ = self._seek_table(bitmaps)

        (glyph_count,) = self._read(">I")
        self.file.seek(bitmaps.offset + 8 + 4 * glyph_count)
        bitmap_sizes = self._read(">4I")
        return Bitmap(glyph_count, bitmap_sizes[format_ & 3])

    def _read_metrics(self, compressed_metrics):
        if compressed_metrics:
            (
                left_side_bearing,
                right_side_bearing,
                character_width,
                character_ascent,
                character_descent,
            ) = self._read("5B")
            left_side_bearing -= 0x80
            right_side_bearing -= 0x80
            character_width -= 0x80
            character_ascent -= 0x80
            character_descent -= 0x80
            attributes = 0
        else:
            (
                left_side_bearing,
                right_side_bearing,
                character_width,
                character_ascent,
                character_descent,
                attributes,
            ) = self._read(">5hH")
        return Metrics(
            left_side_bearing,
            right_side_bearing,
            character_width,
            character_ascent,
            character_descent,
            attributes,
        )

    def _read_accelerator_tables(self):
        # pylint: disable=too-many-locals
        accelerators = self.tables.get(_PCF_BDF_ACCELERATORS)
        if not accelerators:
            accelerators = self.tables.get(_PCF_ACCELERATORS)
        if not accelerators:
            raise RuntimeError("Accelerator table missing")

        format_ = self._seek_table(accelerators)

        has_inkbounds = format_ & _PCF_ACCEL_W_INKBOUNDS
        compressed_metrics = format_ & _PCF_COMPRESSED_METRICS

        (
            no_overlap,
            constant_metrics,
            terminal_font,
            constant_width,
            ink_inside,
            ink_metrics,
            draw_direction,
            _,
            font_ascent,
            font_descent,
            max_overlap,
        ) = self._read(">BBBBBBBBIII")
        minbounds = self._read_metrics(compressed_metrics)
        maxbounds = self._read_metrics(compressed_metrics)
        if has_inkbounds:
            ink_minbounds = self._read_metrics(compressed_metrics)
            ink_maxbounds = self._read_metrics(compressed_metrics)
        else:
            ink_minbounds = minbounds
            ink_maxbounds = maxbounds

        return Accelerators(
            no_overlap,
            constant_metrics,
            terminal_font,
            constant_width,
            ink_inside,
            ink_metrics,
            draw_direction,
            font_ascent,
            font_descent,
            max_overlap,
            minbounds,
            maxbounds,
            ink_minbounds,
            ink_maxbounds,
        )

    def _read_properties(self):
        property_table_offset = self.tables[_PCF_PROPERTIES]["offset"]
        self.file.seek(property_table_offset)
        (format_,) = self._read("<I")

        if format_ & _PCF_BYTE_MASK == 0:
            raise RuntimeError("Only big endian supported")
        (nprops,) = self._read(">I")
        self.file.seek(property_table_offset + 8 + 9 * nprops)

        pos = self.file.tell()
        if pos % 4 > 0:
            self.file.read(4 - pos % 4)
        (string_size,) = self._read(">I")

        strings = self.file.read(string_size)
        string_map = {}
        i = 0
        for value in strings.split(b"\x00"):
            string_map[i] = value
            i += len(value) + 1

        self.file.seek(property_table_offset + 8)
        for _ in range(nprops):
            name_offset, is_string_prop, value = self._read(">IBI")

            if is_string_prop:
                yield (string_map[name_offset], string_map[value])
            else:
                yield (string_map[name_offset], value)

    def load_glyphs(self, code_points):
        # pylint: disable=too-many-statements,too-many-branches,too-many-nested-blocks,too-many-locals
        if isinstance(code_points, int):
            code_points = (code_points,)
        elif isinstance(code_points, str):
            code_points = [ord(c) for c in code_points]

        code_points = sorted(
            c for c in code_points if self._glyphs.get(c, None) is None
        )
        if not code_points:
            return

        indices_offset = self.tables[_PCF_BDF_ENCODINGS].offset + 14
        bitmap_offset_offsets = self.tables[_PCF_BITMAPS].offset + 8
        first_bitmap_offset = self.tables[_PCF_BITMAPS].offset + 4 * (
            6 + self._bitmaps.glyph_count
        )
        metrics_compressed = self.tables[_PCF_METRICS].format & _PCF_COMPRESSED_METRICS
        first_metric_offset = self.tables[_PCF_METRICS].offset + (
            6 if metrics_compressed else 8
        )
        metrics_size = 5 if metrics_compressed else 12

        # These will each _tend to be_ forward reads in the file, at least
        # sometimes we'll benefit from oofatfs's 512 byte cache and avoid
        # excess reads
        indices = [None] * len(code_points)
        for i, code_point in enumerate(code_points):
            enc1 = (code_point >> 8) & 0xFF
            enc2 = code_point & 0xFF

            if enc1 < self._encoding.min_byte1 or enc1 > self._encoding.max_byte1:
                continue
            if enc2 < self._encoding.min_byte2 or enc2 > self._encoding.max_byte2:
                continue

            encoding_idx = (
                (enc1 - self._encoding.min_byte1)
                * (self._encoding.max_byte2 - self._encoding.min_byte2 + 1)
                + enc2
                - self._encoding.min_byte2
            )
            self.file.seek(indices_offset + 2 * encoding_idx)
            (glyph_idx,) = self._read(">H")
            if glyph_idx != 65535:
                indices[i] = glyph_idx

        all_metrics = [None] * len(code_points)
        for i, code_point in enumerate(code_points):
            index = indices[i]
            if index is None:
                continue
            self.file.seek(first_metric_offset + metrics_size * index)
            all_metrics[i] = self._read_metrics(metrics_compressed)
        bitmap_offsets = [None] * len(code_points)
        for i, code_point in enumerate(code_points):
            index = indices[i]
            if index is None:
                continue
            self.file.seek(bitmap_offset_offsets + 4 * index)
            (bitmap_offset,) = self._read(">I")
            bitmap_offsets[i] = bitmap_offset

        # Batch creation of glyphs and bitmaps so that we need only gc.collect
        # once
        gc.collect()
        bitmaps = [None] * len(code_points)
        for i in range(len(all_metrics)):  # pylint: disable=consider-using-enumerate
            metrics = all_metrics[i]
            if metrics is not None:
                width = metrics.right_side_bearing - metrics.left_side_bearing
                height = metrics.character_ascent + metrics.character_descent
                bitmap = bitmaps[i] = self.bitmap_class(width, height, 2)
                self._glyphs[code_points[i]] = Glyph(
                    bitmap,
                    0,
                    width,
                    height,
                    metrics.left_side_bearing,
                    -metrics.character_descent,
                    metrics.character_width,
                    0,
                )

        for i, code_point in enumerate(code_points):
            metrics = all_metrics[i]
            if metrics is None:
                continue
            self.file.seek(first_bitmap_offset + bitmap_offsets[i])
            width = metrics.right_side_bearing - metrics.left_side_bearing
            height = metrics.character_ascent + metrics.character_descent

            bitmap = bitmaps[i]
            words_per_row = (width + 31) // 32
            buf = bytearray(4 * words_per_row)
            start = 0
            for _ in range(height):
                self.file.readinto(buf)
                for k in range(width):
                    if buf[k // 8] & (128 >> (k % 8)):
                        bitmap[start + k] = 1
                start += width
