from pathlib import Path
from geoexpress.utils import run_cmd
from geoexpress.exceptions import GeoExpressCommandError


def tiff_to_jp2(
    input_tif: str,
    output_jp2: str,
    quality: int = 25
) -> str:
    """
    Convert GeoTIFF → JPEG2000 (JP2) using GDAL.
    """
    cmd = [
        "gdal_translate",
        "-of", "JP2OpenJPEG",
        "-co", f"QUALITY={quality}",
        input_tif,
        output_jp2
    ]

    return run_cmd(cmd)


def jp2_to_tiff(
    input_jp2: str,
    output_tif: str
) -> str:
    """
    Convert JPEG2000 (JP2) → GeoTIFF using GDAL.
    """
    cmd = [
        "gdal_translate",
        "-of", "GTiff",
        input_jp2,
        output_tif
    ]

    return run_cmd(cmd)
