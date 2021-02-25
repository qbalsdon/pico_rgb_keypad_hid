# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_display_notification.apple`
================================================================================

Maps Apple Notification Center Notification objects to the notification widgets
in this library.

"""

from . import PlainNotification

__version__ = "0.9.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Display_Notification.git"


def create_notification_widget(
    notification, max_width, max_height, *, color_count=2 ** 16
):
    """Creates a notification widget for the given Apple notification."""
    # pylint: disable=unused-argument
    return PlainNotification(
        notification.title, notification.message, max_width, max_height
    )
