# IMD Daily Rainfall .grd File - SOLVED!

## YOUR FILE FORMAT DISCOVERED ✓

**Your file:** `Rainfall_ind2024_rfp25.grd`

**Structure:**
- **NO HEADER** - Pure float32 data (little-endian)
- **366 days** of daily rainfall for 2024 (leap year)
- **Grid:** 135 columns × 129 rows (standard IMD 0.25° India grid)
- **Coverage:** 66.5°E to 100.25°E, 6.5°N to 38.75°N
- **NoData value:** -999.0
- **Total values:** 6,373,890 (= 135 × 129 × 366)

---

## QUICK START - Test Your File Now!

### Step 1: Run Test Script

```bash
cd "D:\PHD\grd reader\grd_reader_simple\grd_reader_project\backend"
py test_rainfall.py "D:\PHD\exma material\chari\Rainfall_ind2024_rfp25.grd"
```

This will:
- ✓ Parse all 366 days
- ✓ Show statistics
- ✓ Export Jan 1, 2024 to CSV
- ✓ Extract Delhi rainfall time series

**Expected output:** All tests pass, CSV exported!

---

## What You Can Do With This File

### 1. Export Specific Day
```bash
py imd_daily_parser.py "Rainfall_ind2024_rfp25.grd" "2024-01-01"
```

### 2. Get Time Series for Location
```python
from imd_daily_parser import IMDDailyGRDParser

parser = IMDDailyGRDParser("Rainfall_ind2024_rfp25.grd", "2024-01-01")
parser.parse()

# Get time series for any location
delhi_ts = parser.get_time_series_at_location(77.2, 28.6)
```

### 3. Export All Days to CSV (WARNING: Large file!)
```python
parser.export_all_days_to_csv("rainfall_2024_all.csv")
# Output: ~5-10 GB CSV file with all 366 days
```

### 4. Get Statistics
```python
# Statistics for specific day
stats_jan1 = parser.get_statistics(day_index=0)

# Statistics for all days
stats_all = parser.get_statistics()
```

---

## Use Web Interface

### 1. Start Server
```bash
cd backend
py app.py
```

### 2. Open Browser
```
http://localhost:5000
```

### 3. Upload File
- The interface will automatically detect it's a multi-day file
- Shows statistics for first day and all days
- Export options:
  - Single day CSV
  - All days CSV
  - Time series for locations

---

## File Details

**Why 366 days?**
- 2024 is a leap year
- File contains Jan 1 to Dec 31, 2024

**Grid Coverage:**
- Entire India at 0.25° (~25 km) resolution
- Latitude: 6.5°N to 38.75°N
- Longitude: 66.5°E to 100.25°E

**Data Format:**
- Each day: 135 × 129 = 17,415 grid cells
- Total: 17,415 cells × 366 days = 6,373,890 values
- File size: 6,373,890 values × 4 bytes = 25,495,560 bytes

---

## Technical Details

**Byte Structure:**
```
Byte 0-3:     First cell, Day 1 (float32, little-endian)
Byte 4-7:     Second cell, Day 1
...
Byte 69,656:  Last cell, Day 1 (17,415th cell)
Byte 69,660:  First cell, Day 2
...
```

**Storage Order:**
- Days are sequential
- Within each day: row-major order (left-to-right, top-to-bottom)

---

## Common Tasks

### Task 1: Extract Monthly Rainfall
```python
parser = IMDDailyGRDParser("Rainfall_ind2024_rfp25.grd", "2024-01-01")
parser.parse()

# Extract January (days 0-30)
jan_data = parser.data[0:31]  # Shape: (31, 129, 135)
jan_total = np.nansum(jan_data, axis=0)  # Sum over days
```

### Task 2: Find Wettest Day
```python
daily_means = [parser.get_statistics(i)['mean'] for i in range(366)]
wettest_day = np.argmax(daily_means)
print(f"Wettest day: Day {wettest_day} ({parser.start_date + timedelta(days=wettest_day)})")
```

### Task 3: Extract Specific Region
```python
# Define region bounds
lon_min, lon_max = 75, 80  # Example: subset region
lat_min, lat_max = 20, 25

# Convert to grid indices
col_start = int((lon_min - parser.xllcorner) / parser.cellsize)
col_end = int((lon_max - parser.xllcorner) / parser.cellsize)
row_start = int((parser.yllcorner + parser.nrows * parser.cellsize - lat_max) / parser.cellsize)
row_end = int((parser.yllcorner + parser.nrows * parser.cellsize - lat_min) / parser.cellsize)

# Extract subset
subset = parser.data[:, row_start:row_end, col_start:col_end]
```

---

## Summary

**✓ Your file format is now fully understood**
**✓ Custom parser created for this exact format**
**✓ Can extract any day, location, or region**
**✓ Ready to use for analysis!**

Run the test script to verify everything works!
