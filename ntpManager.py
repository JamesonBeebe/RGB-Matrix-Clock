import socketpool
import struct
import time
import wifi

NTP_HOST = "pool.ntp.org"
NTP_PORT = 123
NTP_DELTA = 2208988800
SECONDS_PER_DAY = 86400


def _isLeap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _daysBeforeYear(year):
    year -= 1
    return year * 365 + year // 4 - year // 100 + year // 400


def _daysBeforeMonth(year, month):
    daysBeforeMonth = (0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
    days = daysBeforeMonth[month]
    if month > 2 and _isLeap(year):
        days += 1
    return days


def _epochSeconds(year, month, day, hour):
    days = _daysBeforeYear(year) - _daysBeforeYear(1970)
    days += _daysBeforeMonth(year, month) + day - 1
    return days * SECONDS_PER_DAY + hour * 3600


def _weekday(year, month, day):
    days = _daysBeforeYear(year) + _daysBeforeMonth(year, month) + day
    return (days + 6) % 7


def _firstSunday(year, month):
    firstWeekday = _weekday(year, month, 1)
    if firstWeekday == 6:
        return 1
    return 7 - firstWeekday


def _usEasternOffset(utcSeconds):
    utcTime = time.localtime(utcSeconds)
    year = utcTime.tm_year
    dstStartDay = _firstSunday(year, 3) + 7
    dstEndDay = _firstSunday(year, 11)
    dstStartUtc = _epochSeconds(year, 3, dstStartDay, 7)
    dstEndUtc = _epochSeconds(year, 11, dstEndDay, 6)
    if dstStartUtc <= utcSeconds < dstEndUtc:
        return -4
    return -5


def getTimezoneOffset(utcSeconds, timezoneName, defaultOffset):
    if timezoneName == "US/Eastern":
        return _usEasternOffset(utcSeconds)
    return defaultOffset


def getLocalTime(timezoneOffsetHours, timezoneName=None):
    if not wifi.radio.connected:
        return None

    pool = socketpool.SocketPool(wifi.radio)
    address = pool.getaddrinfo(NTP_HOST, NTP_PORT)[0][-1]
    packet = bytearray(48)
    packet[0] = 0x1B
    response = bytearray(48)

    socket = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
    socket.settimeout(5)
    try:
        socket.sendto(packet, address)
        socket.recv_into(response)
    finally:
        socket.close()

    utcSeconds = struct.unpack("!I", response[40:44])[0] - NTP_DELTA
    offset = getTimezoneOffset(utcSeconds, timezoneName, timezoneOffsetHours)
    return time.localtime(utcSeconds + int(offset * 3600))
