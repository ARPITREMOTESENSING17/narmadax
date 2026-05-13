"""
shared.py — Common config and helpers shared across all route blueprints.
Import this in every routes/*.py file.
"""

import os
import re
import struct

# ── Folders ──────────────────────────────────────────────────────────
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = '../output'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────

def get_year_from_filename(filepath: str) -> int:
    """Extract 4-digit year from any IMD filename."""
    match = re.search(r'(\d{4})', os.path.basename(filepath))
    if match:
        year = int(match.group(1))
        if 1901 <= year <= 2100:
            return year
    return 2024


def get_start_date(filepath: str) -> str:
    """Return YYYY-01-01 string extracted from filename."""
    return f"{get_year_from_filename(filepath)}-01-01"


# ── Rainfall-specific sniff cache ─────────────────────────────────────
_sniff_cache = {}

def is_imd_daily(filepath: str):
    """
    Sniff file to check if it is a multi-day IMD rainfall binary.
    Returns (is_daily: bool, n_days: int). Result is cached.
    """
    if filepath in _sniff_cache:
        return _sniff_cache[filepath]

    imd_cells = 135 * 129  # 17,415 cells per day
    with open(filepath, 'rb') as f:
        first_float = struct.unpack('<f', f.read(4))[0]
        f.seek(0, 2)
        file_size = f.tell()

    total_values = file_size // 4
    if abs(first_float - (-999.0)) < 0.1 and total_values % imd_cells == 0:
        result = (True, total_values // imd_cells)
    else:
        result = (False, 0)

    _sniff_cache[filepath] = result
    return result