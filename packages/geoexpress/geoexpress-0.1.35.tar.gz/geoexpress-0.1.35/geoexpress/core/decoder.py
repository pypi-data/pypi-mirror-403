from typing import Optional
from geoexpress.core.base import GeoExpressCommand

_decoder = GeoExpressCommand("mrsidgeodecode")


def decode(
    input: str,
    output: str,
    password: Optional[str] = None
) -> str:
    """
    Decode MrSID to GeoTIFF.
    """

    args = [
        "-i", input,
        "-o", output
    ]

    if password:
        args.extend(["-pwd", password])

    return _decoder.run(args)
