import struct
import numpy as np
from datetime import datetime, timedelta

class IMDDailyGRDParser:
    """
    Parser for IMD daily rainfall .grd files
    - No header
    - Pure float32 data (little-endian)
    - Multiple daily grids stacked together
    - Standard IMD India grid: 135 x 129 cells (0.25° resolution)
    """
    
    def __init__(self, filepath, start_date="2024-01-01"):
        self.filepath = filepath
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Standard IMD 0.25° India grid
        self.ncols = 135
        self.nrows = 129
        self.xllcorner = 66.5
        self.yllcorner = 6.5
        self.cellsize = 0.25
        self.nodata_value = -999.0
        
        self.cells_per_day = self.ncols * self.nrows
        self.n_days = None
        self.data = None
        
    def parse(self):
        """Parse entire file"""
        with open(self.filepath, 'rb') as f:
            # Get file size
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(0)
            
            # Calculate number of days
            total_values = file_size // 4  # 4 bytes per float32
            self.n_days = total_values // self.cells_per_day
            
            print(f"File contains {self.n_days} days of data")
            print(f"Grid: {self.ncols} x {self.nrows} cells")
            print(f"Total values: {total_values:,}")
            
            # Read all data
            all_bytes = f.read()
            all_values = struct.unpack(f'<{total_values}f', all_bytes)
            
            # Reshape to (days, rows, cols)
            self.data = np.array(all_values).reshape(
                self.n_days, 
                self.nrows, 
                self.ncols
            )
            
            # Replace -999 with NaN
            self.data[np.abs(self.data - self.nodata_value) < 0.01] = np.nan
            
        return self.data
    
    def get_day_data(self, day_index):
        """Get data for specific day (0-indexed)"""
        if self.data is None:
            self.parse()
        
        if day_index >= self.n_days:
            raise ValueError(f"Day {day_index} out of range (0-{self.n_days-1})")
        
        return self.data[day_index]
    
    def get_date_data(self, date_str):
        """Get data for specific date (YYYY-MM-DD)"""
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
        day_index = (target_date - self.start_date).days
        
        return self.get_day_data(day_index)
    
    def get_statistics(self, day_index=None):
        """Calculate statistics for a specific day or all days"""
        if self.data is None:
            self.parse()
        
        if day_index is not None:
            data_subset = self.data[day_index]
        else:
            data_subset = self.data
        
        valid_data = data_subset[~np.isnan(data_subset)]
        
        stats = {
            'min': float(np.min(valid_data)) if len(valid_data) > 0 else None,
            'max': float(np.max(valid_data)) if len(valid_data) > 0 else None,
            'mean': float(np.mean(valid_data)) if len(valid_data) > 0 else None,
            'median': float(np.median(valid_data)) if len(valid_data) > 0 else None,
            'std': float(np.std(valid_data)) if len(valid_data) > 0 else None,
            'count': int(len(valid_data)),
            'total_cells': int(data_subset.size)
        }
        
        return stats
    
    def export_day_to_csv(self, day_index, output_path):
        """Export single day to CSV"""
        import pandas as pd
        
        day_data = self.get_day_data(day_index)
        date = self.start_date + timedelta(days=day_index)
        
        rows = []
        for row_idx in range(self.nrows):
            for col_idx in range(self.ncols):
                value = day_data[row_idx, col_idx]
                
                if not np.isnan(value):
                    lon = self.xllcorner + (col_idx * self.cellsize) + (self.cellsize / 2)
                    # CORRECT: Grid row 0 = South India (Kerala), row 128 = North India (Kashmir)
                    lat = self.yllcorner + (row_idx * self.cellsize) + (self.cellsize / 2)
                    
                    rows.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'longitude': round(lon, 4),
                        'latitude': round(lat, 4),
                        'rainfall_mm': round(value, 2)
                    })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        return output_path
    
    def export_all_days_to_csv(self, output_path):
        """Export all days to single CSV (warning: large file!)"""
        import pandas as pd
        
        if self.data is None:
            self.parse()
        
        rows = []
        for day_idx in range(self.n_days):
            date = self.start_date + timedelta(days=day_idx)
            day_data = self.data[day_idx]
            
            for row_idx in range(self.nrows):
                for col_idx in range(self.ncols):
                    value = day_data[row_idx, col_idx]
                    
                    if not np.isnan(value):
                        lon = self.xllcorner + (col_idx * self.cellsize) + (self.cellsize / 2)
                        # CORRECT: Grid row 0 = South India (Kerala), row 128 = North India (Kashmir)
                        lat = self.yllcorner + (row_idx * self.cellsize) + (self.cellsize / 2)
                        
                        rows.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'longitude': round(lon, 4),
                            'latitude': round(lat, 4),
                            'rainfall_mm': round(value, 2)
                        })
            
            if (day_idx + 1) % 30 == 0:
                print(f"Processed {day_idx + 1}/{self.n_days} days...")
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        return output_path
    
    def get_time_series_at_location(self, lon, lat):
        """Extract time series for a specific location"""
        if self.data is None:
            self.parse()
        
        # Convert lon/lat to grid indices
        col = int((lon - self.xllcorner) / self.cellsize)
        # CORRECT: Grid row 0 = South India (Kerala), row 128 = North India (Kashmir)
        row = int((lat - self.yllcorner) / self.cellsize)
        
        if not (0 <= row < self.nrows and 0 <= col < self.ncols):
            raise ValueError(f"Location ({lon}, {lat}) outside grid bounds")
        
        # Extract time series
        time_series = []
        for day_idx in range(self.n_days):
            date = self.start_date + timedelta(days=day_idx)
            value = self.data[day_idx, row, col]
            
            time_series.append({
                'date': date.strftime('%Y-%m-%d'),
                'rainfall_mm': float(value) if not np.isnan(value) else None
            })
        
        return time_series


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python imd_daily_parser.py <input.grd> [start_date]")
        print("Example: python imd_daily_parser.py rainfall_2024.grd 2024-01-01")
        sys.exit(1)
    
    filepath = sys.argv[1]
    start_date = sys.argv[2] if len(sys.argv) > 2 else "2024-01-01"
    
    # Create parser
    parser = IMDDailyGRDParser(filepath, start_date)
    
    # Parse file
    print(f"Parsing {filepath}...")
    data = parser.parse()
    
    # Show statistics for first day
    print(f"\nStatistics for {start_date}:")
    stats = parser.get_statistics(day_index=0)
    print(f"  Min: {stats['min']:.2f} mm")
    print(f"  Max: {stats['max']:.2f} mm")
    print(f"  Mean: {stats['mean']:.2f} mm")
    
    # Export first day
    output_file = filepath.replace('.grd', '_day1.csv')
    print(f"\nExporting first day to: {output_file}")
    parser.export_day_to_csv(0, output_file)
    print("Done!")