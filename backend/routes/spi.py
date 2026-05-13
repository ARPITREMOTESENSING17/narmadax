"""
routes/spi.py
─────────────────────────────────────────────────────────────────
SPI Calculator API routes.
Two sections:
  Standard → Any region, pure SPI calculation
  AI        → Narmada Basin only, Ollama-powered analysis

Register in app.py:
  from routes.spi import spi_bp
  app.register_blueprint(spi_bp)
"""

import os
import io
import json
import numpy as np
import pandas as pd
from datetime import datetime

from flask import Blueprint, request, jsonify, Response, stream_with_context

from shared import UPLOAD_FOLDER
from spi_engine import (
    daily_to_monthly, calculate_spi_grid,
    drought_statistics, get_spi_category
)
from narmada_context import (
    SYSTEM_PROMPT, NARMADA_BOUNDS,
    build_interpretation_prompt, build_pattern_prompt,
    build_gde_impact_prompt, build_qa_prompt
)
from ollama_client import is_ollama_running, generate, _stream_generate

# ── Blueprint ─────────────────────────────────────────────────────────
spi_bp = Blueprint('spi', __name__)

# ── In-memory result cache ─────────────────────────────────────────────
# Stores last SPI result per session (keyed by upload filename)
_spi_cache = {}


# ═══════════════════════════════════════════════════════════════════════
# STANDARD SPI SECTION
# ═══════════════════════════════════════════════════════════════════════

@spi_bp.route('/api/spi/calculate', methods=['POST'])
def spi_calculate():
    """
    Main SPI calculation endpoint.

    Accepts:
      - CSV file upload  (from IMDTools Rainfall Reader)
      - OR JSON body with manual monthly values

    Body params:
      scale         : int  (1, 3, 6, 9, 12, 24)
      ref_start_yr  : int  (default 1951)
      ref_end_yr    : int  (default 2010)
      basin_filter  : str  ('narmada' | 'all')
      single_point  : {lat, lon} optional

    Returns:
      JSON with spi_data, statistics, chart_data
    """
    try:
        scale        = int(request.form.get('scale', 3))
        ref_start_yr = int(request.form.get('ref_start_yr', 1951))
        ref_end_yr   = int(request.form.get('ref_end_yr',   2010))
        basin_filter = request.form.get('basin_filter', 'all')
        single_point = request.form.get('single_point')  # "lat,lon"

        # ── Validate scale ────────────────────────────────────────────
        if scale not in (1, 3, 6, 9, 12, 24):
            return jsonify({'error': 'Scale must be 1, 3, 6, 9, 12, or 24'}), 400

        # ── Load data ─────────────────────────────────────────────────
        if 'file' in request.files and request.files['file'].filename:
            # CSV upload from IMDTools
            f    = request.files['file']
            df   = pd.read_csv(f)
            mode = 'csv'
        elif request.form.get('manual_data'):
            # Manual JSON data
            raw  = json.loads(request.form.get('manual_data'))
            df   = pd.DataFrame(raw)
            mode = 'manual'
        else:
            return jsonify({'error': 'Provide a CSV file or manual data'}), 400

        # ── Validate columns ──────────────────────────────────────────
        required = {'date', 'latitude', 'longitude', 'rainfall_mm'}
        if mode == 'csv' and not required.issubset(df.columns):
            return jsonify({
                'error': f'CSV must have columns: {required}. '
                         f'Found: {list(df.columns)}'
            }), 400

        # ── Aggregate to monthly ──────────────────────────────────────
        if mode == 'csv':
            monthly = daily_to_monthly(df)
        else:
            # Manual data already monthly
            monthly = df

        # ── Basin filter ──────────────────────────────────────────────
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

        # ── Single point filter ───────────────────────────────────────
        if single_point:
            lat_q, lon_q = map(float, single_point.split(','))
            # Find nearest grid point
            monthly['dist'] = (
                (monthly['latitude']  - lat_q)**2 +
                (monthly['longitude'] - lon_q)**2
            )
            nearest = monthly.nsmallest(1, 'dist')
            nearest_lat = float(nearest['latitude'].iloc[0])
            nearest_lon = float(nearest['longitude'].iloc[0])
            monthly = monthly[
                (monthly['latitude']  == nearest_lat) &
                (monthly['longitude'] == nearest_lon)
            ]
            monthly = monthly.drop(columns=['dist'], errors='ignore')

        # ── Calculate SPI ─────────────────────────────────────────────
        n_points = monthly[['latitude','longitude']].drop_duplicates().shape[0]
        if n_points > 500:
            return jsonify({
                'error': f'Too many grid points ({n_points}). '
                         'Use basin_filter=narmada or select a single point.'
            }), 400

        # Check minimum years
        n_years = monthly['year'].nunique()
        if n_years < 30:
            return jsonify({
                'warning': f'Only {n_years} years of data. '
                           'WMO recommends minimum 30 years for reliable SPI.',
                'n_years': n_years
            }), 200

        spi_df = calculate_spi_grid(
            monthly, scale, ref_start_yr, ref_end_yr
        )

        # ── Build response ────────────────────────────────────────────
        # Time series for first/only point (for chart)
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

        # Statistics for that point
        spi_series = ts['spi'].dropna()
        stats = drought_statistics(spi_series)

        # Cache result for AI analysis
        cache_key = f"{basin_filter}_{scale}"
        _spi_cache[cache_key] = {
            'spi_df':   spi_df.to_dict('records'),
            'stats':    stats,
            'scale':    scale,
            'n_years':  n_years,
            'ref_period': f'{ref_start_yr}-{ref_end_yr}',
            'n_points': n_points,
        }

        return jsonify({
            'status':      'success',
            'scale':       scale,
            'n_points':    n_points,
            'n_years':     n_years,
            'ref_period':  f'{ref_start_yr}-{ref_end_yr}',
            'statistics':  stats,
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
    """Export SPI results as CSV."""
    if cache_key not in _spi_cache:
        return jsonify({'error': 'No SPI results found. Please calculate first.'}), 404

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
    """
    Get SPI time series for a specific lat/lon point
    from already-calculated results.
    """
    body      = request.get_json()
    cache_key = body.get('cache_key')
    lat       = float(body.get('lat'))
    lon       = float(body.get('lon'))

    if cache_key not in _spi_cache:
        return jsonify({'error': 'Calculate SPI first'}), 404

    df = pd.DataFrame(_spi_cache[cache_key]['spi_df'])

    # Find nearest point
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
        'spi':    [r['spi']    for _, r in ts.iterrows()],
        'colors': [r['color']  for _, r in ts.iterrows()],
        'stats':  drought_statistics(ts['spi'].dropna()),
    }), 200


# ═══════════════════════════════════════════════════════════════════════
# AI SPI SECTION — Narmada Basin Only
# ═══════════════════════════════════════════════════════════════════════

@spi_bp.route('/api/spi/ai/status', methods=['GET'])
def ai_status():
    """Check if Ollama is running and which models are available."""
    from ollama_client import get_available_models
    running = is_ollama_running()
    models  = get_available_models() if running else []
    return jsonify({
        'ollama_running': running,
        'models':         models,
        'recommended':    'llama3.1',
    })


@spi_bp.route('/api/spi/ai/interpret', methods=['POST'])
def ai_interpret():
    """
    AI interpretation of SPI results (streaming).
    Narmada Basin only.

    Body: { cache_key, analysis_type }
    analysis_type: 'interpretation' | 'patterns' | 'gde_impact'
    """
    body          = request.get_json()
    cache_key     = body.get('cache_key')
    analysis_type = body.get('analysis_type', 'interpretation')
    model         = body.get('model', 'llama3.1')

    if cache_key not in _spi_cache:
        return jsonify({'error': 'Calculate SPI first'}), 404

    if not is_ollama_running():
        return jsonify({
            'error': 'Ollama is not running. '
                     'Please install from https://ollama.com and run: ollama serve'
        }), 503

    cached = _spi_cache[cache_key]
    stats  = cached['stats']
    scale  = cached['scale']
    period = cached['ref_period']

    # Build prompt based on analysis type
    if analysis_type == 'interpretation':
        prompt = build_interpretation_prompt(stats, scale, period)
    elif analysis_type == 'patterns':
        prompt = build_pattern_prompt(
            stats, scale, stats.get('decade_drought_freq', {})
        )
    elif analysis_type == 'gde_impact':
        prompt = build_gde_impact_prompt(stats)
    else:
        return jsonify({'error': f'Unknown analysis_type: {analysis_type}'}), 400

    # Stream response from Ollama
    def generate_stream():
        for chunk in _stream_generate({
            'model':  model,
            'prompt': prompt,
            'system': SYSTEM_PROMPT,
            'stream': True,
            'options': {'temperature': 0.3, 'num_predict': 800}
        }):
            yield chunk

    return Response(
        stream_with_context(generate_stream()),
        mimetype='text/plain',
        headers={'X-Accel-Buffering': 'no'}
    )


@spi_bp.route('/api/spi/ai/ask', methods=['POST'])
def ai_ask():
    """
    Q&A on SPI results using Ollama (streaming).
    User asks a natural language question about their data.
    """
    body      = request.get_json()
    cache_key = body.get('cache_key')
    question  = body.get('question', '').strip()
    model     = body.get('model', 'llama3.1')

    if not question:
        return jsonify({'error': 'Please provide a question'}), 400

    if cache_key not in _spi_cache:
        return jsonify({'error': 'Calculate SPI first'}), 404

    if not is_ollama_running():
        return jsonify({
            'error': 'Ollama is not running. '
                     'Please run: ollama serve'
        }), 503

    cached = _spi_cache[cache_key]
    prompt = build_qa_prompt(question, cached['stats'], cached['scale'])

    def generate_stream():
        for chunk in _stream_generate({
            'model':  model,
            'prompt': prompt,
            'system': SYSTEM_PROMPT,
            'stream': True,
            'options': {'temperature': 0.4, 'num_predict': 600}
        }):
            yield chunk

    return Response(
        stream_with_context(generate_stream()),
        mimetype='text/plain',
        headers={'X-Accel-Buffering': 'no'}
    )