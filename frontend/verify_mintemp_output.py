"""
verify_mintemp_output.py
─────────────────────────────────────────────────────────────
Reads and verifies the exported MinTemp CSV from IMDTools.
File: Mintemp_MinT_2023.GRD_2022-12-31_to_2023-04-29.csv

Run:
    python verify_mintemp_output.py

Checks:
    1. File loads correctly
    2. Column names are correct
    3. Date range is correct
    4. Coordinate range is within India bounds
    5. Temperature values are in realistic range (-20°C to 50°C)
    6. No duplicate rows
    7. Missing value count
    8. Summary statistics per month
    9. Plots a map of Day 1 data points
   10. Plots time series for Bhopal (77.4°E, 23.2°N)
"""

import pandas as pd
import numpy as np
import os

# ── Config ────────────────────────────────────────────────────────────
CSV_FILE = r"D:\PHD\exma material\chari\Mintemp_MinT_2023.GRD_2022-12-31_to_2023-04-29.csv"

# Known bounds for 31×31 IMD MinTemp grid
LON_MIN, LON_MAX = 67.5,  97.5   # 31 columns × 1.0°
LAT_MIN, LAT_MAX =  7.5,  37.5   # 31 rows    × 1.0°

TEMP_MIN_VALID = -20.0   # °C — realistic India minimum
TEMP_MAX_VALID =  50.0   # °C — realistic India maximum

# ── Load ──────────────────────────────────────────────────────────────
print("=" * 60)
print("IMDTools — MinTemp CSV Verification")
print("=" * 60)

if not os.path.exists(CSV_FILE):
    print(f"❌ File not found: {CSV_FILE}")
    exit()

print(f"\n✅ File found: {os.path.basename(CSV_FILE)}")
print(f"   Size: {os.path.getsize(CSV_FILE) / 1024:.1f} KB")

df = pd.read_csv(CSV_FILE)
print(f"   Rows loaded: {len(df):,}")

# ── CHECK 1: Column names ─────────────────────────────────────────────
print("\n── Check 1: Columns ──")
expected_cols = {'day_index', 'date', 'latitude', 'longitude', 'mintemp_c'}
actual_cols   = set(df.columns)
missing_cols  = expected_cols - actual_cols

if missing_cols:
    print(f"   ❌ Missing columns: {missing_cols}")
else:
    print(f"   ✅ All columns present: {list(df.columns)}")

# ── CHECK 2: Date range ───────────────────────────────────────────────
print("\n── Check 2: Date Range ──")
df['date'] = pd.to_datetime(df['date'])
date_min = df['date'].min()
date_max = df['date'].max()
n_days   = df['day_index'].nunique()

print(f"   Start date : {date_min.date()}")
print(f"   End date   : {date_max.date()}")
print(f"   Unique days: {n_days}")

expected_start = pd.Timestamp('2022-12-31')
expected_end   = pd.Timestamp('2023-04-29')
if date_min == expected_start and date_max == expected_end:
    print(f"   ✅ Date range matches filename")
else:
    print(f"   ⚠️  Expected {expected_start.date()} → {expected_end.date()}")

# ── CHECK 3: Coordinate bounds ────────────────────────────────────────
print("\n── Check 3: Coordinate Bounds ──")
lon_min = df['longitude'].min()
lon_max = df['longitude'].max()
lat_min = df['latitude'].min()
lat_max = df['latitude'].max()

print(f"   Longitude : {lon_min:.2f}°E → {lon_max:.2f}°E")
print(f"   Latitude  : {lat_min:.2f}°N → {lat_max:.2f}°N")

lon_ok = LON_MIN <= lon_min and lon_max <= LON_MAX
lat_ok = LAT_MIN <= lat_min and lat_max <= LAT_MAX

print(f"   Lon bounds: {'✅' if lon_ok else '❌'} (expected {LON_MIN}–{LON_MAX})")
print(f"   Lat bounds: {'✅' if lat_ok else '❌'} (expected {LAT_MIN}–{LAT_MAX})")

n_unique_points = df.groupby(['latitude','longitude']).ngroups
print(f"   Unique grid points: {n_unique_points} (expected ~961 for 31×31)")

# ── CHECK 4: Temperature value range ─────────────────────────────────
print("\n── Check 4: Temperature Values ──")
temp = df['mintemp_c'].dropna()

print(f"   Min    : {temp.min():.2f} °C")
print(f"   Max    : {temp.max():.2f} °C")
print(f"   Mean   : {temp.mean():.2f} °C")
print(f"   Median : {temp.median():.2f} °C")
print(f"   Std    : {temp.std():.2f} °C")

out_of_range = df[(df['mintemp_c'] < TEMP_MIN_VALID) |
                  (df['mintemp_c'] > TEMP_MAX_VALID)]
if len(out_of_range) == 0:
    print(f"   ✅ All values within realistic range ({TEMP_MIN_VALID} to {TEMP_MAX_VALID} °C)")
else:
    print(f"   ⚠️  {len(out_of_range)} values outside realistic range!")
    print(out_of_range.head())

# ── CHECK 5: Missing values ───────────────────────────────────────────
print("\n── Check 5: Missing Values ──")
nulls = df['mintemp_c'].isna().sum()
pct   = nulls / len(df) * 100
print(f"   NaN count : {nulls:,} ({pct:.1f}%)")
if pct < 5:
    print(f"   ✅ Missing values acceptable")
else:
    print(f"   ⚠️  High missing value rate")

# ── CHECK 6: Duplicate rows ───────────────────────────────────────────
print("\n── Check 6: Duplicate Rows ──")
dupes = df.duplicated(subset=['date','latitude','longitude']).sum()
if dupes == 0:
    print(f"   ✅ No duplicate rows")
else:
    print(f"   ❌ {dupes} duplicate rows found!")

# ── CHECK 7: Grid cells per day ───────────────────────────────────────
print("\n── Check 7: Grid Cells Per Day ──")
cells_per_day = df.groupby('day_index').size()
print(f"   Min cells/day : {cells_per_day.min()}")
print(f"   Max cells/day : {cells_per_day.max()}")
print(f"   Expected      : 961 (31×31)")
if cells_per_day.min() == cells_per_day.max() == 961:
    print(f"   ✅ Consistent 961 cells per day")
else:
    print(f"   ⚠️  Inconsistent cell count — check parser")

# ── CHECK 8: Monthly statistics ───────────────────────────────────────
print("\n── Check 8: Monthly Statistics ──")
df['month'] = df['date'].dt.to_period('M')
monthly = df.groupby('month')['mintemp_c'].agg(['mean','min','max','count'])
monthly.columns = ['Mean °C', 'Min °C', 'Max °C', 'Records']
print(monthly.to_string())

# ── CHECK 9: Bhopal point verification ───────────────────────────────
print("\n── Check 9: Bhopal Point (77.5°E, 23.5°N) ──")
# Nearest grid point to Bhopal at 1.0° resolution
bhopal_lat = 23.5
bhopal_lon = 77.5

bhopal = df[
    (df['latitude']  == bhopal_lat) &
    (df['longitude'] == bhopal_lon)
].sort_values('date')

if len(bhopal) == 0:
    # Try nearest
    df['dist'] = ((df['latitude'] - bhopal_lat)**2 +
                  (df['longitude'] - bhopal_lon)**2)**0.5
    nearest = df.loc[df['dist'].idxmin()]
    print(f"   Exact point not found, nearest: "
          f"({nearest['latitude']}°N, {nearest['longitude']}°E)")
    bhopal = df[
        (df['latitude']  == nearest['latitude']) &
        (df['longitude'] == nearest['longitude'])
    ].sort_values('date')

if len(bhopal) > 0:
    print(f"   Days found : {len(bhopal)}")
    print(f"   Mean MinT  : {bhopal['mintemp_c'].mean():.2f} °C")
    print(f"   Min MinT   : {bhopal['mintemp_c'].min():.2f} °C  "
          f"({bhopal.loc[bhopal['mintemp_c'].idxmin(), 'date'].date()})")
    print(f"   Max MinT   : {bhopal['mintemp_c'].max():.2f} °C  "
          f"({bhopal.loc[bhopal['mintemp_c'].idxmax(), 'date'].date()})")
    print(f"\n   First 10 days:")
    print(bhopal[['date','mintemp_c']].head(10).to_string(index=False))

# ── Plot (optional — skip if matplotlib not available) ────────────────
print("\n── Plot: Try importing matplotlib ──")
try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # ── Plot 1: Spatial map Day 1 ──
    day0 = df[df['day_index'] == df['day_index'].min()].copy()
    sc = axes[0].scatter(
        day0['longitude'], day0['latitude'],
        c=day0['mintemp_c'],
        cmap='RdYlBu_r', s=200, marker='s',
        vmin=df['mintemp_c'].quantile(0.05),
        vmax=df['mintemp_c'].quantile(0.95)
    )
    plt.colorbar(sc, ax=axes[0], label='Min Temp (°C)')
    axes[0].set_title(f"Spatial Map — {day0['date'].iloc[0].date()}")
    axes[0].set_xlabel('Longitude (°E)')
    axes[0].set_ylabel('Latitude (°N)')
    axes[0].set_xlim(65, 100)
    axes[0].set_ylim(5, 40)
    axes[0].grid(True, alpha=0.3)
    # Mark Bhopal
    axes[0].plot(77.4, 23.2, 'k*', markersize=12, label='Bhopal')
    axes[0].legend()

    # ── Plot 2: Bhopal time series ──
    if len(bhopal) > 0:
        axes[1].plot(bhopal['date'], bhopal['mintemp_c'],
                     color='steelblue', linewidth=1.5, marker='o',
                     markersize=3, label='Min Temp')
        axes[1].axhline(0, color='red', linestyle='--', alpha=0.5, label='0°C')
        axes[1].fill_between(bhopal['date'], bhopal['mintemp_c'],
                             alpha=0.15, color='steelblue')
        axes[1].set_title('Min Temperature — Bhopal (77.5°E, 23.5°N)')
        axes[1].set_xlabel('Date')
        axes[1].set_ylabel('Min Temp (°C)')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=30, ha='right')

    plt.tight_layout()
    out_fig = r"D:\PHD\exma material\chari\mintemp_verification.png"
    plt.savefig(out_fig, dpi=150, bbox_inches='tight')
    print(f"   ✅ Plot saved: {out_fig}")
    plt.show()

except ImportError:
    print("   ⚠️  matplotlib not installed — skipping plots")
    print("   Install: pip install matplotlib")

# ── Final summary ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  File      : {os.path.basename(CSV_FILE)}")
print(f"  Rows      : {len(df):,}")
print(f"  Days      : {n_days}")
print(f"  Grid pts  : {n_unique_points}")
print(f"  Temp range: {temp.min():.1f}°C → {temp.max():.1f}°C")
print(f"  Missing   : {nulls:,} ({pct:.1f}%)")
print(f"  Duplicates: {dupes}")
print("=" * 60)