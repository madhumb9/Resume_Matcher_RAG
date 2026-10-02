import os
import sys
from pathlib import Path


os.environ["APP_ENV"] = "vercel"

ROOT_DIR = Path(
    __file__
).resolve().parents[1]

SRC_DIR = ROOT_DIR / "src"

sys.path.insert(
    0,
    str(SRC_DIR)
)


from resume_matcher.main import app