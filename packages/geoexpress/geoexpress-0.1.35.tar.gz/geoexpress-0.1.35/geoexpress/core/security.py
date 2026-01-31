import os
import tempfile

from geoexpress.core.decoder import decode
from geoexpress.core.encoder import encode
from geoexpress.exceptions import GeoExpressError


def lock_image(input_sid: str, output_sid: str, password: str) -> str:
    """
    Lock an existing MrSID by re-encoding it with a password.
    """

    if not os.path.exists(input_sid):
        raise FileNotFoundError(input_sid)

    with tempfile.TemporaryDirectory(prefix="geoexpress_lock_") as tmp:
        temp_tif = os.path.join(tmp, "decoded.tif")

        # 1️⃣ Decode SID → TIFF
        decode(
            input=input_sid,
            output=temp_tif
        )

        # 2️⃣ Encode TIFF → LOCKED SID (MG3 + pwd)
        return encode(
            input=temp_tif,
            output=output_sid,
            password=password
        )


def unlock_image(input_sid: str, output_sid: str, password: str) -> str:
    """
    Unlock a password-protected MrSID by re-encoding it without password.
    """

    if not os.path.exists(input_sid):
        raise FileNotFoundError(input_sid)

    with tempfile.TemporaryDirectory(prefix="geoexpress_unlock_") as tmp:
        temp_tif = os.path.join(tmp, "decoded.tif")

        # 1️⃣ Decode SID → TIFF (requires password)
        decode(
            input=input_sid,
            output=temp_tif,
            password=password
        )

        # 2️⃣ Encode TIFF → UNLOCKED SID (default MG4)
        return encode(
            input=temp_tif,
            output=output_sid
        )
