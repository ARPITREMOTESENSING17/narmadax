import struct
import numpy as np

class ChunkedGRDParser:
    """
    Parser for large .grd files that processes data in chunks
    """
    
    def __init__(self, filepath, chunk_rows=500):
        self.filepath = filepath
        self.chunk_rows = chunk_rows
        self.metadata = {}
        
    def parse_header(self):
        """Parse header only (fast)"""
        with open(self.filepath, 'rb') as f:
            # Try different header formats based on inspector results
            header_bytes = f.read(24)  # Read 24 bytes to try different formats
            
            # Format 1: Try 2 int32 + 4 float32
            f.seek(0)
            header_bytes = f.read(24)
            header = struct.unpack('2i4f', header_bytes)
            
            self.metadata = {
                'ncols': header[0],
                'nrows': header[1],
                'xllcorner': header[2],
                'yllcorner': header[3],
                'cellsize': header[4],
                'nodata_value': header[5],
                'header_size': 24
            }
            
        return self.metadata
    
    def process_in_chunks(self, callback_func):
        """
        Process file in chunks, applying callback_func to each chunk
        
        callback_func: function(chunk_data, chunk_metadata) -> result
        Returns: list of results from each chunk
        """
        
        with open(self.filepath, 'rb') as f:
            # Skip header
            f.seek(self.metadata['header_size'])
            
            results = []
            rows_processed = 0
            
            while rows_processed < self.metadata['nrows']:
                # Calculate chunk size
                rows_to_read = min(self.chunk_rows, self.metadata['nrows'] - rows_processed)
                cells_to_read = rows_to_read * self.metadata['ncols']
                
                # Read chunk
                chunk_bytes = f.read(cells_to_read * 4)
                chunk_flat = struct.unpack(f'{cells_to_read}f', chunk_bytes)
                chunk_data = np.array(chunk_flat).reshape(rows_to_read, self.metadata['ncols'])
                
                # Replace nodata with NaN
                chunk_data[chunk_data == self.metadata['nodata_value']] = np.nan
                
                # Chunk metadata
                chunk_metadata = {
                    'start_row': rows_processed,
                    'end_row': rows_processed + rows_to_read,
                    'nrows': rows_to_read,
                    'ncols': self.metadata['ncols']
                }
                
                # Apply callback
                result = callback_func(chunk_data, chunk_metadata)
                results.append(result)
                
                rows_processed += rows_to_read
                print(f"Processed {rows_processed}/{self.metadata['nrows']} rows...")
            
        return results
    
    def export_to_csv_chunked(self, output_path):
        """Export to CSV in chunks (memory efficient)"""
        
        with open(output_path, 'w') as out_file:
            # Write header
            out_file.write("longitude,latitude,value\n")
            
            def write_chunk(chunk_data, chunk_metadata):
                for row_idx in range(chunk_metadata['nrows']):
                    actual_row = chunk_metadata['start_row'] + row_idx
                    
                    for col_idx in range(chunk_metadata['ncols']):
                        value = chunk_data[row_idx, col_idx]
                        
                        if not np.isnan(value):
                            # Calculate lat/lon
                            lon = self.metadata['xllcorner'] + (col_idx * self.metadata['cellsize']) + (self.metadata['cellsize'] / 2)
                            lat = self.metadata['yllcorner'] + ((self.metadata['nrows'] - actual_row - 1) * self.metadata['cellsize']) + (self.metadata['cellsize'] / 2)
                            
                            out_file.write(f"{lon:.4f},{lat:.4f},{value:.2f}\n")
                
                return None
            
            self.process_in_chunks(write_chunk)
        
        return output_path
    
    def calculate_statistics_chunked(self):
        """Calculate statistics in chunks (memory efficient)"""
        
        all_mins = []
        all_maxs = []
        all_sums = []
        all_counts = []
        
        def calc_chunk_stats(chunk_data, chunk_metadata):
            valid_data = chunk_data[~np.isnan(chunk_data)]
            
            if len(valid_data) > 0:
                return {
                    'min': np.min(valid_data),
                    'max': np.max(valid_data),
                    'sum': np.sum(valid_data),
                    'count': len(valid_data)
                }
            return None
        
        chunk_results = self.process_in_chunks(calc_chunk_stats)
        
        # Aggregate results
        chunk_results = [r for r in chunk_results if r is not None]
        
        stats = {
            'min': min([r['min'] for r in chunk_results]),
            'max': max([r['max'] for r in chunk_results]),
            'mean': sum([r['sum'] for r in chunk_results]) / sum([r['count'] for r in chunk_results]),
            'count': sum([r['count'] for r in chunk_results]),
            'total_cells': self.metadata['ncols'] * self.metadata['nrows']
        }
        
        return stats


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python chunked_grd_parser.py <input.grd>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
    # Create parser
    parser = ChunkedGRDParser(filepath, chunk_rows=500)
    
    # Parse header
    print("Parsing header...")
    metadata = parser.parse_header()
    print(f"Grid: {metadata['ncols']} x {metadata['nrows']}")
    print(f"Cellsize: {metadata['cellsize']}")
    
    # Calculate statistics
    print("\nCalculating statistics (chunked)...")
    stats = parser.calculate_statistics_chunked()
    print(f"Min: {stats['min']:.2f}")
    print(f"Max: {stats['max']:.2f}")
    print(f"Mean: {stats['mean']:.2f}")
    print(f"Valid cells: {stats['count']:,}")
    
    # Export to CSV
    output_file = filepath.replace('.grd', '_chunked.csv')
    print(f"\nExporting to CSV (chunked): {output_file}")
    parser.export_to_csv_chunked(output_file)
    print("Done!")
