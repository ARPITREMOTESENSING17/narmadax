"""
routes/maxtemp.py
All API routes for IMD Max Temperature (.GRD 1.0 degree) reader.
Register in app.py:
    from routes.maxtemp import maxtemp_bp
    app.register_blueprint(maxtemp_bp)

File naming : Maxtemp_MaxT_YYYY  or  Maxtemp_MaxT_YYYY.GRD
Grid        : 31 × 31 = 961 cells/day
Resolution  : 1.0°
"""

import os
from datetime import date, timedelta

from flask import Blueprint, request, jsonify, Response
from shared import UPLOAD_FOLDER, get_start_date
from imd_maxtemp_parser import IMDMaxTempParser

# ── Blueprint ─────────────────────────────────────────────────────────
maxtemp_bp = Blueprint('maxtemp', __name__)

# ── Parser cache ──────────────────────────────────────────────────────
_maxtemp_cache = {}

def _get_parser(filepath: str) -> IMDMaxTempParser:
    if filepath not in _maxtemp_cache:
        parser = IMDMaxTempParser(filepath)
        parser.parse()
        _maxtemp_cache[filepath] = parser
    return _maxtemp_cache[filepath]

def _clear(filepath: str):
    _maxtemp_cache.pop(filepath, None)

def _resolve(file_id: str) -> str:
    """
    Resolve file_id to full filepath.
    Handles: Maxtemp_MaxT_2023.GRD  or  Maxtemp_MaxT_2023 (no ext)
    """
    exact = os.path.join(UPLOAD_FOLDER, file_id)
    if os.path.exists(exact):
        return exact
    for ext in ('.GRD', '.grd'):
        candidate = exact + ext
        if os.path.exists(candidate):
            return candidate
    return exact


# ── Upload ────────────────────────────────────────────────────────────
@maxtemp_bp.route('/api/maxtemp/upload', methods=['POST'])
def maxtemp_upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'No filename'}), 400

    filename = f.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    f.save(filepath)
    _clear(filepath)

    try:
        parser = _get_parser(filepath)
        base   = date.fromisoformat(parser.start_date)
        end    = base + timedelta(days=parser.n_days - 1)

        return jsonify({
            'file_id':    filename,
            'file_type':  'imd_maxtemp',
            'n_days':     parser.n_days,
            'start_date': parser.start_date,
            'end_date':   end.isoformat(),
            'metadata': {
                'ncols':     parser.ncols,
                'nrows':     parser.nrows,
                'cellsize':  parser.cellsize,
                'xllcorner': parser.xllcorner,
                'yllcorner': parser.yllcorner,
            },
            'statistics_first_day': parser.get_statistics(day_idx=0),
            'extent': parser.extent,
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Export all days ───────────────────────────────────────────────────
@maxtemp_bp.route('/api/maxtemp/export/<path:file_id>/csv_all', methods=['GET'])
def maxtemp_export_csv_all(file_id):
    filepath = _resolve(file_id)
    try:
        parser = _get_parser(filepath)
        base   = date.fromisoformat(parser.start_date)

        def generate():
            yield 'day_index,date,latitude,longitude,maxtemp_c\n'
            for di in range(parser.n_days):
                d = (base + timedelta(days=di)).isoformat()
                for lat, lon, val in parser.iter_day_rows(di):
                    yield f'{di},{d},{lat:.4f},{lon:.4f},{val:.4f}\n'

        return Response(generate(), mimetype='text/csv',
            headers={'Content-Disposition':
                     f'attachment; filename={file_id}_all_days.csv'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Export date range ─────────────────────────────────────────────────
@maxtemp_bp.route('/api/maxtemp/export/<path:file_id>/csv_range', methods=['GET'])
def maxtemp_export_csv_range(file_id):
    from_day = int(request.args.get('from', 0))
    to_day   = int(request.args.get('to',   0))
    filepath = _resolve(file_id)

    try:
        parser = _get_parser(filepath)
        base   = date.fromisoformat(parser.start_date)

        def generate():
            yield 'day_index,date,latitude,longitude,maxtemp_c\n'
            for di in range(from_day, to_day + 1):
                d = (base + timedelta(days=di)).isoformat()
                for lat, lon, val in parser.iter_day_rows(di):
                    yield f'{di},{d},{lat:.4f},{lon:.4f},{val:.4f}\n'

        fd    = (base + timedelta(days=from_day)).isoformat()
        td    = (base + timedelta(days=to_day)).isoformat()
        fname = f'{file_id}_{fd}_to_{td}.csv'

        return Response(generate(), mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={fname}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Time series for a point ───────────────────────────────────────────
@maxtemp_bp.route('/api/maxtemp/timeseries/<path:file_id>', methods=['POST'])
def maxtemp_timeseries(file_id):
    body     = request.get_json()
    lon      = body.get('longitude')
    lat      = body.get('latitude')
    from_day = int(body.get('from_day', 0))
    to_day   = body.get('to_day')
    filepath = _resolve(file_id)

    try:
        parser = _get_parser(filepath)
        to     = int(to_day) if to_day is not None else parser.n_days - 1
        ts     = parser.get_timeseries(lon, lat, from_day, to)
        return jsonify({'time_series': ts}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500