"""
routes/spi.py
SPI Calculator API routes — Standard only.
"""

import os
import io
import json
import numpy as np
import pandas as pd
from datetime import datetime

from flask import Blueprint, request, jsonify, Response

from shared import UPLOAD_FOLDER
from spi_engine import (
    daily_to_monthly, calculate_spi_grid,
    drought_statistics, get_spi_category
)

# ── Blueprint ─────────────────────────────────────────────────────────
spi_bp = Blueprint('spi', __name__)

# ── Narmada Basin bounds ───────────────────────────────────────────────
NARMADA_BOUNDS = {
    'lon_min': 72.0, 'lon_max': 82.0,
    'lat_min': 21.0, 'lat_max': 24.5
}

# ── In-memory result cache ─────────────────────────────────────────────
_spi_cache = {}


# ═══════════════════════════════════════════════════════════════════════
# STANDARD SPI SECTION
# ═══════════════════════════════════════════════════════════════════════

@spi_bp.route('/api/spi/calculate', methods=['POST'])
def spi_calculate():
    try:
        scale        = int(request.form.get('scale', 3))
        ref_start_yr = int(request.form.get('ref_start_yr', 1951))
        ref_end_yr   = int(request.form.get('ref_end_yr',   2010))
        basin_filter = request.form.get('basin_filter', 'all')
        single_point = request.form.get('single_point')

        if scale not in (1, 3, 6, 9, 12, 24):
            return jsonify({'error': 'Scale must be 1, 3, 6, 9, 12, or 24'}), 400

        if 'file' in request.files and request.files['file'].filename:
            f    = request.files['file']
            df   = pd.read_csv(f)
            mode = 'csv'
        elif request.form.get('manual_data'):
            raw  = json.loads(request.form.get('manual_data'))
            df   = pd.DataFrame(raw)
            mode = 'manual'
        else:
            return jsonify({'error': 'Provide a CSV file or manual data'}), 400

        required = {'date', 'latitude', 'longitude', 'rainfall_mm'}
        if mode == 'csv' and not required.issubset(df.columns):
            return jsonify({
                'error': f'CSV must have columns: {required}. '
                         f'Found: {list(df.columns)}'
            }), 400

        if mode == 'csv':
            monthly = daily_to_monthly(df)
        else:
            monthly = df

        if basin_filter == 'narmada':
            b = NARMADA_BOUNDS
            monthly = monthly[
                (monthly['longitude'] >= b['lon_min']) &
                (monthly['longitude'] <= b['lon_max']) &
                (monthly['latitude']  >= b['lat_min']) &
                (monthly['latitude']  <= b['lat_max'])
            ]
            if len(monthly) == 0:
                return jsonify({
                    'error': 'No data found within Narmada Basin bounds '
                             '(72-82°E, 21-24.5°N). Check your data extent.'
                }), 400

        if single_point:
            lat_q, lon_q = map(float, single_point.split(','))
            monthly['dist'] = (
                (monthly['latitude']  - lat_q)**2 +
                (monthly['longitude'] - lon_q)**2
            )
            nearest     = monthly.nsmallest(1, 'dist')
            nearest_lat = float(nearest['latitude'].iloc[0])
            nearest_lon = float(nearest['longitude'].iloc[0])
            monthly = monthly[
                (monthly['latitude']  == nearest_lat) &
                (monthly['longitude'] == nearest_lon)
            ]
            monthly = monthly.drop(columns=['dist'], errors='ignore')

        n_points = monthly[['latitude','longitude']].drop_duplicates().shape[0]
        if n_points > 500:
            return jsonify({
                'error': f'Too many grid points ({n_points}). '
                         'Use basin_filter=narmada or select a single point.'
            }), 400

        n_years = monthly['year'].nunique()
        if n_years < 30:
            return jsonify({
                'warning': f'Only {n_years} years of data. '
                           'WMO recommends minimum 30 years for reliable SPI.',
                'n_years': n_years
            }), 200

        spi_df = calculate_spi_grid(monthly, scale, ref_start_yr, ref_end_yr)

        first_pt = spi_df[['latitude','longitude']].drop_duplicates().iloc[0]
        ts = spi_df[
            (spi_df['latitude']  == first_pt['latitude']) &
            (spi_df['longitude'] == first_pt['longitude'])
        ].sort_values(['year','month'])

        chart_labels = [
            f"{int(r['year'])}-{int(r['month']):02d}"
            for _, r in ts.iterrows()
        ]
        chart_spi    = [r['spi']   for _, r in ts.iterrows()]
        chart_colors = [r['color'] for _, r in ts.iterrows()]

        spi_series = ts['spi'].dropna()
        stats = drought_statistics(spi_series)

        cache_key = f"{basin_filter}_{scale}"
        _spi_cache[cache_key] = {
            'spi_df':     spi_df.to_dict('records'),
            'stats':      stats,
            'scale':      scale,
            'n_years':    n_years,
            'ref_period': f'{ref_start_yr}-{ref_end_yr}',
            'n_points':   n_points,
        }

        return jsonify({
            'status':     'success',
            'scale':      scale,
            'n_points':   n_points,
            'n_years':    n_years,
            'ref_period': f'{ref_start_yr}-{ref_end_yr}',
            'statistics': stats,
            'chart': {
                'labels': chart_labels,
                'spi':    chart_spi,
                'colors': chart_colors,
            },
            'point': {
                'lat': float(first_pt['latitude']),
                'lon': float(first_pt['longitude']),
            },
            'cache_key': cache_key,
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@spi_bp.route('/api/spi/export/<cache_key>', methods=['GET'])
def spi_export(cache_key):
    if cache_key not in _spi_cache:
        return jsonify({'error': 'No SPI results found. Calculate first.'}), 404

    cached = _spi_cache[cache_key]
    df     = pd.DataFrame(cached['spi_df'])
    scale  = cached['scale']

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    fname = f'SPI_{scale}_Narmada_{datetime.now().strftime("%Y%m%d")}.csv'
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={fname}'}
    )


@spi_bp.route('/api/spi/point', methods=['POST'])
def spi_point_query():
    body      = request.get_json()
    cache_key = body.get('cache_key')
    lat       = float(body.get('lat'))
    lon       = float(body.get('lon'))

    if cache_key not in _spi_cache:
        return jsonify({'error': 'Calculate SPI first'}), 404

    df = pd.DataFrame(_spi_cache[cache_key]['spi_df'])
    df['dist'] = (df['latitude'] - lat)**2 + (df['longitude'] - lon)**2
    nearest    = df.nsmallest(1, 'dist')
    n_lat      = float(nearest['latitude'].iloc[0])
    n_lon      = float(nearest['longitude'].iloc[0])

    ts = df[(df['latitude'] == n_lat) & (df['longitude'] == n_lon)]\
           .sort_values(['year','month'])

    return jsonify({
        'lat':    n_lat,
        'lon':    n_lon,
        'labels': [f"{int(r['year'])}-{int(r['month']):02d}" for _, r in ts.iterrows()],
        'spi':    [r['spi']   for _, r in ts.iterrows()],
        'colors': [r['color'] for _, r in ts.iterrows()],
        'stats':  drought_statistics(ts['spi'].dropna()),
    }), 200


@spi_bp.route('/api/spi/ai/status', methods=['GET'])
def ai_status():
    """Placeholder — AI feature coming soon."""
    return jsonify({
        'ollama_running': False,
        'models':         [],
        'message':        'AI analysis coming soon.'
    })