import struct
import numpy as np
import json

class GRDParser:
    """Parser for IMD .grd files with auto-format detection"""
    
    def __init__(self, filepath, header_format='auto'):
        self.filepath = filepath
        self.header_format = header_format  # 'auto', 'format1', 'format2', 'format3'
        self.metadata = {}
        self.data = None
        
    def detect_format(self):
        """Auto-detect the correct header format"""
        with open(self.filepath, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(0)
            
            # Try different formats
            formats_to_try = [
                ('format1', 24, '6i'),      # 6 int32
                ('format2', 24, '4i2f'),    # 4 int32 + 2 float32
                ('format3', 24, '2i4f'),    # 2 int32 + 4 float32
            ]
            
            for format_name, header_size, format_str in formats_to_try:
                f.seek(0)
                header_bytes = f.read(header_size)
                header = struct.unpack(format_str, header_bytes)
                
                ncols = header[0]
                nrows = header[1]
                
                # Check if valid
                if ncols > 0 and ncols < 10000 and nrows > 0 and nrows < 10000:
                    expected_data_bytes = ncols * nrows * 4
                    actual_data_bytes = file_size - header_size
                    
                    if abs(expected_data_bytes - actual_data_bytes) < 100:
                        return format_name, header_size, format_str
            
            raise ValueError("Could not auto-detect format. Please run inspect_grd.py first")
        
    def parse(self):
        """Parse .grd file and extract metadata + data"""
        with open(self.filepath, 'rb') as f:
            # Get file size
            f.seek(0, 2)
            file_size = f.tell()
            f.seek(0)
            
            # Detect format if auto
            if self.header_format == 'auto':
                format_name, header_size, format_str = self.detect_format()
            else:
                # Use specified format
                format_map = {
                    'format1': (24, '6i'),
                    'format2': (24, '4i2f'),
                    'format3': (24, '2i4f'),
                }
                header_size, format_str = format_map[self.header_format]
            
            # Read header
            header_bytes = f.read(header_size)
            header = struct.unpack(format_str, header_bytes)
            
            self.metadata = {
                'ncols': int(header[0]),
                'nrows': int(header[1]),
                'xllcorner': float(header[2]),
                'yllcorner': float(header[3]),
                'cellsize': float(header[4]) if len(header) > 4 else 0.25,
                'nodata_value': float(header[5]) if len(header) > 5 else -999.0,
                'header_size': header_size
            }
            
            # Calculate total cells
            total_cells = self.metadata['ncols'] * self.metadata['nrows']
            expected_data_size = total_cells * 4
            actual_data_size = file_size - header_size
            
            # Validation
            if abs(actual_data_size - expected_data_size) > 100:
                raise ValueError(
                    f"Data size mismatch!\n"
                    f"Expected: {total_cells} cells ({expected_data_size} bytes)\n"
                    f"Found: {actual_data_size} bytes ({actual_data_size // 4} values)\n"
                    f"Header: ncols={self.metadata['ncols']}, nrows={self.metadata['nrows']}\n"
                    f"File size: {file_size} bytes\n"
                    f"Run inspect_grd.py to determine correct format"
                )
            
            # Read data
            data_bytes = f.read(expected_data_size)
            data_flat = struct.unpack(f'{total_cells}f', data_bytes)
            
            # Reshape to grid
            self.data = np.array(data_flat).reshape(
                self.metadata['nrows'], 
                self.metadata['ncols']
            )
            
            # Replace nodata with NaN
            nodata = self.metadata['nodata_value']
            self.data[np.abs(self.data - nodata) < 0.01] = np.nan
            
        return self.metadata, self.data
    
    def get_statistics(self):
        """Calculate basic statistics"""
        valid_data = self.data[~np.isnan(self.data)]
        
        stats = {
            'min': float(np.min(valid_data)),
            'max': float(np.max(valid_data)),
            'mean': float(np.mean(valid_data)),
            'median': float(np.median(valid_data)),
            'std': float(np.std(valid_data)),
            'count': int(len(valid_data)),
            'total_cells': int(self.data.size),
            'nodata_cells': int(np.isnan(self.data).sum())
        }
        
        return stats
    
    def get_extent(self):
        """Get geographic extent"""
        xmax = self.metadata['xllcorner'] + (self.metadata['ncols'] * self.metadata['cellsize'])
        ymax = self.metadata['yllcorner'] + (self.metadata['nrows'] * self.metadata['cellsize'])
        
        return {
            'xmin': self.metadata['xllcorner'],
            'ymin': self.metadata['yllcorner'],
            'xmax': xmax,
            'ymax': ymax
        }
    
    def extract_point_value(self, lon, lat):
        """Extract value at specific coordinates"""
        # Convert lat/lon to row/col
        col = int((lon - self.metadata['xllcorner']) / self.metadata['cellsize'])
        row = int((self.metadata['yllcorner'] + (self.metadata['nrows'] * self.metadata['cellsize']) - lat) / self.metadata['cellsize'])
        
        if 0 <= row < self.metadata['nrows'] and 0 <= col < self.metadata['ncols']:
            value = self.data[row, col]
            return float(value) if not np.isnan(value) else None
        return None
