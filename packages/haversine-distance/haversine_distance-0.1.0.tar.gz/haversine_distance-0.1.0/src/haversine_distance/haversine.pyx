from libc.math cimport sin, cos, asin, sqrt

cdef double EARTH_RADIUS_M = 6371000.0
cdef double DEG_TO_RAD = 0.017453292519943295  # pi / 180


cpdef double haversine(double lon1, double lat1,
                       double lon2, double lat2):
    """
    Compute geodetic distance in meters using the Haversine formula.

    Parameters
    ----------
    lon1, lat1 : float
        Longitude and latitude of the first point in degrees.
    lon2, lat2 : float
        Longitude and latitude of the second point in degrees.

    Returns
    -------
    float
        Distance in meters.
    """

    cdef double dlon, dlat, a, c

    lon1 *= DEG_TO_RAD
    lat1 *= DEG_TO_RAD
    lon2 *= DEG_TO_RAD
    lat2 *= DEG_TO_RAD

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat * 0.5) ** 2 + cos(lat1) * cos(lat2) * sin(dlon * 0.5) ** 2
    c = 2.0 * asin(sqrt(a))

    return EARTH_RADIUS_M * c
