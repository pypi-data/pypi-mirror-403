# import os
# from pathlib import Path
# from geoexpress.exceptions import GeoExpressNotInstalled


# def find_geoexpress_bin() -> Path:
#     candidates = []

#     if os.name == "nt":
#         candidates.append(Path("C:/Program Files/LizardTech/GeoExpress/bin"))
#     else:
#         candidates.append(Path("/usr/local/LizardTech/GeoExpress/bin"))

#     for path in candidates:
#         if path.exists():
#             return path

#     raise GeoExpressNotInstalled(
#         "GeoExpress not installed.\n"
#         "Please download and install GeoExpress from Extensis."
#     )


# GEOEXPRESS_BIN = find_geoexpress_bin()

import os
from pathlib import Path
from geoexpress.exceptions import GeoExpressNotInstalled


def find_geoexpress_root() -> Path:
    candidates = []

    if os.name == "nt":
        candidates.append(Path("C:/Program Files/LizardTech/GeoExpress"))
    else:
        candidates.append(Path("/usr/local/LizardTech/GeoExpress"))

    for root in candidates:
        if root.exists():
            return root

    raise GeoExpressNotInstalled(
        "GeoExpress not installed.\n"
        "Please download and install GeoExpress from Extensis."
    )


GEOEXPRESS_ROOT = find_geoexpress_root()
GEOEXPRESS_BIN = GEOEXPRESS_ROOT / "bin"
GEOEXPRESS_ADMIN = GEOEXPRESS_ROOT / "Tools" / "Admin"
