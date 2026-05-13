"""
Raw byte inspector for IMD .grd files
Shows actual bytes to understand file structure
"""

import struct
import sys
import os

def inspect_raw_bytes(filepath):
    """Examine raw bytes of .grd file"""
    
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return
    
    with open(filepath, 'rb') as f:
        # Get file size
        f.seek(0, 2)
        file_size = f.tell()
        f.seek(0)
        
        print("=" * 70)
        print("RAW BYTE INSPECTOR - IMD .GRD FILE")
        print("=" * 70)
        print(f"File: {filepath}")
        print(f"Total size: {file_size:,} bytes")
        print()
        
        # Read first 100 bytes
        first_100 = f.read(100)
        
        print("FIRST 100 BYTES (HEX):")
        print("-" * 70)
        for i in range(0, len(first_100), 16):
            hex_str = ' '.join(f'{b:02x}' for b in first_100[i:i+16])
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in first_100[i:i+16])
            print(f"{i:04x}:  {hex_str:<48}  {ascii_str}")
        
        print()
        print("TRYING DIFFERENT INTERPRETATIONS:")
        print("=" * 70)
        
        # Try little-endian int32
        f.seek(0)
        header = struct.unpack('<6i', f.read(24))
        print("\n1. Little-endian int32 (6 values):")
        print(f"   {header}")
        
        # Try big-endian int32
        f.seek(0)
        header = struct.unpack('>6i', f.read(24))
        print("\n2. Big-endian int32 (6 values):")
        print(f"   {header}")
        
        # Try little-endian float32
        f.seek(0)
        header = struct.unpack('<6f', f.read(24))
        print("\n3. Little-endian float32 (6 values):")
        print(f"   {header}")
        
        # Try big-endian float32
        f.seek(0)
        header = struct.unpack('>6f', f.read(24))
        print(f"\n4. Big-endian float32 (6 values):")
        print(f"   {header}")
        
        # Calculate possible grid dimensions
        print("\n" + "=" * 70)
        print("POSSIBLE GRID DIMENSIONS:")
        print("-" * 70)
        
        # Assuming different header sizes
        for header_size in [0, 20, 24, 28, 32]:
            data_bytes = file_size - header_size
            n_values = data_bytes // 4
            
            print(f"\nWith {header_size}-byte header:")
            print(f"  Data bytes: {data_bytes:,}")
            print(f"  Float values: {n_values:,}")
            
            # Try to find square or rectangular grids
            import math
            sqrt_val = math.sqrt(n_values)
            
            if abs(sqrt_val - round(sqrt_val)) < 0.01:
                print(f"  → Could be {int(sqrt_val)} x {int(sqrt_val)} (square grid)")
            
            # Try common IMD grid sizes
            imd_grids = [
                (135, 129),  # 0.25° India
                (270, 258),  # 0.5° India
                (675, 645),  # 0.05° India
                (31, 31),    # Small test grid
                (129, 135),  # Transposed
            ]
            
            for ncols, nrows in imd_grids:
                if ncols * nrows == n_values:
                    print(f"  → Could be {ncols} x {nrows} (matches IMD grid)")
        
        print("\n" + "=" * 70)
        print("ANALYSIS:")
        print("-" * 70)
        
        # Check if it starts with -999 (common nodata marker)
        f.seek(0)
        first_float = struct.unpack('<f', f.read(4))[0]
        print(f"First 4 bytes as float (little-endian): {first_float}")
        
        f.seek(0)
        first_float_big = struct.unpack('>f', f.read(4))[0]
        print(f"First 4 bytes as float (big-endian): {first_float_big}")
        
        # Check if file is all data (no header)
        data_only = file_size // 4
        sqrt_data = math.sqrt(data_only)
        print(f"\nIf NO header (pure data):")
        print(f"  Total values: {data_only:,}")
        print(f"  Square root: {sqrt_data:.2f}")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_raw.py <path_to_grd_file>")
        sys.exit(1)
    
    inspect_raw_bytes(sys.argv[1])
