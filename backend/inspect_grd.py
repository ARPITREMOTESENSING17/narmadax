"""
IMD .grd file format detector
Tries multiple header formats to find the correct one
"""

import struct
import sys
import os

def try_format_1(f, file_size):
    """Try: 6 int32 header values"""
    f.seek(0)
    header_bytes = f.read(24)
    header = struct.unpack('6i', header_bytes)
    
    return {
        'format': 'Format 1: 6 int32 values',
        'header_size': 24,
        'ncols': header[0],
        'nrows': header[1],
        'xllcorner': header[2],
        'yllcorner': header[3],
        'cellsize': header[4],
        'nodata': header[5],
        'expected_cells': header[0] * header[1] if header[0] > 0 and header[1] > 0 else 0,
        'expected_data_bytes': header[0] * header[1] * 4 if header[0] > 0 and header[1] > 0 else 0,
        'actual_data_bytes': file_size - 24
    }

def try_format_2(f, file_size):
    """Try: 4 int32 + 2 float32"""
    f.seek(0)
    header_bytes = f.read(24)
    header = struct.unpack('4i2f', header_bytes)
    
    return {
        'format': 'Format 2: 4 int32 + 2 float32',
        'header_size': 24,
        'ncols': header[0],
        'nrows': header[1],
        'xllcorner': header[2],
        'yllcorner': header[3],
        'cellsize': header[4],
        'nodata': header[5],
        'expected_cells': header[0] * header[1] if header[0] > 0 and header[1] > 0 else 0,
        'expected_data_bytes': header[0] * header[1] * 4 if header[0] > 0 and header[1] > 0 else 0,
        'actual_data_bytes': file_size - 24
    }

def try_format_3(f, file_size):
    """Try: 2 int32 + 4 float32"""
    f.seek(0)
    header_bytes = f.read(24)
    header = struct.unpack('2i4f', header_bytes)
    
    return {
        'format': 'Format 3: 2 int32 + 4 float32',
        'header_size': 24,
        'ncols': header[0],
        'nrows': header[1],
        'xllcorner': header[2],
        'yllcorner': header[3],
        'cellsize': header[4],
        'nodata': header[5],
        'expected_cells': header[0] * header[1] if header[0] > 0 and header[1] > 0 else 0,
        'expected_data_bytes': header[0] * header[1] * 4 if header[0] > 0 and header[1] > 0 else 0,
        'actual_data_bytes': file_size - 24
    }

def try_format_4(f, file_size):
    """Try: 2 int32 + 2 float64 (double precision)"""
    f.seek(0)
    header_bytes = f.read(24)
    header = struct.unpack('2i2d', header_bytes)
    
    return {
        'format': 'Format 4: 2 int32 + 2 float64',
        'header_size': 24,
        'ncols': header[0],
        'nrows': header[1],
        'xllcorner': header[2],
        'yllcorner': header[3],
        'cellsize': 'unknown',
        'nodata': 'unknown',
        'expected_cells': header[0] * header[1] if header[0] > 0 and header[1] > 0 else 0,
        'expected_data_bytes': header[0] * header[1] * 4 if header[0] > 0 and header[1] > 0 else 0,
        'actual_data_bytes': file_size - 24
    }

def inspect_grd(filepath):
    """Inspect .grd file and try different formats"""
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return
    
    with open(filepath, 'rb') as f:
        # Get file size
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0)
        
        print("=" * 70)
        print("IMD .GRD FILE FORMAT DETECTOR")
        print("=" * 70)
        print(f"File: {filepath}")
        print(f"Total file size: {file_size:,} bytes")
        print()
        
        # Check if ASCII
        f.seek(0)
        first_bytes = f.read(100)
        try:
            text = first_bytes.decode('ascii')
            if 'ncols' in text.lower() or 'nrows' in text.lower():
                print("✓ ASCII FORMAT DETECTED (like .asc file):")
                print("-" * 70)
                print(text[:200])
                print("\nThis is an ASCII grid file, not binary .grd")
                print("=" * 70)
                return
        except:
            pass
        
        # Try binary formats
        formats = [
            try_format_1(f, file_size),
            try_format_2(f, file_size),
            try_format_3(f, file_size),
            try_format_4(f, file_size),
        ]
        
        print("TESTING BINARY FORMATS:")
        print("=" * 70)
        
        valid_formats = []
        
        for i, fmt in enumerate(formats, 1):
            print(f"\n{fmt['format']}")
            print("-" * 70)
            print(f"  ncols:              {fmt['ncols']}")
            print(f"  nrows:              {fmt['nrows']}")
            print(f"  xllcorner:          {fmt['xllcorner']}")
            print(f"  yllcorner:          {fmt['yllcorner']}")
            print(f"  cellsize:           {fmt['cellsize']}")
            print(f"  nodata:             {fmt['nodata']}")
            print(f"  Expected cells:     {fmt['expected_cells']:,}")
            print(f"  Expected data:      {fmt['expected_data_bytes']:,} bytes")
            print(f"  Actual data:        {fmt['actual_data_bytes']:,} bytes")
            
            # Check if valid
            is_valid = (
                fmt['ncols'] > 0 and fmt['ncols'] < 10000 and
                fmt['nrows'] > 0 and fmt['nrows'] < 10000 and
                abs(fmt['expected_data_bytes'] - fmt['actual_data_bytes']) < 100
            )
            
            if is_valid:
                print(f"  ✓ MATCH! This format looks correct!")
                valid_formats.append((i, fmt))
            else:
                diff = fmt['actual_data_bytes'] - fmt['expected_data_bytes']
                print(f"  ✗ Mismatch (difference: {diff:,} bytes)")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY:")
        print("=" * 70)
        if valid_formats:
            print(f"✓ Found {len(valid_formats)} valid format(s):")
            for idx, fmt in valid_formats:
                print(f"\n  {fmt['format']}")
                print(f"    Grid: {fmt['ncols']} x {fmt['nrows']} cells")
                print(f"    Extent: ({fmt['xllcorner']}, {fmt['yllcorner']})")
                print(f"    Cellsize: {fmt['cellsize']}")
        else:
            print("✗ No standard format matched!")
            print("\nPlease share:")
            print("  1. File source (IMD website URL?)")
            print("  2. Data type (rainfall/temp/etc)")
            print("  3. Grid coverage area")
        
        print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_grd.py <path_to_grd_file>")
        print('Example: python inspect_grd.py "rainfall.grd"')
        sys.exit(1)
    
    inspect_grd(sys.argv[1])
