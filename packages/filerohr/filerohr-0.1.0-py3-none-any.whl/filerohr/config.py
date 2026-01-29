import logging
from pathlib import Path
import shutil

from filerohr.env import Environment

logger = logging.getLogger(__name__)

base_env = Environment()
env = Environment("FILEROHR_")

BASE_DIR = Path(__file__).parent.parent

TZ = base_env.get("TZ", default="Europe/Vienna")
FFMPEG_BIN = env.get("FFMPEG_BIN", cast=Path, default=Path("/usr/bin/ffmpeg"))
FFPROBE_BIN = env.get("FFPROBE_BIN", cast=Path, default=Path("/usr/bin/ffprobe"))
FFMPEG_NORMALIZE_BIN = env.get(
    "FFMPEG_NORMALIZE_BIN", cast=Path, default=Path(shutil.which("ffmpeg-normalize"))
)
DATA_DIR = env.get("DATA_DIR", cast=Path, default=BASE_DIR / "data")
TMP_DIR = env.get("TMP_DIR", cast=Path, default=DATA_DIR / "tmp")
TASK_MODULES = env.get_list("TASK_MODULES", default=[])
PIPELINE_CONFIG_DIR = env.get(
    "PIPELINE_CONFIG_DIR", cast=Path, default=BASE_DIR / "pipeline.conf.d"
)

DATA_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
FFMPEG_BIN.stat()
FFPROBE_BIN.stat()

if TMP_DIR.stat().st_dev != DATA_DIR.stat().st_dev:
    logger.warning("TMP_DIR on a different filesystem than DATA_DIR is discouraged.")
