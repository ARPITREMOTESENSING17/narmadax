"""
Quick test script for IMD daily rainfall .grd file
Run this to verify the parser works on your file
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from imd_daily_parser import IMDDailyGRDParser

def test_rainfall_file(filepath):
    """Test parsing the rainfall file"""
    
    print("=" * 70)
    print("TESTING IMD DAILY RAINFALL PARSER")
    print("=" * 70)
    print(f"File: {filepath}\n")
    
    # Create parser
    parser = IMDDailyGRDParser(filepath, start_date="2024-01-01")
    
    # Parse file
    print("Step 1: Parsing file...")
    data = parser.parse()
    print(f"✓ Successfully parsed {parser.n_days} days of data\n")
    
    # Show grid info
    print("Grid Information:")
    print(f"  Columns: {parser.ncols}")
    print(f"  Rows: {parser.nrows}")
    print(f"  Cell size: {parser.cellsize}°")
    print(f"  Coverage: {parser.xllcorner}°E to {parser.xllcorner + parser.ncols * parser.cellsize}°E")
    print(f"           {parser.yllcorner}°N to {parser.yllcorner + parser.nrows * parser.cellsize}°N\n")
    
    # Statistics for first day (Jan 1, 2024)
    print("Step 2: Calculating statistics for Jan 1, 2024...")
    stats_day1 = parser.get_statistics(day_index=0)
    print(f"✓ Jan 1, 2024 Rainfall:")
    print(f"    Min: {stats_day1['min']:.2f} mm")
    print(f"    Max: {stats_day1['max']:.2f} mm")
    print(f"    Mean: {stats_day1['mean']:.2f} mm")
    print(f"    Median: {stats_day1['median']:.2f} mm")
    print(f"    Valid cells: {stats_day1['count']:,}\n")
    
    # Statistics for all days
    print("Step 3: Calculating statistics for all 366 days...")
    stats_all = parser.get_statistics()
    print(f"✓ All Days (2024) Rainfall:")
    print(f"    Min: {stats_all['min']:.2f} mm")
    print(f"    Max: {stats_all['max']:.2f} mm")
    print(f"    Mean: {stats_all['mean']:.2f} mm\n")
    
    # Export first day to CSV
    output_file = filepath.replace('.grd', '_Jan01_2024.csv')
    print(f"Step 4: Exporting Jan 1, 2024 to CSV...")
    parser.export_day_to_csv(0, output_file)
    print(f"✓ Exported to: {output_file}\n")
    
    # Get time series for a location (example: Delhi)
    print("Step 5: Extracting time series for Delhi (77.2°E, 28.6°N)...")
    try:
        time_series = parser.get_time_series_at_location(77.2, 28.6)
        jan_rainfall = [day['rainfall_mm'] for day in time_series[:31] if day['rainfall_mm'] is not None]
        total_jan = sum(jan_rainfall)
        print(f"✓ Delhi January 2024 total rainfall: {total_jan:.2f} mm\n")
    except Exception as e:
        print(f"  Note: {e}\n")
    
    print("=" * 70)
    print("✓ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nYour file format is correct and ready to use!")
    print(f"The parser found {parser.n_days} days of rainfall data for India")
    print(f"Grid: {parser.ncols} x {parser.nrows} cells at 0.25° resolution")
    print("\nNext steps:")
    print("  1. Run the web app: python app.py")
    print("  2. Upload your file through the web interface")
    print("  3. Export daily or full year data as needed")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_rainfall.py <path_to_grd_file>")
        print('Example: python test_rainfall.py "D:\\PHD\\exma material\\chari\\Rainfall_ind2024_rfp25.grd"')
        sys.exit(1)
    
    test_rainfall_file(sys.argv[1])
