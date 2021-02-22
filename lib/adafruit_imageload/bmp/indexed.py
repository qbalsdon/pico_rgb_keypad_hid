# SPDX-FileCopyrightText: 2018 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_imageload.bmp.indexed`
====================================================

Load pixel values (indices or colors) into a bitmap and colors into a palette from an indexed BMP.

* Author(s): Scott Shawcroft

"""

__version__ = "0.13.2"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_ImageLoad.git"

import sys


def load(
    file,
    width,
    height,
    data_start,
    colors,
    color_depth,
    compression,
    *,
    bitmap=None,
    palette=None
):
    """Loads indexed bitmap data into bitmap and palette objects.

    :param file file: The open bmp file
    :param int width: Image width in pixels
    :param int height: Image height in pixels
    :param int data_start: Byte location where the data starts (after headers)
    :param int colors: Number of distinct colors in the image
    :param int color_depth: Number of bits used to store a value
    :param int compression: 0 - none, 1 - 8bit RLE, 2 - 4bit RLE"""
    # pylint: disable=too-many-arguments,too-many-locals,too-many-branches
    if palette:
        palette = palette(colors)

        file.seek(data_start - colors * 4)
        for value in range(colors):
            c_bytes = file.read(4)
            # Need to swap red & blue bytes (bytes 0 and 2)
            palette[value] = bytes(
                b"".join([c_bytes[2:3], c_bytes[1:2], c_bytes[0:1], c_bytes[3:1]])
            )

    if bitmap:
        minimum_color_depth = 1
        while colors > 2 ** minimum_color_depth:
            minimum_color_depth *= 2

        if sys.maxsize > 1073741823:
            # pylint: disable=import-outside-toplevel
            from .negative_height_check import negative_height_check

            # convert unsigned int to signed int when height is negative
            height = negative_height_check(height)
        bitmap = bitmap(width, abs(height), colors)
        file.seek(data_start)
        line_size = width // (8 // color_depth)
        if width % (8 // color_depth) != 0:
            line_size += 1
        if line_size % 4 != 0:
            line_size += 4 - line_size % 4

        mask = (1 << minimum_color_depth) - 1
        if height > 0:
            range1 = height - 1
            range2 = -1
            range3 = -1
        else:
            range1 = 0
            range2 = abs(height)
            range3 = 1

        if compression == 0:
            chunk = bytearray(line_size)
            for y in range(range1, range2, range3):
                file.readinto(chunk)
                pixels_per_byte = 8 // color_depth
                offset = y * width

                for x in range(width):
                    i = x // pixels_per_byte
                    pixel = (
                        chunk[i] >> (8 - color_depth * (x % pixels_per_byte + 1))
                    ) & mask
                    bitmap[offset + x] = pixel
        elif compression in (1, 2):
            decode_rle(
                bitmap=bitmap,
                file=file,
                compression=compression,
                y_range=(range1, range2, range3),
                width=width,
            )

    return bitmap, palette


def decode_rle(bitmap, file, compression, y_range, width):
    """Helper to decode RLE images"""
    # pylint: disable=too-many-locals,too-many-nested-blocks,too-many-branches

    # RLE algorithm, either 8-bit (1) or 4-bit (2)
    #
    # Ref: http://www.fileformat.info/format/bmp/egff.htm

    is_4bit = compression == 2

    # This will store the 2-byte run commands, which are either an
    # amount to repeat and a value to repeat, or a 0x00 and command
    # marker.
    run_buf = bytearray(2)

    # We need to be prepared to load up to 256 pixels of literal image
    # data. (0xFF is max literal length, but odd literal runs are padded
    # up to an even byte count, so we need space for 256 in the case of
    # 8-bit.) 4-bit images can get away with half that.
    literal_buf = bytearray(128 if is_4bit else 256)

    # We iterate with numbers rather than a range because the "delta"
    # command can cause us to jump forward arbitrarily in the output
    # image.
    #
    # In theory RLE images are only stored in bottom-up scan line order,
    # but we support either.
    (range1, range2, range3) = y_range
    y = range1
    x = 0

    while y * range3 < range2 * range3:
        offset = y * width + x

        # We keep track of how much space is left in our row so that we
        # can avoid writing extra data outside of the Bitmap. While the
        # reference above seems to say that the "end run" command is
        # optional and that image data should wrap from one scan line to
        # the next, in practice (looking at the output of ImageMagick
        # and GIMP, and what Preview renders) the bitmap part of the
        # image can contain data that goes beyond the image’s stated
        # width that should just be ignored. For example, the 8bit RLE
        # file is 15px wide but has data for 16px.
        width_remaining = width - x

        file.readinto(run_buf)

        if run_buf[0] == 0:
            # A repeat length of "0" is a special command. The next byte
            # tells us what needs to happen.
            if run_buf[1] == 0:
                # end of the current scan line
                y = y + range3
                x = 0
            elif run_buf[1] == 1:
                # end of image
                break
            elif run_buf[1] == 2:
                # delta command jumps us ahead in the bitmap output by
                # the x, y amounts stored in the next 2 bytes.
                file.readinto(run_buf)

                x = x + run_buf[0]
                y = y + run_buf[1] * range3
            else:
                # command values of 3 or more indicate that many pixels
                # of literal (uncompressed) image data. For 8-bit mode,
                # this is raw bytes, but 4-bit mode counts in nibbles.
                literal_length_px = run_buf[1]

                # Inverting the value here to get round-up integer division
                if is_4bit:
                    read_length_bytes = -(-literal_length_px // 2)
                else:
                    read_length_bytes = literal_length_px

                # If the run has an odd length then there’s a 1-byte padding
                # we need to consume but not write into the output
                if read_length_bytes % 2 == 1:
                    read_length_bytes += 1

                # We use memoryview to artificially limit the length of
                # literal_buf so that readinto only reads the amount
                # that we want.
                literal_buf_mem = memoryview(literal_buf)
                file.readinto(literal_buf_mem[0:read_length_bytes])

                if is_4bit:
                    for i in range(0, min(literal_length_px, width_remaining)):
                        # Expanding the two nibbles of the 4-bit data
                        # into two bytes for our output bitmap.
                        if i % 2 == 0:
                            bitmap[offset + i] = literal_buf[i // 2] >> 4
                        else:
                            bitmap[offset + i] = literal_buf[i // 2] & 0x0F
                else:
                    # 8-bit values are just a raw copy (limited by
                    # what’s left in the row so we don’t overflow out of
                    # the buffer)
                    for i in range(0, min(literal_length_px, width_remaining)):
                        bitmap[offset + i] = literal_buf[i]

                x = x + literal_length_px
        else:
            # first byte was not 0, which means it tells us how much to
            # repeat the next byte into the output
            run_length_px = run_buf[0]

            if is_4bit:
                # In 4 bit mode, we repeat the *two* values that are
                # packed into the next byte. The repeat amount is based
                # on pixels, not bytes, though, so if we were to repeat
                # 0xab 3 times, the output pixel values would be: 0x0a
                # 0x0b 0x0a (notice how it ends at 0x0a) rather than
                # 0x0a 0x0b 0x0a 0x0b 0x0a 0x0b
                run_values = [run_buf[1] >> 4, run_buf[1] & 0x0F]
                for i in range(0, min(run_length_px, width_remaining)):
                    bitmap[offset + i] = run_values[i % 2]
            else:
                run_value = run_buf[1]
                for i in range(0, min(run_length_px, width_remaining)):
                    bitmap[offset + i] = run_value

            x = x + run_length_px
