import os
from geoexpress.config import GEOEXPRESS_BIN
from geoexpress.guard import ensure_geoexpress_ready
from geoexpress.utils import run_cmd


class GeoExpressCommand:
    """
    Generic wrapper for ANY GeoExpress CLI command.
    """

    def __init__(self, executable: str):
        self.executable = executable

    def run(self, args: list[str]) -> str:
        ensure_geoexpress_ready()

        exe = self.executable + (".exe" if os.name == "nt" else "")
        cmd = [str(GEOEXPRESS_BIN / exe)] + args

        return run_cmd(cmd)
