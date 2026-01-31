from geoexpress.core.base import GeoExpressCommand

_meta = GeoExpressCommand("mrsidgeometa")
_info = GeoExpressCommand("mrsidgeoinfo")


def set_metadata(image: str, key: str, value: str) -> None:
    """
    Set USER metadata on a MrSID file.

    Example:
        set_metadata("file.sid", "Author", "Vibudh")
    """
    _meta.run([
        "-f", image,
        "-d", f"{key}={value}"
    ])


def get_metadata(image: str) -> str:
    """
    Read metadata from a MrSID file.

    Returns raw metadata text (mrsidgeoinfo -meta).
    """
    return _info.run([
        "-meta",
        image
    ])
