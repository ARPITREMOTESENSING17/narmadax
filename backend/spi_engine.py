"""
spi_engine.py
─────────────────────────────────────────────────────────────────
WMO Standard Standardized Precipitation Index (SPI) Calculator

Methodology:
  McKee et al. (1993, 1995), Edwards & McKee (1997)
  WMO Guidelines on the SPI (WMO-No. 1090, 2012)

Steps:
  1. Aggregate daily → monthly rainfall totals
  2. Build rolling window for chosen timescale (1/3/6/9/12/24)
  3. Fit Gamma distribution (handles zero rainfall correctly)
  4. Transform cumulative probabilities → standard normal (SPI)

Reference:
  At least 30 years required (WMO standard)
  Recommended baseline: 1951-2010
"""

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import gamma as gamma_fn
import warnings
warnings.filterwarnings('ignore')


# ── SPI Drought Categories (WMO Table 1) ─────────────────────────────
SPI_CATEGORIES = [
    ( 2.00,  None,  'Extremely Wet',     '#0a1f6e'),
    ( 1.50,  2.00,  'Severely Wet',      '#1565C0'),
    ( 1.00,  1.50,  'Moderately Wet',    '#42A5F5'),
    (-0.99,  1.00,  'Near Normal',       '#66BB6A'),
    (-1.50, -1.00,  'Moderate Drought',  '#FDD835'),
    (-2.00, -1.50,  'Severe Drought',    '#EF6C00'),
    ( None, -2.00,  'Extreme Drought',   '#B71C1C'),
]

def get_spi_category(value: float) -> dict:
    """Return category name and color for an SPI value."""
    if np.isnan(value):
        return {'label': 'No Data', 'color': '#cccccc'}
    for upper, lower, label, color in SPI_CATEGORIES:
        lo_ok = (lower is None) or (value >= lower)
        hi_ok = (upper is None) or (value <  upper)
        if lo_ok and hi_ok:
            return {'label': label, 'color': color}
    return {'label': 'Near Normal', 'color': '#66BB6A'}


# ── Step 1: Daily → Monthly aggregation ──────────────────────────────
def daily_to_monthly(df_daily: pd.DataFrame,
                     date_col: str = 'date',
                     value_col: str = 'rainfall_mm',
                     lat_col:  str = 'latitude',
                     lon_col:  str = 'longitude') -> pd.DataFrame:
    """
    Aggregate daily rainfall CSV (from IMDTools) to monthly totals.

    Input columns : date, latitude, longitude, rainfall_mm
    Output columns: year, month, latitude, longitude, rainfall_mm
    """
    df = df_daily.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df['year']   = df[date_col].dt.year
    df['month']  = df[date_col].dt.month

    monthly = (df.groupby([lat_col, lon_col, 'year', 'month'])[value_col]
                 .sum()
                 .reset_index())
    monthly.columns = [lat_col, lon_col, 'year', 'month', value_col]
    return monthly


# ── Step 2 + 3 + 4: SPI calculation for a single time series ─────────
def calculate_spi_series(monthly_values: np.ndarray,
                         scale: int = 3,
                         ref_start: int = None,
                         ref_end:   int = None) -> np.ndarray:
    """
    Calculate SPI for a 1-D array of monthly rainfall values.

    Parameters:
        monthly_values : array of length N (monthly totals, chronological)
        scale          : SPI timescale (1, 3, 6, 9, 12, 24)
        ref_start      : index of first reference period month (None = all)
        ref_end        : index of last  reference period month (None = all)

    Returns:
        spi : array of length N (NaN for first scale-1 months)
    """
    n = len(monthly_values)
    spi = np.full(n, np.nan)

    # Rolling sums
    rolled = np.full(n, np.nan)
    for i in range(scale - 1, n):
        window = monthly_values[i - scale + 1 : i + 1]
        if not np.any(np.isnan(window)):
            rolled[i] = np.sum(window)

    # Fit per calendar month (month 1-12)
    # This ensures Jan is compared to Jans, Feb to Febs etc.
    months_idx = np.arange(n) % 12   # 0-11

    for m in range(12):
        mask_all = (months_idx == m) & ~np.isnan(rolled)
        if ref_start is not None and ref_end is not None:
            mask_ref = mask_all & (np.arange(n) >= ref_start) & \
                                  (np.arange(n) <= ref_end)
        else:
            mask_ref = mask_all

        vals = rolled[mask_ref]
        if len(vals) < 10:   # need minimum data
            continue

        # Probability of zero (q)
        q = np.sum(vals == 0) / len(vals)
        nonzero = vals[vals > 0]
        if len(nonzero) < 4:
            continue

        # Fit Gamma distribution using MLE
        try:
            alpha, loc, beta = stats.gamma.fit(nonzero, floc=0)
        except Exception:
            continue

        # Transform all months (not just reference) using fitted params
        all_mask = mask_all
        for i in np.where(all_mask)[0]:
            x = rolled[i]
            if np.isnan(x):
                continue
            if x == 0:
                p = q
            else:
                # H(x) = q + (1-q) * G(x)  where G = gamma CDF
                G = stats.gamma.cdf(x, alpha, scale=beta)
                p = q + (1 - q) * G

            # Clamp to avoid infinity at extremes
            p = np.clip(p, 1e-6, 1 - 1e-6)

            # Inverse normal transform (Abramowitz & Stegun approximation)
            # Used in McKee 1993 and WMO manual
            if p <= 0.5:
                W = np.sqrt(-2 * np.log(p))
                sign = -1
            else:
                W = np.sqrt(-2 * np.log(1 - p))
                sign = 1

            C0, C1, C2 = 2.515517, 0.802853, 0.010328
            d1, d2, d3 = 1.432788, 0.189269, 0.001308

            spi_val = sign * (W - (C0 + C1*W + C2*W**2) /
                                   (1 + d1*W + d2*W**2 + d3*W**3))
            spi[i] = spi_val

    return spi


# ── Main: Calculate SPI for full grid or single point ─────────────────
def calculate_spi_grid(monthly_df: pd.DataFrame,
                       scale:       int  = 3,
                       ref_start_yr: int = 1951,
                       ref_end_yr:   int = 2010,
                       lat_col:  str = 'latitude',
                       lon_col:  str = 'longitude',
                       val_col:  str = 'rainfall_mm') -> pd.DataFrame:
    """
    Calculate SPI for every grid point in a monthly rainfall DataFrame.

    Input:  monthly_df with columns [lat, lon, year, month, rainfall_mm]
    Output: DataFrame with columns [lat, lon, year, month, spi, category, color]
    """
    results = []

    points = monthly_df[[lat_col, lon_col]].drop_duplicates().values

    for lat, lon in points:
        pt = monthly_df[
            (monthly_df[lat_col] == lat) &
            (monthly_df[lon_col] == lon)
        ].sort_values(['year', 'month']).reset_index(drop=True)

        vals = pt[val_col].values.astype(float)

        # Reference period indices
        ref_mask = (pt['year'] >= ref_start_yr) & (pt['year'] <= ref_end_yr)
        ref_indices = np.where(ref_mask)[0]
        ref_start = int(ref_indices[0])  if len(ref_indices) > 0 else None
        ref_end   = int(ref_indices[-1]) if len(ref_indices) > 0 else None

        spi_vals = calculate_spi_series(vals, scale, ref_start, ref_end)

        for i, row in pt.iterrows():
            s = spi_vals[i]
            cat = get_spi_category(s)
            results.append({
                lat_col:  lat,
                lon_col:  lon,
                'year':   int(row['year']),
                'month':  int(row['month']),
                'rainfall_mm': float(row[val_col]),
                'spi':    round(float(s), 4) if not np.isnan(s) else None,
                'category': cat['label'],
                'color':    cat['color'],
            })

    return pd.DataFrame(results)


# ── Statistics summary ────────────────────────────────────────────────
def drought_statistics(spi_series: pd.Series,
                       dates: pd.Series = None) -> dict:
    """
    Compute drought statistics from SPI time series.
    Returns dict ready for JSON response.
    """
    valid = spi_series.dropna()
    if len(valid) == 0:
        return {}

    drought = valid[valid <= -1.0]
    severe  = valid[valid <= -1.5]
    extreme = valid[valid <= -2.0]
    wet     = valid[valid >= 1.0]

    # Longest consecutive drought spell
    in_drought = (valid <= -1.0).astype(int)
    max_spell, cur = 0, 0
    for v in in_drought:
        cur = cur + 1 if v else 0
        max_spell = max(max_spell, cur)

    # Decade-wise drought frequency
    decade_freq = {}
    if dates is not None:
        yrs = pd.to_datetime(dates).dt.year
        for decade_start in range(1950, 2030, 10):
            mask = (yrs >= decade_start) & (yrs < decade_start + 10)
            d_vals = valid[mask[valid.index]]
            if len(d_vals) > 0:
                freq = round((d_vals <= -1.0).sum() / len(d_vals) * 100, 1)
                decade_freq[f"{decade_start}s"] = freq

    return {
        'total_months':         int(len(valid)),
        'drought_months':       int(len(drought)),
        'drought_pct':          round(len(drought) / len(valid) * 100, 1),
        'severe_drought_months': int(len(severe)),
        'extreme_drought_months': int(len(extreme)),
        'wet_months':           int(len(wet)),
        'mean_spi':             round(float(valid.mean()), 3),
        'min_spi':              round(float(valid.min()),  3),
        'max_spi':              round(float(valid.max()),  3),
        'longest_drought_spell': int(max_spell),
        'decade_drought_freq':  decade_freq,
    }