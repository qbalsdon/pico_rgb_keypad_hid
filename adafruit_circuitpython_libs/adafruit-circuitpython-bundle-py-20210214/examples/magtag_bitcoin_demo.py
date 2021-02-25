# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense
from adafruit_magtag.magtag import MagTag

# Set up where we'll be fetching data from
DATA_SOURCE = "https://api.coindesk.com/v1/bpi/currentprice.json"
DATA_LOCATION = ["bpi", "USD", "rate_float"]


def text_transform(val):
    return "Bitcoin: $%d" % val


magtag = MagTag(
    url=DATA_SOURCE,
    json_path=DATA_LOCATION,
)

magtag.network.connect()

magtag.add_text(
    text_position=(
        (magtag.graphics.display.width // 2) - 1,
        (magtag.graphics.display.height // 2) - 1,
    ),
    text_scale=3,
    text_transform=text_transform,
    text_anchor_point=(0.5, 0.5),
)

try:
    value = magtag.fetch()
    print("Response is", value)
except (ValueError, RuntimeError) as e:
    print("Some error occured, retrying! -", e)
magtag.exit_and_deep_sleep(60)
