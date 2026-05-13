# IMD .grd File Reader & Converter

A simple web platform to read, analyze, and convert IMD Pune .grd files into useful formats.

## Features

- Upload and parse IMD .grd files
- Display metadata (grid dimensions, resolution, extent)
- Calculate statistics (min, max, mean, median, std)
- Export to multiple formats:
  - CSV (lat, lon, value)
  - GeoTIFF (georeferenced raster)
  - ASCII Grid (.asc)
  - Statistics CSV
- Query point values by coordinates

## Setup Instructions

### Quick Start (Windows)

1. **Extract the zip** to `D:\PHD\grd reader`
2. **Double-click** `INSTALL.bat` (installs dependencies)
3. **Double-click** `START_SERVER.bat` (starts server)
4. **Open browser:** `http://localhost:5000`

### Manual Setup

#### 1. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**GeoTIFF Export (Optional):**
- GeoTIFF export requires rasterio
- If you don't need GeoTIFF, skip this
- To enable: `pip install rasterio` or use conda

#### 2. Run the Backend

```bash
cd backend
python app.py
```

Or double-click `START_SERVER.bat`

Server will start at `http://localhost:5000`

#### 3. Open Frontend

Navigate to `http://localhost:5000` in your browser

## Usage

1. Click "Choose File" and select your .grd file
2. Click "Process File"
3. View metadata, statistics, and extent
4. Export to desired format using the export buttons
5. Query specific point values by entering coordinates

## Troubleshooting

### Error: "can only specify one unknown dimension"

This error means your .grd file format doesn't match the expected structure. Run the diagnostic tool:

```bash
cd backend
python inspect_grd.py "path\to\your\file.grd"
```

This will show:
- File size and structure
- Header values
- Data size mismatch details
- Possible issues

**Example:**
```bash
python inspect_grd.py "D:\data\rainfall_2024.grd"
```

The diagnostic output will help identify the correct file format.

---

## File Structure

```
grd_reader_project/
├── backend/
│   ├── app.py                 # Flask API
│   ├── grd_parser.py          # .grd file parser
│   ├── data_processor.py      # Data conversion
│   ├── requirements.txt       # Dependencies
│   └── uploads/               # Uploaded files (temp)
├── frontend/
│   ├── index.html            # Main page
│   ├── css/style.css         # Styling
│   └── js/upload.js          # Frontend logic
├── output/                    # Generated exports
└── README.md
```

## API Endpoints

- `POST /api/upload` - Upload and process .grd file
- `GET /api/export/<file_id>/<format>` - Export to format (csv/geotiff/ascii/stats)
- `POST /api/point-value/<file_id>` - Query value at coordinates

## Notes

- Maximum file size: 100MB
- Supported formats: .grd only
- NoData value is treated as -999
- All exports use EPSG:4326 (WGS84) coordinate system
