import os
import subprocess
import ctypes
from geoexpress.exceptions import GeoExpressCommandError
from geoexpress.logger import logger
from pathlib import Path


def is_admin() -> bool:
    if os.name != "nt":
        return True
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_cmd(cmd: list[str]) -> str:
    display_cmd = [Path(cmd[0]).name] + cmd[1:]
    logger.info("Running command:")
    logger.info(" ".join(display_cmd))

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if proc.returncode != 0:
        logger.error(proc.stderr.strip())
        raise GeoExpressCommandError(proc.stderr.strip())

    logger.info("Completed successfully")
    return proc.stdout.strip()
