# SPDX-FileCopyrightText: 2001-2021 Python Software Foundation.All rights reserved.
# SPDX-FileCopyrightText: 2000 BeOpen.com. All rights reserved.
# SPDX-FileCopyrightText: 1995-2001 Corporation for National Research Initiatives.
#                         All rights reserved.
# SPDX-FileCopyrightText: 1995-2001 Corporation for National Research Initiatives.
#                         All rights reserved.
# SPDX-FileCopyrightText: 1991-1995 Stichting Mathematisch Centrum. All rights reserved.
# SPDX-FileCopyrightText: 2017 Paul Sokolovsky
# SPDX-License-Identifier: Python-2.0

"""
`adafruit_datetime`
================================================================================
Concrete date/time and related types.

See http://www.iana.org/time-zones/repository/tz-link.html for
time zone and DST data sources.

Implementation Notes
--------------------

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases


"""
# pylint: disable=too-many-lines
import time as _time
import math as _math
from micropython import const

__version__ = "1.0.1"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_DateTime.git"

# Constants
MINYEAR = const(1)
MAXYEAR = const(9999)
_MAXORDINAL = const(3652059)
_DI400Y = const(146097)
_DI100Y = const(36524)
_DI4Y = const(1461)
# https://svn.python.org/projects/sandbox/trunk/datetime/datetime.py
_DAYS_IN_MONTH = (None, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_DAYS_BEFORE_MONTH = (None, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
# Month and day names.  For localized versions, see the calendar module.
_MONTHNAMES = (
    None,
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
_DAYNAMES = (None, "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# Utility functions - universal
def _cmp(obj_x, obj_y):
    return 0 if obj_x == obj_y else 1 if obj_x > obj_y else -1


def _cmperror(obj_x, obj_y):
    raise TypeError(
        "can't compare '%s' to '%s'" % (type(obj_x).__name__, type(obj_y).__name__)
    )


# Utility functions - time
def _check_time_fields(hour, minute, second, microsecond, fold):
    if not isinstance(hour, int):
        raise TypeError("Hour expected as int")
    if not 0 <= hour <= 23:
        raise ValueError("hour must be in 0..23", hour)
    if not 0 <= minute <= 59:
        raise ValueError("minute must be in 0..59", minute)
    if not 0 <= second <= 59:
        raise ValueError("second must be in 0..59", second)
    if not 0 <= microsecond <= 999999:
        raise ValueError("microsecond must be in 0..999999", microsecond)
    if fold not in (0, 1):  # from CPython API
        raise ValueError("fold must be either 0 or 1", fold)


def _check_utc_offset(name, offset):
    assert name in ("utcoffset", "dst")
    if offset is None:
        return
    if not isinstance(offset, timedelta):
        raise TypeError(
            "tzinfo.%s() must return None "
            "or timedelta, not '%s'" % (name, type(offset))
        )
    if offset % timedelta(minutes=1) or offset.microseconds:
        raise ValueError(
            "tzinfo.%s() must return a whole number "
            "of minutes, got %s" % (name, offset)
        )
    if not -timedelta(1) < offset < timedelta(1):
        raise ValueError(
            "%s()=%s, must be must be strictly between"
            " -timedelta(hours=24) and timedelta(hours=24)" % (name, offset)
        )


# pylint: disable=invalid-name
def _format_offset(off):
    s = ""
    if off is not None:
        if off.days < 0:
            sign = "-"
            off = -off
        else:
            sign = "+"
        hh, mm = divmod(off, timedelta(hours=1))
        mm, ss = divmod(mm, timedelta(minutes=1))
        s += "%s%02d:%02d" % (sign, hh, mm)
        if ss or ss.microseconds:
            s += ":%02d" % ss.seconds

            if ss.microseconds:
                s += ".%06d" % ss.microseconds
    return s


# Utility functions - timezone
def _check_tzname(name):
    """"Just raise TypeError if the arg isn't None or a string."""
    if name is not None and not isinstance(name, str):
        raise TypeError(
            "tzinfo.tzname() must return None or string, " "not '%s'" % type(name)
        )


def _check_tzinfo_arg(time_zone):
    if time_zone is not None and not isinstance(time_zone, tzinfo):
        raise TypeError("tzinfo argument must be None or of a tzinfo subclass")


# Utility functions - date
def _is_leap(year):
    "year -> 1 if leap year, else 0."
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _days_in_month(year, month):
    "year, month -> number of days in that month in that year."
    assert 1 <= month <= 12, month
    if month == 2 and _is_leap(year):
        return 29
    return _DAYS_IN_MONTH[month]


def _check_date_fields(year, month, day):
    if not isinstance(year, int):
        raise TypeError("int expected")
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError("year must be in %d..%d" % (MINYEAR, MAXYEAR), year)
    if not 1 <= month <= 12:
        raise ValueError("month must be in 1..12", month)
    dim = _days_in_month(year, month)
    if not 1 <= day <= dim:
        raise ValueError("day must be in 1..%d" % dim, day)


def _days_before_month(year, month):
    "year, month -> number of days in year preceding first day of month."
    assert 1 <= month <= 12, "month must be in 1..12"
    return _DAYS_BEFORE_MONTH[month] + (month > 2 and _is_leap(year))


def _days_before_year(year):
    "year -> number of days before January 1st of year."
    year = year - 1
    return year * 365 + year // 4 - year // 100 + year // 400


def _ymd2ord(year, month, day):
    "year, month, day -> ordinal, considering 01-Jan-0001 as day 1."
    assert 1 <= month <= 12, "month must be in 1..12"
    dim = _days_in_month(year, month)
    assert 1 <= day <= dim, "day must be in 1..%d" % dim
    return _days_before_year(year) + _days_before_month(year, month) + day


# pylint: disable=too-many-arguments
def _build_struct_time(tm_year, tm_month, tm_mday, tm_hour, tm_min, tm_sec, tm_isdst):
    tm_wday = (_ymd2ord(tm_year, tm_month, tm_mday) + 6) % 7
    tm_yday = _days_before_month(tm_year, tm_month) + tm_mday
    return _time.struct_time(
        (
            tm_year,
            tm_month,
            tm_mday,
            tm_hour,
            tm_min,
            tm_sec,
            tm_wday,
            tm_yday,
            tm_isdst,
        )
    )


# pylint: disable=invalid-name
def _format_time(hh, mm, ss, us, timespec="auto"):
    if timespec != "auto":
        raise NotImplementedError("Only default timespec supported")
    if us:
        spec = "{:02d}:{:02d}:{:02d}.{:06d}"
    else:
        spec = "{:02d}:{:02d}:{:02d}"
    fmt = spec
    return fmt.format(hh, mm, ss, us)


# A 4-year cycle has an extra leap day over what we'd get from pasting
# together 4 single years.
assert _DI4Y == 4 * 365 + 1

# Similarly, a 400-year cycle has an extra leap day over what we'd get from
# pasting together 4 100-year cycles.
assert _DI400Y == 4 * _DI100Y + 1

# OTOH, a 100-year cycle has one fewer leap day than we'd get from
# pasting together 25 4-year cycles.
assert _DI100Y == 25 * _DI4Y - 1


def _ord2ymd(n):
    "ordinal -> (year, month, day), considering 01-Jan-0001 as day 1."

    # n is a 1-based index, starting at 1-Jan-1.  The pattern of leap years
    # repeats exactly every 400 years.  The basic strategy is to find the
    # closest 400-year boundary at or before n, then work with the offset
    # from that boundary to n.  Life is much clearer if we subtract 1 from
    # n first -- then the values of n at 400-year boundaries are exactly
    # those divisible by _DI400Y:
    #
    #     D  M   Y            n              n-1
    #     -- --- ----        ----------     ----------------
    #     31 Dec -400        -_DI400Y       -_DI400Y -1
    #      1 Jan -399         -_DI400Y +1   -_DI400Y      400-year boundary
    #     ...
    #     30 Dec  000        -1             -2
    #     31 Dec  000         0             -1
    #      1 Jan  001         1              0            400-year boundary
    #      2 Jan  001         2              1
    #      3 Jan  001         3              2
    #     ...
    #     31 Dec  400         _DI400Y        _DI400Y -1
    #      1 Jan  401         _DI400Y +1     _DI400Y      400-year boundary
    n -= 1
    n400, n = divmod(n, _DI400Y)
    year = n400 * 400 + 1  # ..., -399, 1, 401, ...

    # Now n is the (non-negative) offset, in days, from January 1 of year, to
    # the desired date.  Now compute how many 100-year cycles precede n.
    # Note that it's possible for n100 to equal 4!  In that case 4 full
    # 100-year cycles precede the desired day, which implies the desired
    # day is December 31 at the end of a 400-year cycle.
    n100, n = divmod(n, _DI100Y)

    # Now compute how many 4-year cycles precede it.
    n4, n = divmod(n, _DI4Y)

    # And now how many single years.  Again n1 can be 4, and again meaning
    # that the desired day is December 31 at the end of the 4-year cycle.
    n1, n = divmod(n, 365)

    year += n100 * 100 + n4 * 4 + n1
    if n1 == 4 or n100 == 4:
        assert n == 0
        return year - 1, 12, 31

    # Now the year is correct, and n is the offset from January 1.  We find
    # the month via an estimate that's either exact or one too large.
    leapyear = n1 == 3 and (n4 != 24 or n100 == 3)
    assert leapyear == _is_leap(year)
    month = (n + 50) >> 5
    preceding = _DAYS_BEFORE_MONTH[month] + (month > 2 and leapyear)
    if preceding > n:  # estimate is too large
        month -= 1
        preceding -= _DAYS_IN_MONTH[month] + (month == 2 and leapyear)
    n -= preceding
    assert 0 <= n < _days_in_month(year, month)

    # Now the year and month are correct, and n is the offset from the
    # start of that month:  we're done!
    return year, month, n + 1


class timedelta:
    """A timedelta object represents a duration, the difference between two dates or times."""

    # pylint: disable=too-many-arguments, too-many-locals, too-many-statements
    def __new__(
        cls,
        days=0,
        seconds=0,
        microseconds=0,
        milliseconds=0,
        minutes=0,
        hours=0,
        weeks=0,
    ):

        # Check that all inputs are ints or floats.
        if not all(
            isinstance(i, (int, float))
            for i in [days, seconds, microseconds, milliseconds, minutes, hours, weeks]
        ):
            raise TypeError("Kwargs to this function must be int or float.")

        # Final values, all integer.
        # s and us fit in 32-bit signed ints; d isn't bounded.
        d = s = us = 0

        # Normalize everything to days, seconds, microseconds.
        days += weeks * 7
        seconds += minutes * 60 + hours * 3600
        microseconds += milliseconds * 1000

        # Get rid of all fractions, and normalize s and us.
        if isinstance(days, float):
            dayfrac, days = _math.modf(days)
            daysecondsfrac, daysecondswhole = _math.modf(dayfrac * (24.0 * 3600.0))
            assert daysecondswhole == int(daysecondswhole)  # can't overflow
            s = int(daysecondswhole)
            assert days == int(days)
            d = int(days)
        else:
            daysecondsfrac = 0.0
            d = days
        assert isinstance(daysecondsfrac, float)
        assert abs(daysecondsfrac) <= 1.0
        assert isinstance(d, int)
        assert abs(s) <= 24 * 3600
        # days isn't referenced again before redefinition

        if isinstance(seconds, float):
            secondsfrac, seconds = _math.modf(seconds)
            assert seconds == int(seconds)
            seconds = int(seconds)
            secondsfrac += daysecondsfrac
            assert abs(secondsfrac) <= 2.0
        else:
            secondsfrac = daysecondsfrac
        # daysecondsfrac isn't referenced again
        assert isinstance(secondsfrac, float)
        assert abs(secondsfrac) <= 2.0

        assert isinstance(seconds, int)
        days, seconds = divmod(seconds, 24 * 3600)
        d += days
        s += int(seconds)  # can't overflow
        assert isinstance(s, int)
        assert abs(s) <= 2 * 24 * 3600
        # seconds isn't referenced again before redefinition

        usdouble = secondsfrac * 1e6
        assert abs(usdouble) < 2.1e6  # exact value not critical
        # secondsfrac isn't referenced again

        if isinstance(microseconds, float):
            microseconds = round(microseconds + usdouble)
            seconds, microseconds = divmod(microseconds, 1000000)
            days, seconds = divmod(seconds, 24 * 3600)
            d += days
            s += seconds
        else:
            microseconds = int(microseconds)
            seconds, microseconds = divmod(microseconds, 1000000)
            days, seconds = divmod(seconds, 24 * 3600)
            d += days
            s += seconds
            microseconds = round(microseconds + usdouble)
        assert isinstance(s, int)
        assert isinstance(microseconds, int)
        assert abs(s) <= 3 * 24 * 3600
        assert abs(microseconds) < 3.1e6

        # Just a little bit of carrying possible for microseconds and seconds.
        seconds, us = divmod(microseconds, 1000000)
        s += seconds
        days, s = divmod(s, 24 * 3600)
        d += days

        assert isinstance(d, int)
        assert isinstance(s, int) and 0 <= s < 24 * 3600
        assert isinstance(us, int) and 0 <= us < 1000000

        if abs(d) > 999999999:
            raise OverflowError("timedelta # of days is too large: %d" % d)

        self = object.__new__(cls)
        self._days = d
        self._seconds = s
        self._microseconds = us
        self._hashcode = -1
        return self

    # Instance attributes (read-only)
    @property
    def days(self):
        """Days, Between -999999999 and 999999999 inclusive"""
        return self._days

    @property
    def seconds(self):
        """Seconds, Between 0 and 86399 inclusive"""
        return self._seconds

    @property
    def microseconds(self):
        """Microseconds, Between 0 and 999999 inclusive"""
        return self._microseconds

    # Instance methods
    def total_seconds(self):
        """Return the total number of seconds contained in the duration."""
        return (
            (self._days * 86400 + self._seconds) * 10 ** 6 + self._microseconds
        ) / 10 ** 6

    def __repr__(self):
        args = []
        if self._days:
            args.append("days=%d" % self._days)
        if self._seconds:
            args.append("seconds=%d" % self._seconds)
        if self._microseconds:
            args.append("microseconds=%d" % self._microseconds)
        if not args:
            args.append("0")
        return "%s.%s(%s)" % (
            self.__class__.__module__,
            self.__class__.__qualname__,
            ", ".join(args),
        )

    def __str__(self):
        mm, ss = divmod(self._seconds, 60)
        hh, mm = divmod(mm, 60)
        s = "%d:%02d:%02d" % (hh, mm, ss)
        if self._days:

            def plural(n):
                return n, abs(n) != 1 and "s" or ""

            s = ("%d day%s, " % plural(self._days)) + s
        if self._microseconds:
            s = s + ".%06d" % self._microseconds
        return s

    # Supported operations
    def __neg__(self):
        return timedelta(-self._days, -self._seconds, -self._microseconds)

    def __add__(self, other):
        if isinstance(other, timedelta):
            return timedelta(
                self._days + other._days,
                self._seconds + other._seconds,
                self._microseconds + other._microseconds,
            )
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, timedelta):
            return timedelta(
                self._days - other._days,
                self._seconds - other._seconds,
                self._microseconds - other._microseconds,
            )
        return NotImplemented

    def _to_microseconds(self):
        return (self._days * (24 * 3600) + self._seconds) * 1000000 + self._microseconds

    def __floordiv__(self, other):
        if not isinstance(other, (int, timedelta)):
            return NotImplemented
        usec = self._to_microseconds()
        if isinstance(other, timedelta):
            return usec // other._to_microseconds()
        return timedelta(0, 0, usec // other)

    def __mod__(self, other):
        if isinstance(other, timedelta):
            r = self._to_microseconds() % other._to_microseconds()
            return timedelta(0, 0, r)
        return NotImplemented

    def __divmod__(self, other):
        if isinstance(other, timedelta):
            q, r = divmod(self._to_microseconds(), other._to_microseconds())
            return q, timedelta(0, 0, r)
        return NotImplemented

    def __mul__(self, other):
        if isinstance(other, int):
            # for CPython compatibility, we cannot use
            # our __class__ here, but need a real timedelta
            return timedelta(
                self._days * other, self._seconds * other, self._microseconds * other
            )
        if isinstance(other, float):
            # a, b = other.as_integer_ratio()
            # return self * a / b
            usec = self._to_microseconds()
            return timedelta(0, 0, round(usec * other))
        return NotImplemented

    __rmul__ = __mul__

    # Supported comparisons
    def __eq__(self, other):
        if not isinstance(other, timedelta):
            return False
        return self._cmp(other) == 0

    def __ne__(self, other):
        if not isinstance(other, timedelta):
            return True
        return self._cmp(other) != 0

    def __le__(self, other):
        if not isinstance(other, timedelta):
            _cmperror(self, other)
        return self._cmp(other) <= 0

    def __lt__(self, other):
        if not isinstance(other, timedelta):
            _cmperror(self, other)
        return self._cmp(other) < 0

    def __ge__(self, other):
        if not isinstance(other, timedelta):
            _cmperror(self, other)
        return self._cmp(other) >= 0

    def __gt__(self, other):
        if not isinstance(other, timedelta):
            _cmperror(self, other)
        return self._cmp(other) > 0

    # pylint: disable=no-self-use, protected-access
    def _cmp(self, other):
        assert isinstance(other, timedelta)
        return _cmp(self._getstate(), other._getstate())

    def __bool__(self):
        return self._days != 0 or self._seconds != 0 or self._microseconds != 0

    def _getstate(self):
        return (self._days, self._seconds, self._microseconds)


# pylint: disable=no-self-use
class tzinfo:
    """This is an abstract base class, meaning that this class should not
    be instantiated directly. Define a subclass of tzinfo to capture information
    about a particular time zone.

    """

    def utcoffset(self, dt):
        """Return offset of local time from UTC, as a timedelta
        object that is positive east of UTC.

        """
        raise NotImplementedError("tzinfo subclass must override utcoffset()")

    def tzname(self, dt):
        """Return the time zone name corresponding to the datetime object dt, as a string."""
        raise NotImplementedError("tzinfo subclass must override tzname()")

    # tzinfo is an abstract base class, disabling for self._offset
    # pylint: disable=no-member
    def fromutc(self, dt):
        "datetime in UTC -> datetime in local time."

        if not isinstance(dt, datetime):
            raise TypeError("fromutc() requires a datetime argument")
        if dt.tzinfo is not self:
            raise ValueError("dt.tzinfo is not self")

        dtoff = dt.utcoffset()
        if dtoff is None:
            raise ValueError("fromutc() requires a non-None utcoffset() " "result")
        return dt + self._offset


class date:
    """A date object represents a date (year, month and day) in an idealized calendar,
    the current Gregorian calendar indefinitely extended in both directions.
    Objects of this type are always naive.

    """

    def __new__(cls, year, month, day):
        """Creates a new date object.

        :param int year: Year within range, MINYEAR <= year <= MAXYEAR
        :param int month: Month within range, 1 <= month <= 12
        :param int day: Day within range, 1 <= day <= number of days in the given month and year
        """
        _check_date_fields(year, month, day)
        self = object.__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._hashcode = -1
        return self

    # Instance attributes (read-only)
    @property
    def year(self):
        """Between MINYEAR and MAXYEAR inclusive."""
        return self._year

    @property
    def month(self):
        """Between 1 and 12 inclusive."""
        return self._month

    @property
    def day(self):
        """Between 1 and the number of days in the given month of the given year."""
        return self._day

    # Class Methods
    @classmethod
    def fromtimestamp(cls, t):
        """Return the local date corresponding to the POSIX timestamp,
        such as is returned by time.time().
        """
        tm_struct = _time.localtime(t)
        return cls(tm_struct[0], tm_struct[1], tm_struct[2])

    @classmethod
    def fromordinal(cls, ordinal):
        """Return the date corresponding to the proleptic Gregorian ordinal,
        where January 1 of year 1 has ordinal 1.

        """
        if not ordinal >= 1:
            raise ValueError("ordinal must be >=1")
        y, m, d = _ord2ymd(ordinal)
        return cls(y, m, d)

    @classmethod
    def today(cls):
        """Return the current local date."""
        return cls.fromtimestamp(_time.time())

    # Instance Methods
    def replace(self, year=None, month=None, day=None):
        """Return a date with the same value, except for those parameters
        given new values by whichever keyword arguments are specified.
        If no keyword arguments are specified - values are obtained from
        datetime object.

        """
        raise NotImplementedError()

    def timetuple(self):
        """Return a time.struct_time such as returned by time.localtime().
        The hours, minutes and seconds are 0, and the DST flag is -1.

        """
        return _build_struct_time(self._year, self._month, self._day, 0, 0, 0, -1)

    def toordinal(self):
        """Return the proleptic Gregorian ordinal of the date, where January 1 of
        year 1 has ordinal 1.
        """
        return _ymd2ord(self._year, self._month, self._day)

    def weekday(self):
        """Return the day of the week as an integer, where Monday is 0 and Sunday is 6."""
        return (self.toordinal() + 6) % 7

    # ISO date
    def isoweekday(self):
        """Return the day of the week as an integer, where Monday is 1 and Sunday is 7."""
        return self.toordinal() % 7 or 7

    def isoformat(self):
        """Return a string representing the date in ISO 8601 format, YYYY-MM-DD:"""
        return "%04d-%02d-%02d" % (self._year, self._month, self._day)

    # For a date d, str(d) is equivalent to d.isoformat()
    __str__ = isoformat

    def __repr__(self):
        """Convert to formal string, for repr()."""
        return "%s(%d, %d, %d)" % (
            "datetime." + self.__class__.__name__,
            self._year,
            self._month,
            self._day,
        )

    # Supported comparisons
    def __eq__(self, other):
        if isinstance(other, date):
            return self._cmp(other) == 0
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, date):
            return self._cmp(other) <= 0
        return NotImplemented

    def __lt__(self, other):
        if isinstance(other, date):
            return self._cmp(other) < 0
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, date):
            return self._cmp(other) >= 0
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, date):
            return self._cmp(other) > 0
        return NotImplemented

    def _cmp(self, other):
        assert isinstance(other, date)
        y, m, d = self._year, self._month, self._day
        y2, m2, d2 = other.year, other.month, other.day
        return _cmp((y, m, d), (y2, m2, d2))

    def __hash__(self):
        if self._hashcode == -1:
            self._hashcode = hash(self._getstate())
        return self._hashcode

    # Pickle support
    def _getstate(self):
        yhi, ylo = divmod(self._year, 256)
        return (bytes([yhi, ylo, self._month, self._day]),)

    def _setstate(self, string):
        yhi, ylo, self._month, self._day = string
        self._year = yhi * 256 + ylo


class timezone(tzinfo):
    """The timezone class is a subclass of tzinfo, each instance of which represents a
    timezone defined by a fixed offset from UTC.

    Objects of this class cannot be used to represent timezone information in the locations
    where different offsets are used in different days of the year or where historical changes
    have been made to civil time.

    """

    # Sentinel value to disallow None
    _Omitted = object()

    def __new__(cls, offset, name=_Omitted):
        if not isinstance(offset, timedelta):
            raise TypeError("offset must be a timedelta")
        if name is cls._Omitted:
            if not offset:
                return cls.utc
            name = None
        elif not isinstance(name, str):
            raise TypeError("name must be a string")
        if not cls.minoffset <= offset <= cls.maxoffset:
            raise ValueError(
                "offset must be a timedelta"
                " strictly between -timedelta(hours=24) and"
                " timedelta(hours=24)."
            )
        if offset.microseconds != 0 or offset.seconds % 60 != 0:
            raise ValueError(
                "offset must be a timedelta" " representing a whole number of minutes"
            )
        cls._offset = offset
        cls._name = name
        return cls._create(offset, name)

    # pylint: disable=protected-access, bad-super-call
    @classmethod
    def _create(cls, offset, name=None):
        """High-level creation for a timezone object."""
        self = super(tzinfo, cls).__new__(cls)
        self._offset = offset
        self._name = name
        return self

    # Instance methods
    def utcoffset(self, dt):
        if isinstance(dt, datetime) or dt is None:
            return self._offset
        raise TypeError("utcoffset() argument must be a datetime instance" " or None")

    def tzname(self, dt):
        if isinstance(dt, datetime) or dt is None:
            if self._name is None:
                return self._name_from_offset(self._offset)
            return self._name
        raise TypeError("tzname() argument must be a datetime instance" " or None")

    # Comparison to other timezone objects
    def __eq__(self, other):
        if not isinstance(other, timezone):
            return False
        return self._offset == other._offset

    def __hash__(self):
        return hash(self._offset)

    def __repr__(self):
        """Convert to formal string, for repr()."""
        if self is self.utc:
            return "datetime.timezone.utc"
        if self._name is None:
            return "%s(%r)" % ("datetime." + self.__class__.__name__, self._offset)
        return "%s(%r, %r)" % (
            "datetime." + self.__class__.__name__,
            self._offset,
            self._name,
        )

    def __str__(self):
        return self.tzname(None)

    @staticmethod
    def _name_from_offset(delta):
        if delta < timedelta(0):
            sign = "-"
            delta = -delta
        else:
            sign = "+"
        hours, rest = divmod(delta, timedelta(hours=1))
        minutes = rest // timedelta(minutes=1)
        return "UTC{}{:02d}:{:02d}".format(sign, hours, minutes)

    maxoffset = timedelta(hours=23, minutes=59)
    minoffset = -maxoffset


class time:
    """A time object represents a (local) time of day, independent of
    any particular day, and subject to adjustment via a tzinfo object.

    """

    # pylint: disable=redefined-outer-name
    def __new__(cls, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0):
        _check_time_fields(hour, minute, second, microsecond, fold)
        _check_tzinfo_arg(tzinfo)
        self = object.__new__(cls)
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        self._fold = fold
        self._hashcode = -1
        return self

    # Instance attributes (read-only)
    @property
    def hour(self):
        """In range(24)."""
        return self._hour

    @property
    def minute(self):
        """In range(60)."""
        return self._minute

    @property
    def second(self):
        """In range(60)."""
        return self._second

    @property
    def microsecond(self):
        """In range(1000000)."""
        return self._microsecond

    @property
    def fold(self):
        """Fold."""
        return self._fold

    @property
    def tzinfo(self):
        """The object passed as the tzinfo argument to
        the time constructor, or None if none was passed.
        """
        return self._tzinfo

    # Instance methods
    def isoformat(self, timespec="auto"):
        """Return a string representing the time in ISO 8601 format, one of:
        HH:MM:SS.ffffff, if microsecond is not 0

        HH:MM:SS, if microsecond is 0

        HH:MM:SS.ffffff+HH:MM[:SS[.ffffff]], if utcoffset() does not return None

        HH:MM:SS+HH:MM[:SS[.ffffff]], if microsecond is 0 and utcoffset() does not return None

        """
        s = _format_time(
            self._hour, self._minute, self._second, self._microsecond, timespec
        )
        tz = self._tzstr()
        if tz:
            s += tz
        return s

    # For a time t, str(t) is equivalent to t.isoformat()
    __str__ = isoformat

    def utcoffset(self):
        """Return the timezone offset in minutes east of UTC (negative west of
        UTC)."""
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.utcoffset(None)
        _check_utc_offset("utcoffset", offset)
        return offset

    def tzname(self):
        """Return the timezone name.

        Note that the name is 100% informational -- there's no requirement that
        it mean anything in particular. For example, "GMT", "UTC", "-500",
        "-5:00", "EDT", "US/Eastern", "America/New York" are all valid replies.
        """
        if self._tzinfo is None:
            return None
        name = self._tzinfo.tzname(None)
        _check_tzname(name)
        return name

    # Standard conversions and comparisons
    def __eq__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other, allow_mixed=True) == 0

    def __le__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other) <= 0

    def __lt__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other) < 0

    def __ge__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other) >= 0

    def __gt__(self, other):
        if not isinstance(other, time):
            return NotImplemented
        return self._cmp(other) > 0

    def _cmp(self, other, allow_mixed=False):
        assert isinstance(other, time)
        mytz = self._tzinfo
        ottz = other.tzinfo
        myoff = otoff = None

        if mytz is ottz:
            base_compare = True
        else:
            myoff = self.utcoffset()
            otoff = other.utcoffset()
            base_compare = myoff == otoff

        if base_compare:
            return _cmp(
                (self._hour, self._minute, self._second, self._microsecond),
                (other.hour, other.minute, other.second, other.microsecond),
            )
        if myoff is None or otoff is None:
            if not allow_mixed:
                raise TypeError("cannot compare naive and aware times")
            return 2  # arbitrary non-zero value
        myhhmm = self._hour * 60 + self._minute - myoff // timedelta(minutes=1)
        othhmm = other.hour * 60 + other.minute - otoff // timedelta(minutes=1)
        return _cmp(
            (myhhmm, self._second, self._microsecond),
            (othhmm, other.second, other.microsecond),
        )

    def __hash__(self):
        """Hash."""
        if self._hashcode == -1:
            t = self
            tzoff = t.utcoffset()
            if not tzoff:  # zero or None
                self._hashcode = hash(t._getstate()[0])
            else:
                h, m = divmod(
                    timedelta(hours=self.hour, minutes=self.minute) - tzoff,
                    timedelta(hours=1),
                )
                assert not m % timedelta(minutes=1), "whole minute"
                m //= timedelta(minutes=1)
                if 0 <= h < 24:
                    self._hashcode = hash(time(h, m, self.second, self.microsecond))
                else:
                    self._hashcode = hash((h, m, self.second, self.microsecond))
        return self._hashcode

    def _tzstr(self, sep=":"):
        """Return formatted timezone offset (+xx:xx) or None."""
        off = self.utcoffset()
        if off is not None:
            if off.days < 0:
                sign = "-"
                off = -1 * off
            else:
                sign = "+"
            hh, mm = divmod(off, timedelta(hours=1))
            assert not mm % timedelta(minutes=1), "whole minute"
            mm //= timedelta(minutes=1)
            assert 0 <= hh < 24
            off = "%s%02d%s%02d" % (sign, hh, sep, mm)
        return off

    def __format__(self, fmt):
        if not isinstance(fmt, str):
            raise TypeError("must be str, not %s" % type(fmt).__name__)
        return str(self)

    def __repr__(self):
        """Convert to formal string, for repr()."""
        if self._microsecond != 0:
            s = ", %d, %d" % (self._second, self._microsecond)
        elif self._second != 0:
            s = ", %d" % self._second
        else:
            s = ""
        s = "%s(%d, %d%s)" % (
            "datetime." + self.__class__.__name__,
            self._hour,
            self._minute,
            s,
        )
        if self._tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        return s

    # Pickle support
    def _getstate(self, protocol=3):
        us2, us3 = divmod(self._microsecond, 256)
        us1, us2 = divmod(us2, 256)
        h = self._hour
        if self._fold and protocol > 3:
            h += 128
        basestate = bytes([h, self._minute, self._second, us1, us2, us3])
        if not self._tzinfo is None:
            return (basestate, self._tzinfo)
        return (basestate,)


# pylint: disable=too-many-instance-attributes, too-many-public-methods
class datetime(date):
    """A datetime object is a single object containing all the information
    from a date object and a time object. Like a date object, datetime assumes
    the current Gregorian calendar extended in both directions; like a time object,
    datetime assumes there are exactly 3600*24 seconds in every day.

    """

    # pylint: disable=redefined-outer-name
    def __new__(
        cls,
        year,
        month,
        day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
        tzinfo=None,
        *,
        fold=0
    ):
        _check_date_fields(year, month, day)
        _check_time_fields(hour, minute, second, microsecond, fold)
        _check_tzinfo_arg(tzinfo)

        self = object.__new__(cls)
        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond
        self._tzinfo = tzinfo
        self._fold = fold
        self._hashcode = -1
        return self

    # Read-only instance attributes
    @property
    def year(self):
        """Between MINYEAR and MAXYEAR inclusive."""
        return self._year

    @property
    def month(self):
        """Between 1 and 12 inclusive."""
        return self._month

    @property
    def day(self):
        """Between 1 and the number of days in the given month of the given year."""
        return self._day

    @property
    def hour(self):
        """In range(24)."""
        return self._hour

    @property
    def minute(self):
        """In range (60)"""
        return self._minute

    @property
    def second(self):
        """In range (60)"""
        return self._second

    @property
    def microsecond(self):
        """In range (1000000)"""
        return self._microsecond

    @property
    def tzinfo(self):
        """The object passed as the tzinfo argument to the datetime constructor,
        or None if none was passed.
        """
        return self._tzinfo

    # Class methods

    # pylint: disable=protected-access
    @classmethod
    def _fromtimestamp(cls, t, utc, tz):
        """Construct a datetime from a POSIX timestamp (like time.time()).
        A timezone info object may be passed in as well.
        """
        frac, t = _math.modf(t)
        us = round(frac * 1e6)
        if us >= 1000000:
            t += 1
            us -= 1000000
        elif us < 0:
            t -= 1
            us += 1000000

        if utc:
            raise NotImplementedError(
                "CircuitPython does not currently implement time.gmtime."
            )
        converter = _time.localtime
        struct_time = converter(t)
        ss = min(struct_time[5], 59)  # clamp out leap seconds if the platform has them
        result = cls(
            struct_time[0],
            struct_time[1],
            struct_time[2],
            struct_time[3],
            struct_time[4],
            ss,
            us,
            tz,
        )
        if tz is not None:
            result = tz.fromutc(result)
        return result

    ## pylint: disable=arguments-differ
    @classmethod
    def fromtimestamp(cls, timestamp, tz=None):
        return cls._fromtimestamp(timestamp, tz is not None, tz)

    @classmethod
    def now(cls, timezone=None):
        """Return the current local date and time."""
        return cls.fromtimestamp(_time.time(), tz=timezone)

    @classmethod
    def utcfromtimestamp(cls, timestamp):
        """Return the UTC datetime corresponding to the POSIX timestamp, with tzinfo None"""
        return cls._fromtimestamp(timestamp, True, None)

    @classmethod
    def combine(cls, date, time, tzinfo=True):
        """Return a new datetime object whose date components are equal to the
        given date object’s, and whose time components are equal to the given time object’s.

        """
        if not isinstance(date, _date_class):
            raise TypeError("date argument must be a date instance")
        if not isinstance(time, _time_class):
            raise TypeError("time argument must be a time instance")
        if tzinfo is True:
            tzinfo = time.tzinfo
        return cls(
            date.year,
            date.month,
            date.day,
            time.hour,
            time.minute,
            time.second,
            time.microsecond,
            tzinfo,
            fold=time.fold,
        )

    # Instance methods
    def _mktime(self):
        """Return integer POSIX timestamp."""
        epoch = datetime(1970, 1, 1)
        max_fold_seconds = 24 * 3600
        t = (self - epoch) // timedelta(0, 1)

        def local(u):
            y, m, d, hh, mm, ss = _time.localtime(u)[:6]
            return (datetime(y, m, d, hh, mm, ss) - epoch) // timedelta(0, 1)

        # Our goal is to solve t = local(u) for u.
        a = local(t) - t
        u1 = t - a
        t1 = local(u1)
        if t1 == t:
            # We found one solution, but it may not be the one we need.
            # Look for an earlier solution (if `fold` is 0), or a
            # later one (if `fold` is 1).
            u2 = u1 + (-max_fold_seconds, max_fold_seconds)[self._fold]
            b = local(u2) - u2
            if a == b:
                return u1
        else:
            b = t1 - u1
            assert a != b
        u2 = t - b
        t2 = local(u2)
        if t2 == t:
            return u2
        if t1 == t:
            return u1
        # We have found both offsets a and b, but neither t - a nor t - b is
        # a solution.  This means t is in the gap.
        return (max, min)[self._fold](u1, u2)

    def date(self):
        """Return date object with same year, month and day."""
        return _date_class(self._year, self._month, self._day)

    def time(self):
        """Return time object with same hour, minute, second, microsecond and fold.
        tzinfo is None. See also method timetz().

        """
        return _time_class(
            self._hour, self._minute, self._second, self._microsecond, fold=self._fold
        )

    def dst(self):
        """If tzinfo is None, returns None, else returns self.tzinfo.dst(self),
        and raises an exception if the latter doesn’t return None or a timedelta
        object with magnitude less than one day.

        """
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.dst(self)
        _check_utc_offset("dst", offset)
        return offset

    def timetuple(self):
        """Return local time tuple compatible with time.localtime()."""
        dst = self.dst()
        if dst is None:
            dst = -1
        elif dst:
            dst = 1
        else:
            dst = 0
        return _build_struct_time(
            self.year, self.month, self.day, self.hour, self.minute, self.second, dst
        )

    def utcoffset(self):
        """If tzinfo is None, returns None, else returns
        self.tzinfo.utcoffset(self), and raises an exception
        if the latter doesn’t return None or a timedelta object
        with magnitude less than one day.

        """
        if self._tzinfo is None:
            return None
        offset = self._tzinfo.utcoffset(self)
        _check_utc_offset("utcoffset", offset)
        return offset

    def toordinal(self):
        """Return the proleptic Gregorian ordinal of the date."""
        return _ymd2ord(self._year, self._month, self._day)

    def timestamp(self):
        "Return POSIX timestamp as float"
        if not self._tzinfo is None:
            return (self - _EPOCH).total_seconds()
        s = self._mktime()
        return s + self.microsecond / 1e6

    def weekday(self):
        """Return the day of the week as an integer, where Monday is 0 and Sunday is 6."""
        return (self.toordinal() + 6) % 7

    def ctime(self):
        "Return string representing the datetime."
        weekday = self.toordinal() % 7 or 7
        return "%s %s %2d %02d:%02d:%02d %04d" % (
            _DAYNAMES[weekday],
            _MONTHNAMES[self._month],
            self._day,
            self._hour,
            self._minute,
            self._second,
            self._year,
        )

    def __repr__(self):
        """Convert to formal string, for repr()."""
        L = [
            self._year,
            self._month,
            self._day,  # These are never zero
            self._hour,
            self._minute,
            self._second,
            self._microsecond,
        ]
        if L[-1] == 0:
            del L[-1]
        if L[-1] == 0:
            del L[-1]
        s = ", ".join(map(str, L))
        s = "%s(%s)" % ("datetime." + self.__class__.__name__, s)
        if self._tzinfo is not None:
            assert s[-1:] == ")"
            s = s[:-1] + ", tzinfo=%r" % self._tzinfo + ")"
        return s

    def isoformat(self, sep="T", timespec="auto"):
        """Return a string representing the date and time in
        ISO8601 format.

        """
        s = "%04d-%02d-%02d%c" % (
            self._year,
            self._month,
            self._day,
            sep,
        ) + _format_time(
            self._hour, self._minute, self._second, self._microsecond, timespec
        )

        off = self.utcoffset()
        tz = _format_offset(off)
        if tz:
            s += tz

        return s

    def __str__(self):
        "Convert to string, for str()."
        return self.isoformat(sep=" ")

    def replace(
        self,
        year=None,
        month=None,
        day=None,
        hour=None,
        minute=None,
        second=None,
        microsecond=None,
        tzinfo=True,
        *,
        fold=None
    ):
        """Return a datetime with the same attributes,
        except for those attributes given new values by
        whichever keyword arguments are specified.

        """
        if year is None:
            year = self.year
        if month is None:
            month = self.month
        if day is None:
            day = self.day
        if hour is None:
            hour = self.hour
        if minute is None:
            minute = self.minute
        if second is None:
            second = self.second
        if microsecond is None:
            microsecond = self.microsecond
        if tzinfo is True:
            tzinfo = self.tzinfo
        if fold is None:
            fold = self._fold
        return type(self)(
            year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold
        )

    # Comparisons of datetime objects.
    def __eq__(self, other):
        if not isinstance(other, datetime):
            return False
        return self._cmp(other, allow_mixed=True) == 0

    def __le__(self, other):
        if not isinstance(other, datetime):
            _cmperror(self, other)
        return self._cmp(other) <= 0

    def __lt__(self, other):
        if not isinstance(other, datetime):
            _cmperror(self, other)
        return self._cmp(other) < 0

    def __ge__(self, other):
        if not isinstance(other, datetime):
            _cmperror(self, other)
        return self._cmp(other) >= 0

    def __gt__(self, other):
        if not isinstance(other, datetime):
            _cmperror(self, other)
        return self._cmp(other) > 0

    def _cmp(self, other, allow_mixed=False):
        assert isinstance(other, datetime)
        mytz = self._tzinfo
        ottz = other.tzinfo
        myoff = otoff = None

        if mytz is ottz:
            base_compare = True
        else:
            myoff = self.utcoffset()
            otoff = other.utcoffset()
            # Assume that allow_mixed means that we are called from __eq__
            if allow_mixed:
                if myoff != self.replace(fold=not self._fold).utcoffset():
                    return 2
                if otoff != other.replace(fold=not other.fold).utcoffset():
                    return 2
            base_compare = myoff == otoff

        if base_compare:
            return _cmp(
                (
                    self._year,
                    self._month,
                    self._day,
                    self._hour,
                    self._minute,
                    self._second,
                    self._microsecond,
                ),
                (
                    other.year,
                    other.month,
                    other.day,
                    other.hour,
                    other.minute,
                    other.second,
                    other.microsecond,
                ),
            )
        if myoff is None or otoff is None:
            if not allow_mixed:
                raise TypeError("cannot compare naive and aware datetimes")
            return 2  # arbitrary non-zero value
        diff = self - other  # this will take offsets into account
        if diff.days < 0:
            return -1
        return 1 if diff else 0

    def __add__(self, other):
        "Add a datetime and a timedelta."
        if not isinstance(other, timedelta):
            return NotImplemented
        delta = timedelta(
            self.toordinal(),
            hours=self._hour,
            minutes=self._minute,
            seconds=self._second,
            microseconds=self._microsecond,
        )
        delta += other
        hour, rem = divmod(delta._seconds, 3600)
        minute, second = divmod(rem, 60)
        if 0 < delta._days <= _MAXORDINAL:
            return type(self).combine(
                date.fromordinal(delta._days),
                time(hour, minute, second, delta._microseconds, tzinfo=self._tzinfo),
            )
        raise OverflowError("result out of range")

    __radd__ = __add__

    def __sub__(self, other):
        "Subtract two datetimes, or a datetime and a timedelta."
        if not isinstance(other, datetime):
            if isinstance(other, timedelta):
                return self + -other
            return NotImplemented

        days1 = self.toordinal()
        days2 = other.toordinal()
        secs1 = self._second + self._minute * 60 + self._hour * 3600
        secs2 = other._second + other._minute * 60 + other._hour * 3600
        base = timedelta(
            days1 - days2, secs1 - secs2, self._microsecond - other._microsecond
        )
        if self._tzinfo is other._tzinfo:
            return base
        myoff = self.utcoffset()
        otoff = other.utcoffset()
        if myoff == otoff:
            return base
        if myoff is None or otoff is None:
            raise TypeError("cannot mix naive and timezone-aware time")
        return base + otoff - myoff

    def __hash__(self):
        if self._hashcode == -1:
            t = self
            tzoff = t.utcoffset()
            if tzoff is None:
                self._hashcode = hash(t._getstate()[0])
            else:
                days = _ymd2ord(self.year, self.month, self.day)
                seconds = self.hour * 3600 + self.minute * 60 + self.second
                self._hashcode = hash(
                    timedelta(days, seconds, self.microsecond) - tzoff
                )
        return self._hashcode

    def _getstate(self):
        protocol = 3
        yhi, ylo = divmod(self._year, 256)
        us2, us3 = divmod(self._microsecond, 256)
        us1, us2 = divmod(us2, 256)
        m = self._month
        if self._fold and protocol > 3:
            m += 128
        basestate = bytes(
            [
                yhi,
                ylo,
                m,
                self._day,
                self._hour,
                self._minute,
                self._second,
                us1,
                us2,
                us3,
            ]
        )
        if not self._tzinfo is None:
            return (basestate, self._tzinfo)
        return (basestate,)


# Module exports
# pylint: disable=protected-access
timezone.utc = timezone._create(timedelta(0))
timezone.min = timezone._create(timezone.minoffset)
timezone.max = timezone._create(timezone.maxoffset)
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
_date_class = date
_time_class = time
