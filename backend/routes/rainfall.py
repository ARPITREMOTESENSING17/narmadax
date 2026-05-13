"""
routes/rainfall.py
All API routes for IMD Rainfall (.grd 0.25 degree) reader.
Registered in app.py as rainfall_bp.
"""

import os
import numpy as np
from datetime import timedelta

from flask import Blueprint, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename

from shared import UPLOAD_FOLDER, OUTPUT_FOLDER, get_start_date, is_imd_daily
from imd_daily_parser import IMDDailyGRDParser
from grd_parser import GRDParser
from data_processor import DataProcessor

# ── Blueprint ─────────────────────────────────────────────────────────
rainfall_bp = Blueprint('rainfall', __name__)

# ── Parser cache ──────────────────────────────────────────────────────
_parser_cache = {}

def _get_parser(filepath: str) -> IMDDailyGRDParser:
    if filepath not in _parser_cache:
        parser = IMDDailyGRDParser(filepath, start_date=get_start_date(filepath))
        parser.parse()
        _parser_cache[filepath] = parser
    return _parser_cache[filepath]

# ── Upload ─────────────────────────────────────────────────────────────
@rainfall_bp.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ('grd',):
        return jsonify({'error': 'Only .grd files are allowed'}), 400

    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Clear stale cache
        _parser_cache.pop(filepath, None)

        file_id    = filename.replace('.grd', '').replace('.GRD', '')
        daily, n_days = is_imd_daily(filepath)
        start_date = get_start_date(filepath)

        if daily:
            parser = _get_parser(filepath)
            return jsonify({
                'file_id':    file_id,
                'filename':   filename,
                'file_type':  'imd_daily',
                'n_days':     n_days,
                'start_date': start_date,
                'metadata': {
                    'ncols':        parser.ncols,
                    'nrows':        parser.nrows,
                    'xllcorner':    parser.xllcorner,
                    'yllcorner':    parser.yllcorner,
                    'cellsize':     parser.cellsize,
                    'nodata_value': parser.nodata_value,
                },
                'statistics_first_day': parser.get_statistics(day_index=0),
            }), 200

        else:
            parser = GRDParser(filepath)
            metadata, data = parser.parse()
            return jsonify({
                'file_id':   file_id,
                'filename':  filename,
                'file_type': 'single_grid',
                'metadata':  metadata,
                'statistics': parser.get_statistics(),
                'extent':    parser.get_extent(),
            }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Export ─────────────────────────────────────────────────────────────
@rainfall_bp.route('/api/export/<file_id>/<fmt>', methods=['GET'])
def export_data(file_id, fmt):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}.grd")
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found. Please re-upload.'}), 404

        daily, n_days = is_imd_daily(filepath)

        if daily:
            parser = _get_parser(filepath)

            if fmt == 'csv_day':
                day_index = int(request.args.get('day', 0))
                day_index = max(0, min(day_index, n_days - 1))
                out = os.path.join(OUTPUT_FOLDER, f"{file_id}_day{day_index}.csv")
                parser.export_day_to_csv(day_index, out)
                return send_file(out, as_attachment=True,
                                 download_name=f"{file_id}_day{day_index}.csv")

            elif fmt == 'csv_all':
                out = os.path.join(OUTPUT_FOLDER, f"{file_id}_all_days.csv")
                parser.export_all_days_to_csv(out)
                return send_file(out, as_attachment=True,
                                 download_name=f"{file_id}_all_days.csv")

            elif fmt == 'csv_range':
                from_day = max(0, int(request.args.get('from', 0)))
                to_day   = min(int(request.args.get('to', n_days - 1)), n_days - 1)
                if from_day > to_day:
                    from_day, to_day = to_day, from_day

                def generate():
                    yield 'day_index,date,latitude,longitude,rainfall_mm\n'
                    for di in range(from_day, to_day + 1):
                        day_date = (parser.start_date + timedelta(days=di)).strftime('%Y-%m-%d')
                        grid = parser.get_day_data(di)
                        for r in range(parser.nrows):
                            for c in range(parser.ncols):
                                val = grid[r, c]
                                if np.isnan(val):
                                    continue
                                lat = parser.yllcorner + r * parser.cellsize + parser.cellsize / 2
                                lon = parser.xllcorner + c * parser.cellsize + parser.cellsize / 2
                                yield f"{di},{day_date},{lat:.4f},{lon:.4f},{val:.4f}\n"

                fd = (parser.start_date + timedelta(days=from_day)).strftime('%Y-%m-%d')
                td = (parser.start_date + timedelta(days=to_day)).strftime('%Y-%m-%d')
                return Response(generate(), mimetype='text/csv',
                    headers={'Content-Disposition':
                             f'attachment; filename={file_id}_{fd}_to_{td}.csv'})

            else:
                return jsonify({'error': 'Use csv_day, csv_range, or csv_all'}), 400

        else:
            parser = GRDParser(filepath)
            metadata, data = parser.parse()
            processor = DataProcessor(metadata, data)

            out_map = {
                'csv':     (f"{file_id}.csv",       processor.to_csv),
                'geotiff': (f"{file_id}.tif",       processor.to_geotiff),
                'ascii':   (f"{file_id}.asc",       processor.to_ascii_grid),
                'stats':   (f"{file_id}_stats.csv", processor.create_summary_stats_csv),
            }
            if fmt not in out_map:
                return jsonify({'error': 'Invalid format'}), 400

            fname, fn = out_map[fmt]
            out = os.path.join(OUTPUT_FOLDER, fname)
            fn(out)
            return send_file(out, as_attachment=True, download_name=fname)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Time Series ────────────────────────────────────────────────────────
@rainfall_bp.route('/api/timeseries/<file_id>', methods=['POST'])
def get_timeseries(file_id):
    try:
        body     = request.get_json()
        lon      = float(body['longitude'])
        lat      = float(body['latitude'])
        from_day = body.get('from_day')
        to_day   = body.get('to_day')

        filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}.grd")
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found. Please re-upload.'}), 404

        parser = _get_parser(filepath)
        ts = parser.get_time_series_at_location(lon, lat)

        if from_day is not None and to_day is not None:
            ts = ts[int(from_day): int(to_day) + 1]

        return jsonify({'longitude': lon, 'latitude': lat, 'time_series': ts}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Point Value ────────────────────────────────────────────────────────
@rainfall_bp.route('/api/point-value/<file_id>', methods=['POST'])
def get_point_value(file_id):
    try:
        body = request.get_json()
        lon  = float(body['longitude'])
        lat  = float(body['latitude'])

        filepath = os.path.join(UPLOAD_FOLDER, f"{file_id}.grd")
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found. Please re-upload.'}), 404

        parser = GRDParser(filepath)
        parser.parse()
        value = parser.extract_point_value(lon, lat)

        return jsonify({'longitude': lon, 'latitude': lat, 'value': value}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500