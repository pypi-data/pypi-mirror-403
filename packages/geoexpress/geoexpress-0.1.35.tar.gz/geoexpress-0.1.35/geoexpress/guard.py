import os
from geoexpress.config import GEOEXPRESS_BIN
from geoexpress.utils import run_cmd
from geoexpress.exceptions import GeoExpressLicenseError


def ensure_geoexpress_ready():
    exe = "mrsidgeoencoder.exe" if os.name == "nt" else "mrsidgeoencoder"

    try:
        run_cmd([str(GEOEXPRESS_BIN / exe), "-h"])
    except Exception:
        raise GeoExpressLicenseError(
            "GeoExpress license not found or expired.\n"
            "Please install a valid GeoExpress license."
        )
