from typing import Optional
from pathlib import Path

EXTENSION_TO_FORMAT = {
    ".sid": "mg4",
    ".jp2": "jp2",
    ".ntf": "nitfjp2",
    ".nitf": "nitf",
    ".tif": "tiff",
    ".tiff": "tiff",
    ".las": "las",
    ".laz": "laz",
}

def detect_format_from_output(output_path: str) -> Optional[str]:
    return EXTENSION_TO_FORMAT.get(Path(output_path).suffix.lower())
