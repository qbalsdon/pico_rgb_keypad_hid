# SPDX-FileCopyrightText: 2019 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_featherwing.rtc_featherwing`
====================================================

Helper for using the `DS3231 Precision RTC FeatherWing
<https://www.adafruit.com/product/3028>`_.

* Author(s): Melissa LeBlanc-Williams
"""

__version__ = "1.13.3"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_FeatherWing.git"

import time
from collections import namedtuple
import board
import adafruit_ds3231


class RTCFeatherWing:
    """Class representing an `DS3231 Precision RTC FeatherWing
    <https://www.adafruit.com/product/3028>`_.

    Automatically uses the feather's I2C bus."""

    def __init__(self, i2c=None):
        if i2c is None:
            i2c = board.I2C()
        self._rtc = adafruit_ds3231.DS3231(i2c)

    def __setitem__(self, index, value):
        """
        Allow updates using setitem if that makes it easier
        """
        self._set_time_value(index, value)

    def __getitem__(self, index):
        """
        Allow retrievals using getitem if that makes it easier
        """
        return self._get_time_value(index)

    def _set_time_value(self, unit, value):
        """
        Set just the specific unit of time
        """
        now = self._get_now()
        if unit in now:
            now[unit] = value
        else:
            raise ValueError("The specified unit of time is invalid")

        self._rtc.datetime = self._encode(now)

    def _get_time_value(self, unit):
        """
        Get just the specific unit of time
        """
        now = self._get_now()
        if unit in now:
            return now[unit]
        raise ValueError("The specified unit of time is invalid")

    def _get_now(self):
        """
        Return the current date and time in a nice updatable dictionary
        """
        now = self._rtc.datetime
        return {
            "second": now.tm_sec,
            "minute": now.tm_min,
            "hour": now.tm_hour,
            "day": now.tm_mday,
            "month": now.tm_mon,
            "year": now.tm_year,
            "weekday": now.tm_wday,
        }

    def _encode(self, date):
        """
        Encode the updatable dictionary back into a time struct
        """
        now = self._rtc.datetime
        return time.struct_time(
            (
                date["year"],
                date["month"],
                date["day"],
                date["hour"],
                date["minute"],
                date["second"],
                date["weekday"],
                now.tm_yday,
                now.tm_isdst,
            )
        )

    def is_leap_year(self, year=None):
        """
        Check if the year is a leap year

        :param int year: (Optional) The year to check. If none is provided, current year is used.
        """
        if year is None:
            year = self._get_time_value("year")
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    def get_month_days(self, month=None, year=None):
        """
        Return the number of days for the month of the given year

        :param int month: (Optional) The month to use. If none is provided, current month is used.
        :param int year: (Optional) The year to check. If none is provided, current year is used.
        """
        if month is None:
            month = self._get_time_value("month")
        leap_year = self.is_leap_year(year)
        max_days = (31, 29 if leap_year else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
        return max_days[month - 1]

    def set_time(self, hour, minute, second=0):
        """
        Set the time only

        :param int hour: The hour we want to set the time to
        :param int minute: The minute we want to set the time to
        :param int second: (Optional) The second we want to set the time to (default=0)
        """
        if not isinstance(second, int) or not 0 <= second < 60:
            raise ValueError("The second must be an integer in the range of 0-59")

        if not isinstance(minute, int) or not 0 <= minute < 60:
            raise ValueError("The minute must be an integer in the range of 0-59")

        if not isinstance(hour, int) or not 0 <= hour < 24:
            raise ValueError("The hour must be an integer in the range of 0-23")

        now = self._get_now()
        now["hour"] = hour
        now["minute"] = minute
        now["second"] = second
        self._rtc.datetime = self._encode(now)

    def set_date(self, day, month, year):
        """
        Set the date only

        :param int day: The day we want to set the date to
        :param int month: The month we want to set the date to
        :param int year: The year we want to set the date to
        """
        if not isinstance(year, int):
            raise ValueError("The year must be an integer")

        if not isinstance(month, int) or not 1 <= month <= 12:
            raise ValueError("The month must be an integer in the range of 1-12")

        month_days = self.get_month_days(month, year)
        if not isinstance(day, int) or not 1 <= day <= month_days:
            raise ValueError(
                "The day must be an integer in the range of 1-{}".format(month_days)
            )

        now = self._get_now()
        now["day"] = day
        now["month"] = month
        now["year"] = year
        self._rtc.datetime = self._encode(now)

    @property
    def datetime(self):
        """
        Passthru property to the ds3231 library for compatibility
        """
        return self._rtc.datetime

    @datetime.setter
    def datetime(self, datetime):
        self._rtc.datetime = datetime

    @property
    def year(self):
        """
        The Current Year
        """
        return self._get_time_value("year")

    @year.setter
    def year(self, year):
        if isinstance(year, int):
            self._set_time_value("year", year)
        else:
            raise ValueError("The year must be an integer")

    @property
    def month(self):
        """
        The Current Month
        """
        return self._get_time_value("month")

    @month.setter
    def month(self, month):
        if isinstance(month, int) and 1 <= month <= 12:
            self._set_time_value("month", month)
        else:
            raise ValueError("The month must be an integer in the range of 1-12")

    @property
    def day(self):
        """
        The Current Day
        """
        return self._get_time_value("day")

    @day.setter
    def day(self, day):
        month_days = self.get_month_days()
        if isinstance(day, int) and 1 <= day <= month_days:
            self._set_time_value("day", day)
        else:
            raise ValueError(
                "The day must be an integer in the range of 1-{}".format(month_days)
            )

    @property
    def hour(self):
        """
        The Current Hour
        """
        return self._get_time_value("hour")

    @hour.setter
    def hour(self, hour):
        if isinstance(hour, int) and 0 <= hour < 24:
            self._set_time_value("hour", hour)
        else:
            raise ValueError("The hour must be an integer in the range of 0-23")

    @property
    def minute(self):
        """
        The Current Minute
        """
        return self._get_time_value("minute")

    @minute.setter
    def minute(self, minute):
        if isinstance(minute, int) and 0 <= minute < 60:
            self._set_time_value("minute", minute)
        else:
            raise ValueError("The minute must be an integer in the range of 0-59")

    @property
    def second(self):
        """
        The Current Second
        """
        return self._get_time_value("second")

    @second.setter
    def second(self, second):
        if isinstance(second, int) and 0 <= second < 60:
            self._set_time_value("second", second)
        else:
            raise ValueError("The second must be an integer in the range of 0-59")

    @property
    def weekday(self):
        """
        The Current Day of the Week Value (0-6) where Sunday is 0
        """
        return self._get_time_value("weekday")

    @weekday.setter
    def weekday(self, weekday):
        if isinstance(weekday, int) and 0 <= weekday < 7:
            self._set_time_value("weekday", weekday)
        else:
            raise ValueError("The weekday must be an integer in the range of 0-6")

    @property
    def now(self):
        """
        The Current Date and Time in Named Tuple Style (Read Only)
        """
        date_time = namedtuple("DateTime", "second minute hour day month year weekday")
        return date_time(**self._get_now())

    @property
    def unixtime(self):
        """
        The Current Date and Time in Unix Time
        """
        try:
            return time.mktime(self._rtc.datetime)
        except (AttributeError, RuntimeError) as error:
            print("Error attempting to run time.mktime() on this board\n", error)

    @unixtime.setter
    def unixtime(self, unixtime):
        if isinstance(unixtime, int):
            try:
                self._rtc.datetime = time.localtime(unixtime)
            except (AttributeError, RuntimeError) as error:
                print("Error attempting to run time.localtime() on this board\n", error)
