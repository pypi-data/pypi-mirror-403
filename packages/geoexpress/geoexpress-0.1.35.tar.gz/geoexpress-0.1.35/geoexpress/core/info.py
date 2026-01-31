from geoexpress.core.base import GeoExpressCommand

_info = GeoExpressCommand("mrsidgeoinfo")


def info_raw(path: str) -> str:
    return _info.run([path])


def info_parsed(path: str) -> dict:
    raw = info_raw(path)
    parsed = {}

    for line in raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            parsed[k.strip()] = v.strip()

    return {
        "raw": raw,
        "parsed": parsed
    }
