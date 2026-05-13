"""
imd_maxtemp_parser.py
─────────────────────────────────────────────────────────────
IMD Daily Maximum Temperature Grid Parser

File format : Maxtemp_MaxT_YYYY.GRD
Resolution  : 1.0° × 1.0°
Grid        : 31 × 31 = 961 cells/day
Coverage    : 67.5°E–97.5°E, 7.5°N–37.5°N
Values      : °C (float32, little-endian)
Nodata      : 99.9
Leap years  : 366 days included
Source      : IMD High Resolution 1×1° Gridded Daily Temperature (1951–2024)
"""

import struct
import numpy as np
from datetime import date, timedelta
import re


# ── Grid constants ────────────────────────────────────────────────────
NCOLS      = 31
NROWS      = 31
CELLSIZE   = 1.0
XLLCORNER  = 67.0    # western edge  (cell centres start at 67.5)
YLLCORNER  = 7.0     # southern edge (cell centres start at 7.5)
NODATA     = 99.9    # IMD missing value for temperature grids
CELLS_DAY  = NCOLS * NROWS   # 961


def _year_from_filename(filepath: str) -> int:
    """Extract 4-digit year from Maxtemp_MaxT_YYYY.GRD filename."""
    m = re.search(r'(\d{4})', str(filepath))
    if m:
        y = int(m.group(1))
        if 1901 <= y <= 2100:
            return y
    return 2024


def _is_leap(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)


class IMDMaxTempParser:
    """
    Parse IMD daily maximum temperature .GRD files.

    Usage:
        parser = IMDMaxTempParser('Maxtemp_MaxT_2023.GRD')
        parser.parse()
        data = parser.get_day_data(0)   # day 0 = Jan 1
    """

    def __init__(self, filepath: str, start_date: str = None):
        self.filepath   = filepath
        self.year       = _year_from_filename(filepath)
        self.n_days     = 366 if _is_leap(self.year) else 365
        self.start_date = start_date or f'{self.year}-01-01'

        # Grid metadata
        self.ncols        = NCOLS
        self.nrows        = NROWS
        self.cellsize     = CELLSIZE
        self.xllcorner    = XLLCORNER
        self.yllcorner    = YLLCORNER
        self.nodata_value = NODATA   # 99.9

        self._data: np.ndarray | None = None   # shape (n_days, nrows, ncols)

    # ── Public API ────────────────────────────────────────────────────

    def parse(self):
        """Read entire binary file into memory, mask nodata as NaN."""
        with open(self.filepath, 'rb') as f:
            raw = f.read()

        total_floats = len(raw) // 4
        n_days       = total_floats // CELLS_DAY
        self.n_days  = n_days   # update from actual file size

        flat = np.frombuffer(
            raw[:n_days * CELLS_DAY * 4], dtype='<f4'
        ).astype(float)

        # Mask nodata: IMD uses +99.9 for missing/ocean cells
        flat[flat >= NODATA - 0.05] = np.nan

        self._data = flat.reshape(n_days, NROWS, NCOLS)

    def get_day_data(self, day_idx: int) -> np.ndarray:
        """Return (NROWS, NCOLS) array for a given day index (0-based)."""
        self._check_parsed()
        return self._data[day_idx]

    def get_statistics(self, day_idx: int = None) -> dict:
        """
        Stats for one day (day_idx given) or entire dataset (None).
        Returns dict: min / max / mean / median / std / count.
        """
        self._check_parsed()
        arr   = self._data[day_idx] if day_idx is not None else self._data
        valid = arr[~np.isnan(arr)]

        if valid.size == 0:
            return dict(min=None, max=None, mean=None,
                        median=None, std=None, count=0)

        return dict(
            min    = float(np.nanmin(valid)),
            max    = float(np.nanmax(valid)),
            mean   = float(np.nanmean(valid)),
            median = float(np.nanmedian(valid)),
            std    = float(np.nanstd(valid)),
            count  = int(valid.size),
        )

    def get_point_value(self, longitude: float, latitude: float,
                        day_idx: int) -> float | None:
        """
        Nearest-neighbour lookup for (lon, lat) on a given day.
        Returns °C or None if out of bounds / nodata.
        """
        self._check_parsed()
        col = round((longitude - XLLCORNER - CELLSIZE / 2) / CELLSIZE)
        row = round((latitude  - YLLCORNER - CELLSIZE / 2) / CELLSIZE)

        if not (0 <= col < NCOLS and 0 <= row < NROWS):
            return None

        val = self._data[day_idx, row, col]
        return None if np.isnan(val) else float(val)

    def get_timeseries(self, longitude: float, latitude: float,
                       from_day: int = 0, to_day: int = None) -> list:
        """
        Time-series of max temperature for a point over a day range.
        Returns list of {date, maxtemp_c}.
        """
        self._check_parsed()
        to_day = (self.n_days - 1) if to_day is None else to_day
        base   = date.fromisoformat(self.start_date)
        result = []

        for idx in range(from_day, to_day + 1):
            val = self.get_point_value(longitude, latitude, idx)
            d   = base + timedelta(days=idx)
            result.append(dict(date=d.isoformat(), maxtemp_c=val))

        return result

    def iter_day_rows(self, day_idx: int):
        """
        Generator: yields (lat, lon, maxtemp_c) for every valid cell.
        Used for CSV export — skips nodata (ocean/missing) cells.
        """
        self._check_parsed()
        grid = self._data[day_idx]

        for r in range(NROWS):
            lat = YLLCORNER + r * CELLSIZE + CELLSIZE / 2
            for c in range(NCOLS):
                lon = XLLCORNER + c * CELLSIZE + CELLSIZE / 2
                val = grid[r, c]
                if not np.isnan(val):
                    yield lat, lon, float(val)

    @property
    def extent(self) -> dict:
        return dict(
            xmin = XLLCORNER,
            xmax = XLLCORNER + NCOLS * CELLSIZE,
            ymin = YLLCORNER,
            ymax = YLLCORNER + NROWS * CELLSIZE,
        )

    # ── Private ───────────────────────────────────────────────────────

    def _check_parsed(self):
        if self._data is None:
            raise RuntimeError("Call parse() first.")