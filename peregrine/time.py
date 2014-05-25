import datetime

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
    t_utc = t_gpst - datetime.timedelta(seconds = 16)
    if t_utc <= datetime.datetime(2012, 7, 1) or \
       t_utc >= datetime.datetime(2015, 1, 1):
        raise ValueError("Don't know how many leap seconds to use.  " +
                         "Please implement something better in gpst_to_utc()")
    return t_utc

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
    t_gpst = t_utc + datetime.timedelta(seconds = 16)
    if t_utc <= datetime.datetime(2012, 7, 1) or \
       t_utc >= datetime.datetime(2015, 1, 1):
        raise ValueError("Don't know how many leap seconds to use.  " +
                         "Please implement something better in utc_to_gpst()")
    return t_gpst
