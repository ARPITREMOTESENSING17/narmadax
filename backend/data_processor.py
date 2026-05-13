import numpy as np
import pandas as pd
import csv
import os

# Optional: GeoTIFF support (requires rasterio)
try:
    import rasterio
    from rasterio.transform import from_bounds
    GEOTIFF_AVAILABLE = True
except ImportError:
    GEOTIFF_AVAILABLE = False

class DataProcessor:
    """Process and export .grd data to various formats"""
    
    def __init__(self, metadata, data):
        self.metadata = metadata
        self.data = data
    
    def to_csv(self, output_path):
        """Export grid data to CSV with lat, lon, value"""
        rows = []
        
        for row_idx in range(self.metadata['nrows']):
            for col_idx in range(self.metadata['ncols']):
                value = self.data[row_idx, col_idx]
                
                if not np.isnan(value):
                    # Calculate lat/lon for this cell
                    lon = self.metadata['xllcorner'] + (col_idx * self.metadata['cellsize']) + (self.metadata['cellsize'] / 2)
                    lat = self.metadata['yllcorner'] + (row_idx * self.metadata['cellsize']) + (self.metadata['cellsize'] / 2)
                    
                    rows.append({
                        'longitude': round(lon, 4),
                        'latitude': round(lat, 4),
                        'value': round(value, 2)
                    })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        return output_path
    
    def to_geotiff(self, output_path):
        """Export to GeoTIFF format (requires rasterio)"""
        if not GEOTIFF_AVAILABLE:
            raise ImportError("GeoTIFF export requires rasterio. Install with: pip install rasterio")
        
        # Calculate transform
        xmin = self.metadata['xllcorner']
        ymin = self.metadata['yllcorner']
        xmax = xmin + (self.metadata['ncols'] * self.metadata['cellsize'])
        ymax = ymin + (self.metadata['nrows'] * self.metadata['cellsize'])
        
        transform = from_bounds(xmin, ymin, xmax, ymax, 
                               self.metadata['ncols'], 
                               self.metadata['nrows'])
        
        # Write GeoTIFF
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=self.metadata['nrows'],
            width=self.metadata['ncols'],
            count=1,
            dtype=self.data.dtype,
            crs='EPSG:4326',
            transform=transform,
            nodata=-999
        ) as dst:
            # Replace NaN back to -999 for writing
            write_data = self.data.copy()
            write_data[np.isnan(write_data)] = -999
            dst.write(write_data, 1)
        
        return output_path
    
    def to_ascii_grid(self, output_path):
        """Export to ASCII Grid format (.asc)"""
        with open(output_path, 'w') as f:
            # Write header
            f.write(f"ncols         {self.metadata['ncols']}\n")
            f.write(f"nrows         {self.metadata['nrows']}\n")
            f.write(f"xllcorner     {self.metadata['xllcorner']}\n")
            f.write(f"yllcorner     {self.metadata['yllcorner']}\n")
            f.write(f"cellsize      {self.metadata['cellsize']}\n")
            f.write(f"NODATA_value  -999\n")
            
            # Write data
            for row in self.data:
                row_str = ' '.join([f"{val:.2f}" if not np.isnan(val) else "-999" for val in row])
                f.write(row_str + '\n')
        
        return output_path
    
    def create_summary_stats_csv(self, output_path):
        """Create summary statistics CSV"""
        valid_data = self.data[~np.isnan(self.data)]
        
        stats = {
            'Statistic': ['Minimum', 'Maximum', 'Mean', 'Median', 'Std Dev', 
                         'Total Cells', 'Valid Cells', 'NoData Cells'],
            'Value': [
                f"{np.min(valid_data):.2f}",
                f"{np.max(valid_data):.2f}",
                f"{np.mean(valid_data):.2f}",
                f"{np.median(valid_data):.2f}",
                f"{np.std(valid_data):.2f}",
                str(self.data.size),
                str(len(valid_data)),
                str(np.isnan(self.data).sum())
            ]
        }
        
        df = pd.DataFrame(stats)
        df.to_csv(output_path, index=False)
        return output_path
