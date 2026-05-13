"""
narmada_context.py
─────────────────────────────────────────────────────────────────
Narmada Basin knowledge base for Ollama AI prompts.
This file contains:
  - Basin geography and boundaries
  - Sub-basin definitions
  - Climate context
  - Hydrological context
  - Ecological context (GDEs - PhD focus)
  - Prompt templates for different analysis types
"""

# ── Basin Boundary (approximate grid cells at 0.25° resolution) ───────
# Narmada Basin: 72°E–82°E, 21°N–24°N approximately
NARMADA_BOUNDS = {
    'lon_min': 72.0,
    'lon_max': 82.0,
    'lat_min': 21.0,
    'lat_max': 24.5,
}

# ── Sub-basin definitions ──────────────────────────────────────────────
NARMADA_SUBBASINS = {
    'upper': {
        'name':    'Upper Narmada',
        'lon_min': 78.0, 'lon_max': 82.0,
        'lat_min': 22.0, 'lat_max': 24.0,
        'description': 'Originates at Amarkantak, hilly terrain, '
                       'dense forest cover, tribal areas of MP',
        'major_features': ['Amarkantak origin', 'Bargi Dam',
                           'Jabalpur', 'Mandla district'],
    },
    'middle': {
        'name':    'Middle Narmada',
        'lon_min': 76.0, 'lon_max': 78.0,
        'lat_min': 21.5, 'lat_max': 23.5,
        'description': 'Agricultural heartland, major irrigation, '
                       'Marble Rocks at Bhedaghat',
        'major_features': ['Indira Sagar Dam', 'Omkareshwar Dam',
                           'Hoshangabad', 'Narsinghpur'],
    },
    'lower': {
        'name':    'Lower Narmada',
        'lon_min': 72.0, 'lon_max': 76.0,
        'lat_min': 21.0, 'lat_max': 23.0,
        'description': 'Enters Gujarat, estuarine zone, '
                       'Sardar Sarovar command area',
        'major_features': ['Sardar Sarovar Dam', 'Bharuch',
                           'Gulf of Khambhat', 'Rajpipla'],
    },
}

# ── System context for Ollama ──────────────────────────────────────────
SYSTEM_PROMPT = """You are a climate scientist and hydrologist specializing 
in the Narmada River Basin, central India. You have deep expertise in:

BASIN GEOGRAPHY:
- Narmada Basin: 98,796 km², spanning Madhya Pradesh (87%), 
  Maharashtra (7%), Gujarat (6%)
- River length: 1,312 km, flowing west from Amarkantak to Gulf of Khambhat
- Major tributaries: Tawa, Burhner, Banjar, Hiran, Orsang, Goi
- Major dams: Sardar Sarovar (Gujarat), Indira Sagar (MP), 
  Bargi (MP), Omkareshwar (MP), Tawa (MP)

CLIMATE:
- Semi-arid to sub-humid tropical climate
- Monsoon: June-September (90% of annual rainfall)
- Annual rainfall: 800-1600 mm (upper) to 600-900 mm (lower basin)
- Pre-monsoon: March-May (hot and dry)
- Post-monsoon: October-November (retreating monsoon)
- Winter: December-February (cool and dry)
- ENSO influence: El Niño years associated with below-normal monsoon

HYDROLOGY:
- Perennial river with strong seasonal flow variation
- Reservoir storage critical for irrigation and drinking water
- Groundwater recharge primarily during monsoon (June-September)
- Low flow season: February-May (critical for ecosystems)
- Flood events: July-September (major flood risk at Bharuch)

ECOLOGY (PhD RESEARCH FOCUS):
- Groundwater Dependent Ecosystems (GDEs) along river banks
- Riparian forests highly sensitive to low flow conditions
- Aquatic biodiversity hotspot (mahseer, gharial habitat)
- Wetlands: Tawa reservoir, Son Gharana, riparian wetlands
- GDE stress occurs when SPI-12 < -1.0 for 2+ consecutive months

DROUGHT CONTEXT:
- Notable drought years: 1965, 1972, 1979, 1987, 2002, 2009, 2015
- 2002 was worst drought in modern record (SPI < -2.0 in upper basin)
- Agricultural drought (SPI-3 < -1.0) affects Kharif crop severely
- Hydrological drought (SPI-12 < -1.5) affects reservoir levels
- Recent trend (1990-2020): slight drying in upper basin

RESPOND:
- In clear, scientific but accessible language
- With specific references to Narmada sub-basins when relevant
- Connecting drought to water resources, agriculture, and ecosystems
- In 2-4 paragraphs unless asked for more
- With specific numbers from the data provided"""


# ── Prompt templates ───────────────────────────────────────────────────

def build_interpretation_prompt(stats: dict, scale: int,
                                 period: str) -> str:
    """Generate interpretation prompt for SPI results."""
    return f"""Analyze the following SPI-{scale} results for the Narmada Basin
for the period {period}:

STATISTICS:
- Total months analyzed: {stats.get('total_months', 'N/A')}
- Drought months (SPI ≤ -1.0): {stats.get('drought_months', 'N/A')} 
  ({stats.get('drought_pct', 'N/A')}% of record)
- Severe drought months (SPI ≤ -1.5): {stats.get('severe_drought_months', 'N/A')}
- Extreme drought months (SPI ≤ -2.0): {stats.get('extreme_drought_months', 'N/A')}
- Longest consecutive drought spell: {stats.get('longest_drought_spell', 'N/A')} months
- Mean SPI: {stats.get('mean_spi', 'N/A')}
- Minimum SPI: {stats.get('min_spi', 'N/A')}
- Decade drought frequency: {stats.get('decade_drought_freq', {})}

Please provide:
1. Overall drought characterization for this timescale
2. Most significant drought events and their likely impacts
3. Temporal trend (is drought increasing/decreasing?)
4. Implications for water resources and groundwater dependent ecosystems
5. One key finding suitable for a PhD thesis statement"""


def build_pattern_prompt(stats: dict, scale: int,
                          decade_data: dict) -> str:
    """Generate pattern detection prompt."""
    return f"""Analyze drought patterns and trends in the Narmada Basin 
based on SPI-{scale} results:

DECADE-WISE DROUGHT FREQUENCY:
{decade_data}

OVERALL STATISTICS:
- Mean SPI: {stats.get('mean_spi')}
- Drought frequency: {stats.get('drought_pct')}%
- Extreme drought months: {stats.get('extreme_drought_months')}

Identify:
1. Multi-decadal patterns or cycles
2. Whether drought frequency is increasing in recent decades
3. Connection to known climate drivers (ENSO, IOD)
4. Implications for future water security in Narmada Basin
5. Comparison with known drought years (1972, 1987, 2002, 2015)"""


def build_gde_impact_prompt(spi12_stats: dict) -> str:
    """Generate GDE impact assessment prompt (PhD-specific)."""
    return f"""Assess the impact of drought conditions on Groundwater Dependent 
Ecosystems (GDEs) in the Narmada Basin based on SPI-12 results:

SPI-12 STATISTICS:
- Drought months: {spi12_stats.get('drought_months')} 
  ({spi12_stats.get('drought_pct')}% of record)
- Severe drought months: {spi12_stats.get('severe_drought_months')}
- Longest drought spell: {spi12_stats.get('longest_drought_spell')} months
- Recent decade drought frequency: {spi12_stats.get('decade_drought_freq', {}).get('2010s', 'N/A')}%

Provide scientific assessment of:
1. Cumulative stress on riparian GDEs during identified drought periods
2. Groundwater recharge deficit implications (SPI-12 as proxy)
3. Critical thresholds for ecosystem response
4. Which sub-basins (upper/middle/lower) face highest GDE risk
5. Connection to your PhD research on aquatic groundwater-dependent
   ecosystems in the Narmada Basin
This analysis is for a PhD thesis on climate change impacts on 
aquatic groundwater-dependent ecosystems."""


def build_qa_prompt(question: str, stats: dict, scale: int) -> str:
    """Build Q&A prompt from user question + SPI context."""
    return f"""Based on the SPI-{scale} analysis of the Narmada Basin:

DATA SUMMARY:
- Drought frequency: {stats.get('drought_pct')}%
- Mean SPI: {stats.get('mean_spi')}
- Worst drought SPI: {stats.get('min_spi')}
- Decade trends: {stats.get('decade_drought_freq', {})}

USER QUESTION: {question}

Answer specifically using the data provided and your knowledge 
of the Narmada Basin. Be concise and scientific."""