import datetime

# NTP timestamps are in units of seconds since the NTP epoch
# See leap-seconds.list for further details.
NTP_EPOCH = datetime.datetime(1900,1,1,0,0,0)

def sec_since_NTP_epoch(dt):
    """Return the number of seconds since the NTP epoch."""
    return (dt-NTP_EPOCH).total_seconds()

def load_leapsecond_table(f="/usr/share/zoneinfo/leap-seconds.list"):
    """"
    Loads leap second table from system.

    The default file location is appropriate for Ubuntu and is provided by
    the tzdata package.  Refer to the leap-seconds.list file for formatting
    information.

    Parameters
    ----------
    f : string
      Path to a leap-seconds.list file

    Returns: List of tuples in chronological order each containing an
    epoch start time and number of leap seconds applicable for that epoch.
    """

    # Check the expiration date in the file
    with open(f,'r') as fp:
        for line in fp:
            if line[0:2] != "#@":
                continue

            expiration_time = int(line.split('\t')[-1])
            now = sec_since_NTP_epoch(datetime.datetime.now())

            if expiration_time<now:
                raise UserWarning("leap-seconds.list file has expired, update tzdata")

    # Load the load the table
    with open(f,'r') as fp:
        table = []
        for line in fp:
            if line[0]=="#":
                continue
            raw = line.split('\t')
            table.append( (int(raw[0]), int(raw[1])) )

    # Add the expiration time to the end of the table
    table.append( (expiration_time, None) )

    return table

def get_gpst_leap_seconds(dt):
    """Returns the number of leap seconds at the time provided."""

    # Load leap second data from system tzdata file
    lstable = load_leapsecond_table()

    t = sec_since_NTP_epoch(dt)

    ls = None
    for epoch_start,leapseconds in lstable:
        if t>=epoch_start:
            ls = leapseconds

    # Raise warning if specified time is after expiry date of leap second table
    if ls==None:
        raise UserWarning("Specified datetime is after expiry time of leap second table.")

    # GPS leap seconds relative to a Jan 1 1980, where TAI-UTC was 19 seconds.
    gps_leap_seconds = ls - 19

    return datetime.timedelta(seconds = gps_leap_seconds)

def datetime_to_tow(t, mod1024 = True):
    """
    Convert a Python datetime object to GPS Week and Time Of Week.
    Does *not* convert from UTC to GPST.
    Fractional seconds are supported.

    Parameters
    ----------
    t : datetime
      A time to be converted, on the GPST timescale.
    mod1024 : bool, optional
      If True (default), the week number will be output in 10-bit form.

    Returns
    -------
    week, tow : tuple (int, float)
      The GPS week number and time-of-week.
    """
    # DateTime to GPS week and TOW
    wk_ref = datetime.datetime(2014, 2, 16, 0, 0, 0, 0, None)
    refwk = 1780
    wk = (t - wk_ref).days / 7 + refwk
    tow = ((t - wk_ref) - datetime.timedelta((wk - refwk) * 7.0)).total_seconds()
    wk = wk % 1024
    return wk, tow

def gpst_to_utc(t_gpst):
    """
    Convert a time on the GPST timescale (continuous, no leap seconds) to
    a time on the UTC timescale (has leap seconds)

    Parameters
    ---------
    t_gpst : datetime

    Returns
    -------
    t_utc : datetime
    """
    return t_gpst - get_gpst_leap_seconds(t_gpst)

def utc_to_gpst(t_utc):
    """
    Convert a time on the UTC timescale (has leap seconds) to
    a time on the GPST timescale (continuous, no leap seconds)

    Parameters
    ---------
    t_utc : datetime

    Returns
    -------
    t_gpst : datetime
    """
    # TODO: there may be an unhandled corner case here for conversions
    # where the GPST-to-UTCT interval spans a leap second.

    return t_utc + get_gpst_leap_seconds(t_utc)
