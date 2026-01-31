class GeoExpressError(Exception):
    """Base exception for geoexpress SDK"""


class GeoExpressNotInstalled(GeoExpressError):
    pass


class GeoExpressLicenseError(GeoExpressError):
    pass


class GeoExpressCommandError(GeoExpressError):
    pass
