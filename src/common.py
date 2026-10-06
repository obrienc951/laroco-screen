"""
common.py — SHARED HELPERS
==========================
Small functions every other script uses, kept in one place so they
are written once:
  - load_config():  reads config.yaml into a Python dictionary
  - project_path(): turns "data/raw/x.geojson" into a full path
  - log():          prints a timestamped progress message
"""

from pathlib import Path   # pathlib handles file paths on Windows and Mac alike
from datetime import datetime
import yaml                # PyYAML reads the config.yaml text file

# The project folder = the folder above /src (where this file lives).
ROOT = Path(__file__).resolve().parent.parent


def project_path(relative):
    """Convert a path written relative to the project folder into a full path."""
    return ROOT / relative


def load_config():
    """Read config.yaml and return it as a nested dictionary,
    e.g. cfg["filters"]["min_area_ha"] -> 0.2"""
    with open(ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def lookup(table, key):
    """Fetch a per-LA value from config, falling back to 'default'."""
    return table.get(key, table["default"])


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}")
