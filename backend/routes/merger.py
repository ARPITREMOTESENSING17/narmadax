"""
routes/merger.py
─────────────────────────────────────────────────────────────────
CSV Merger — Merge multiple IMDTools CSV exports into one file.
Supports Rainfall, MinTemp, MaxTemp CSVs.
"""

import os
import io
import pandas as pd
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from werkzeug.utils import secure_filename

merger_bp = Blueprint('merger', __name__)

# ── In-memory result cache ─────────────────────────────────────────────
_merged_cache = {}   # key → { df, summary }


def _detect_dtype(df: pd.DataFrame) -> str:
    """Detect data type from CSV columns."""
    cols = set(df.columns)
    if 'rainfall_mm'  in cols: return 'rainfall'
    if 'mintemp_c'    in cols: return 'mintemp'
    if 'maxtemp_c'    in cols: return 'maxtemp'
    return 'unknown'


def _value_col(dtype: str) -> str:
    return {
        'rainfall': 'rainfall_mm',
        'mintemp':  'mintemp_c',
        'maxtemp':  'maxtemp_c',
    }.get(dtype, 'value')


@merger_bp.route('/api/merger/merge', methods=['POST'])
def merge_csvs():
    """
    Merge multiple CSV files uploaded at once.

    Accepts: multipart/form-data with multiple 'files'
    Returns: JSON with summary + cache_key for download
    """
    files = request.files.getlist('files')

    if not files or len(files) == 0:
        return jsonify({'error': 'No files uploaded'}), 400
    if len(files) < 2:
        return jsonify({'error': 'Upload at least 2 CSV files to merge'}), 400
    if len(files) > 100:
        return jsonify({'error': 'Maximum 100 files at once'}), 400

    dfs       = []
    file_info = []
    dtype     = None

    for f in files:
        if not f.filename.endswith('.csv'):
            return jsonify({'error': f'{f.filename} is not a CSV file'}), 400

        try:
            df = pd.read_csv(f)
        except Exception as e:
            return jsonify({'error': f'Could not read {f.filename}: {str(e)}'}), 400

        # Validate required columns
        required = {'date', 'latitude', 'longitude'}
        if not required.issubset(df.columns):
            return jsonify({
                'error': f'{f.filename} missing columns. '
                         f'Need: date, latitude, longitude. '
                         f'Found: {list(df.columns)}'
            }), 400

        # Detect and validate data type consistency
        ftype = _detect_dtype(df)
        if dtype is None:
            dtype = ftype
        elif ftype != dtype and ftype != 'unknown':
            return jsonify({
                'error': f'Mixed data types! '
                         f'Cannot merge {dtype} with {ftype}. '
                         f'Merge same type files only.'
            }), 400

        file_info.append({
            'filename': f.filename,
            'rows':     len(df),
            'dtype':    ftype,
        })
        dfs.append(df)

    # ── Merge ──────────────────────────────────────────────────────────
    merged = pd.concat(dfs, ignore_index=True)
    rows_before = len(merged)

    # Remove duplicates on date + lat + lon
    merged = merged.drop_duplicates(
        subset=['date', 'latitude', 'longitude'],
        keep='first'
    )
    rows_after = len(merged)
    dupes_removed = rows_before - rows_after

    # Sort by lat, lon, date
    merged['date'] = pd.to_datetime(merged['date'])
    merged = merged.sort_values(['latitude', 'longitude', 'date'])
    merged['date'] = merged['date'].dt.strftime('%Y-%m-%d')

    # ── Summary ────────────────────────────────────────────────────────
    dates      = pd.to_datetime(merged['date'])
    date_min   = dates.min().strftime('%Y-%m-%d')
    date_max   = dates.max().strftime('%Y-%m-%d')
    n_years    = dates.dt.year.nunique()
    n_points   = merged[['latitude','longitude']].drop_duplicates().shape[0]
    vcol       = _value_col(dtype)
    value_info = {}
    if vcol in merged.columns:
        vals = pd.to_numeric(merged[vcol], errors='coerce')
        value_info = {
            'mean': round(float(vals.mean()), 3),
            'min':  round(float(vals.min()),  3),
            'max':  round(float(vals.max()),  3),
        }

    # Cache for download
    cache_key = f"merged_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    _merged_cache[cache_key] = {
        'df':    merged,
        'dtype': dtype,
        'date_min': date_min,
        'date_max': date_max,
    }

    return jsonify({
        'status':        'success',
        'cache_key':     cache_key,
        'dtype':         dtype,
        'files_merged':  len(files),
        'rows_total':    rows_after,
        'dupes_removed': dupes_removed,
        'date_min':      date_min,
        'date_max':      date_max,
        'n_years':       n_years,
        'n_points':      n_points,
        'value_info':    value_info,
        'value_col':     vcol,
        'file_info':     file_info,
    }), 200


@merger_bp.route('/api/merger/download/<cache_key>', methods=['GET'])
def merger_download(cache_key):
    """Download merged CSV."""
    if cache_key not in _merged_cache:
        return jsonify({'error': 'Session expired. Please merge again.'}), 404

    cached   = _merged_cache[cache_key]
    df       = cached['df']
    dtype    = cached['dtype']
    date_min = cached['date_min'].replace('-', '')
    date_max = cached['date_max'].replace('-', '')

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    fname = f'{dtype}_merged_{date_min}_to_{date_max}.csv'
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={fname}'}
    )