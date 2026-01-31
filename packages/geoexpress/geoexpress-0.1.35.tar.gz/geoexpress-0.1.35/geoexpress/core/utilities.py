import os
from geoexpress.core.base import GeoExpressCommand
from geoexpress.config import GEOEXPRESS_ADMIN
from geoexpress.utils import is_admin
from geoexpress.exceptions import GeoExpressLicenseError


def locking_code() -> str:
    if os.name == "nt" and not is_admin():
        raise GeoExpressLicenseError(
            "GeoExpress license tools require Administrator privileges.\n"
            "Please run this command from an elevated Command Prompt:\n\n"
            "  Right-click CMD → Run as administrator\n"
            "  geoexpress license"
        )

    exe = "echoid.exe" if os.name == "nt" else "echoid"
    echoid_path = GEOEXPRESS_ADMIN / exe

    cmd = GeoExpressCommand(str(echoid_path))
    return cmd.run([])
