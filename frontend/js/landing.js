// ============================================================
//  IMDTools Suite — Landing Page
//  React (CDN, no build step), no Tailwind
// ============================================================

const { useState } = React;

// ── Data ─────────────────────────────────────────────────────

const CONVERTERS = [
  {
    id: 'rainfall',
    icon: '🌧',
    name: 'Rainfall Reader',
    desc: 'Parse IMD daily rainfall binary files. Export to CSV, query any point, explore date ranges with an interactive calendar picker.',
    tags: ['0.25° × 0.25°', 'Daily', '.grd format'],
    status: 'live',
    pricing: 'free',
    url: '/rainfall',
  },
  {
    id: 'maxtemp',
    icon: '🌡',
    name: 'Max Temperature Reader',
    desc: 'Process IMD gridded maximum temperature data. Analyse heatwave patterns, seasonal extremes, and warming trends across India.',
    tags: ['1.0° × 1.0°', 'Daily', '.grd format'],
    status: 'live',
    pricing: 'free',
    url: '/maxtemp',
  },
  {
    id: 'mintemp',
    icon: '❄',
    name: 'Min Temperature Reader',
    desc: 'Process IMD gridded minimum temperature data. Track cold wave events, frost days, and diurnal temperature range.',
    tags: ['1.0° × 1.0°', 'Daily', 'MinT_YYYY'],
    status: 'live',
    pricing: 'free',
    url: '/mintemp',
  },
  {
    id: 'netcdf',
    icon: '🔷',
    name: 'NetCDF Converter',
    desc: 'Convert IMD NetCDF files with multiple variables, automatic unit conversion (K→°C, kg/m²/s→mm/day), and metadata inspection.',
    tags: ['.nc format', 'Multi-variable', 'Auto unit convert'],
    status: 'planned',
    pricing: 'paid',
    price: '₹499/mo',
    url: null,
  },
];

const CALCULATORS = [
  {
    id: 'spi',
    icon: '💧',
    name: 'SPI Calculator',
    desc: 'Standardized Precipitation Index at SPI-1, 3, 6, 9 and 12 timescales. WMO standard drought metric with AI-powered Narmada Basin analysis.',
    tags: ['SPI-1 to SPI-24', 'AI-Powered', 'Narmada Basin'],
    status: 'live',
    pricing: 'free',
    price: '₹299/mo',
    url: '/spi',
  },
  {
    id: 'spei',
    icon: '🌡',
    name: 'SPEI Calculator',
    desc: 'Standardized Precipitation Evapotranspiration Index. Combines rainfall and temperature for climate-change-aware drought assessment.',
    tags: ['Rainfall + Temp', 'SPEI-1 to 12', 'Climate change'],
    status: 'planned',
    pricing: 'paid',
    price: '₹299/mo',
    url: null,
  },
  {
    id: 'trend',
    icon: '📈',
    name: 'Trend Analyzer',
    desc: 'Mann-Kendall trend test and Sen\'s slope pixel-by-pixel. Detect statistically significant rainfall trends over 25+ years.',
    tags: ['Mann-Kendall', 'Sen\'s Slope', 'Trend maps'],
    status: 'planned',
    pricing: 'paid',
    price: '₹299/mo',
    url: null,
  },
  {
    id: 'extreme',
    icon: '⚡',
    name: 'Extreme Rain Analyzer',
    desc: 'ETCCDI standard indices — R10mm, R20mm, CDD, CWD, Rx1day, Rx5day. Quantify flood and drought extreme events.',
    tags: ['ETCCDI indices', 'Extremes', 'Return period'],
    status: 'planned',
    pricing: 'paid',
    price: '₹299/mo',
    url: null,
  },
  {
    id: 'monsoon',
    icon: '🌀',
    name: 'Monsoon Analyzer',
    desc: 'Monsoon onset and withdrawal dates, active and break spells, ISMR calculation, and inter-annual variability analysis.',
    tags: ['Onset/Withdrawal', 'Active spells', 'ISMR'],
    status: 'planned',
    pricing: 'paid',
    price: '₹299/mo',
    url: null,
  },
];

const TECH_ITEMS = [
  { icon: '🐍', label: 'Python / Flask' },
  { icon: '⚛',  label: 'React' },
  { icon: '🗄',  label: 'PostGIS' },
  { icon: '🗺',  label: 'Leaflet.js' },
  { icon: '📡',  label: 'IMD Gridded Data' },
  { icon: '🛰',  label: 'Remote Sensing' },
];

// ── Small Components ──────────────────────────────────────────

function StatusBadge({ status }) {
  const map = {
    live:    ['status-live',    'Live'],
    soon:    ['status-soon',    'Coming Soon'],
    planned: ['status-planned', 'Planned'],
  };
  const [cls, label] = map[status] || map.planned;
  return React.createElement('div', { className: `card-status ${cls}` }, label);
}

function PricingBadge({ pricing, price }) {
  if (pricing === 'free')
    return React.createElement('div', { className: 'pricing-badge pricing-free' }, '✦ Free');
  return React.createElement('div', { className: 'pricing-badge pricing-paid' }, `💰 ${price}`);
}

function MetaTag({ label }) {
  return React.createElement('span', { className: 'meta-tag' }, label);
}

// ── Product Card ──────────────────────────────────────────────
function ProductCard({ product, accent }) {
  const isLive = product.status === 'live';
  const BtnEl  = isLive ? 'a' : 'button';
  const btnLabel = isLive ? 'Open Tool'
    : product.status === 'soon' ? 'Coming Soon' : 'Planned';

  return React.createElement('div', {
    className: `product-card ${!isLive ? 'card-muted' : ''}`
  },
    React.createElement('div', { className: `card-accent accent-${accent}` }),
    React.createElement('div', { className: 'card-body-wrap' },
      React.createElement('div', { className: 'card-top' },
        React.createElement('div', { className: `card-icon icon-${accent}` }, product.icon),
        React.createElement('div', { className: 'card-badges' },
          React.createElement(StatusBadge, { status: product.status }),
          React.createElement(PricingBadge, { pricing: product.pricing, price: product.price })
        )
      ),
      React.createElement('div', { className: 'card-name' }, product.name),
      React.createElement('div', { className: 'card-desc' }, product.desc),
      React.createElement('div', { className: 'card-meta' },
        ...product.tags.map(t => React.createElement(MetaTag, { key: t, label: t }))
      ),
      React.createElement('div', { className: 'card-footer' },
        React.createElement(BtnEl, {
          className: `card-btn ${isLive ? `btn-${accent}` : 'btn-disabled'}`,
          ...(isLive ? { href: product.url } : { disabled: true })
        },
          React.createElement('span', null, btnLabel),
          React.createElement('span', { className: 'btn-arrow' }, isLive ? '→' : '·')
        )
      )
    )
  );
}

// ── Section Header ────────────────────────────────────────────
function SectionHeader({ icon, tag, title, desc, count, accent }) {
  return React.createElement('div', { className: 'section-header' },
    React.createElement('div', { className: `section-eyebrow eyebrow-${accent}` },
      React.createElement('span', null, icon),
      React.createElement('span', null, tag)
    ),
    React.createElement('div', { className: 'section-header-row' },
      React.createElement('div', { className: 'section-header-text' },
        React.createElement('h2', { className: 'section-title' }, title),
        React.createElement('p',  { className: 'section-desc'  }, desc)
      ),
      React.createElement('div', { className: `section-count count-${accent}` },
        React.createElement('span', { className: 'count-num'   }, count),
        React.createElement('span', { className: 'count-label' }, count === 1 ? 'tool' : 'tools')
      )
    )
  );
}

// ── Navbar ────────────────────────────────────────────────────
function Navbar() {
  return React.createElement('nav', { className: 'navbar' },
    React.createElement('div', { className: 'navbar-inner' },
      React.createElement('div', { className: 'nav-brand' },
        React.createElement('div', { className: 'nav-logo' }, '🛰'),
        React.createElement('div', { className: 'nav-name' },
          'IMD', React.createElement('span', null, 'Tools')
        )
      ),
      React.createElement('div', { className: 'nav-links' },
        React.createElement('a', { className: 'nav-link', href: '#converters'  }, 'Converters'),
        React.createElement('a', { className: 'nav-link', href: '#calculators' }, 'Calculators'),
        React.createElement('a', { className: 'nav-link', href: '#geoportal'   }, 'Geoportal'),
        React.createElement('a', { className: 'nav-link', href: '#about'       }, 'About'),
        React.createElement('a', { className: 'nav-cta',  href: '/rainfall'    }, 'Try Free →')
      )
    )
  );
}

// ── Hero ──────────────────────────────────────────────────────
function Hero() {
  return React.createElement('section', { className: 'hero' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'hero-eyebrow' },
        React.createElement('div', { className: 'hero-dot' }),
        'IMD Gridded Climate Data Suite'
      ),
      React.createElement('h1', null,
        'Process IMD Data.',
        React.createElement('span', { className: 'hero-line2' }, 'Without the Pain.')
      ),
      React.createElement('p', { className: 'hero-desc' },
        'Free converters and paid research calculators for IMD binary gridded datasets — ' +
        'built by researchers, for researchers.'
      ),
      React.createElement('div', { className: 'hero-tags' },
        ['🌧 Rainfall', '🌡 Temperature', '💧 Drought Indices',
         '📈 Trend Analysis', '🗺 Geoportal'].map(t =>
          React.createElement('span', { key: t, className: 'hero-tag' }, t)
        )
      ),
      React.createElement('div', { className: 'hero-stats' },
        [
          ['10',    'Tools Planned'],
          ['3',     'Free Forever'],
          ['25+',   'Years of Data'],
          ['0.25°', 'Max Resolution'],
        ].map(([val, label], i, arr) =>
          React.createElement(React.Fragment, { key: label },
            React.createElement('div', { className: 'hero-stat' },
              React.createElement('div', { className: 'hero-stat-val' }, val),
              React.createElement('div', { className: 'hero-stat-label' }, label)
            ),
            i < arr.length - 1 &&
              React.createElement('div', { key: `d${i}`, className: 'hero-divider' })
          )
        )
      )
    )
  );
}

// ── Tech Strip ────────────────────────────────────────────────
function TechStrip() {
  return React.createElement('div', { className: 'tech-strip' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'tech-inner' },
        React.createElement('span', { className: 'tech-label' }, 'Built with'),
        React.createElement('div',  { className: 'tech-divider' }),
        React.createElement('div',  { className: 'tech-items' },
          ...TECH_ITEMS.map(item =>
            React.createElement('div', { className: 'tech-item', key: item.label },
              React.createElement('span', null, item.icon),
              React.createElement('span', null, item.label)
            )
          )
        )
      )
    )
  );
}

// ── Converters Section ────────────────────────────────────────
function ConvertersSection() {
  return React.createElement('section', {
    className: 'section section-blue', id: 'converters'
  },
    React.createElement('div', { className: 'container' },
      React.createElement(SectionHeader, {
        icon: '📦', tag: 'IMD Converters',
        title: 'Convert IMD Binary Files',
        desc:  'Parse raw IMD .grd and .nc binary files into usable formats. ' +
               'Export to CSV, GeoTIFF, and more. Converter tools are always free.',
        count: CONVERTERS.length,
        accent: 'blue'
      }),
      React.createElement('div', { className: 'products-grid' },
        ...CONVERTERS.map(p =>
          React.createElement(ProductCard, { key: p.id, product: p, accent: 'blue' })
        )
      )
    )
  );
}

// ── Calculators Section ───────────────────────────────────────
function CalculatorsSection() {
  return React.createElement('section', {
    className: 'section section-green', id: 'calculators'
  },
    React.createElement('div', { className: 'container' },
      React.createElement(SectionHeader, {
        icon: '📊', tag: 'Climate Calculators',
        title: 'Research-Grade Analysis Tools',
        desc:  'Advanced climate indices and statistical analysis built for PhD research, ' +
               'hydrology studies, and climate change assessment. Paid access.',
        count: CALCULATORS.length,
        accent: 'green'
      }),
      React.createElement('div', { className: 'products-grid' },
        ...CALCULATORS.map(p =>
          React.createElement(ProductCard, { key: p.id, product: p, accent: 'green' })
        )
      )
    )
  );
}

// ── Geoportal Banner ──────────────────────────────────────────
function GeoportalSection() {
  return React.createElement('section', {
    className: 'section section-purple', id: 'geoportal'
  },
    React.createElement('div', { className: 'container' },
      React.createElement(SectionHeader, {
        icon: '🗺', tag: 'Geoportal',
        title: 'Narmada Basin Research Platform',
        desc:  'A dedicated spatial platform for Narmada River Basin climate and drought analysis.',
        count: 1,
        accent: 'purple'
      }),
      React.createElement('div', { className: 'geoportal-banner' },
        React.createElement('div', { className: 'geoportal-left' },
          React.createElement('div', { className: 'geoportal-map-icon' }, '🗺'),
          React.createElement('div', { className: 'geoportal-content' },
            React.createElement('h3', { className: 'geoportal-title' },
              'Narmada Basin Geoportal'
            ),
            React.createElement('p', { className: 'geoportal-desc' },
              'An interactive research platform dedicated to the Narmada River Basin. ' +
              'Visualize rainfall patterns, compare multi-year data, generate GIF animations, ' +
              'and analyse drought conditions — all in one place.'
            ),
            React.createElement('div', { className: 'geoportal-features' },
              ['🗺 Interactive Basin Map', '📅 Multi-year Comparison',
               '🎞 GIF Animation', '📊 Spatial Statistics',
               '🖼 Image Export', '💧 Drought Zones'].map(f =>
                React.createElement('span', { key: f, className: 'geo-feature-tag' }, f)
              )
            )
          )
        ),
        React.createElement('div', { className: 'geoportal-right' },
          React.createElement('div', { className: 'geo-status-badge' }, '🚧 In Development'),
          React.createElement('div', { className: 'geo-pricing-badge' }, '💰 Paid Access'),
          React.createElement('button', {
            className: 'card-btn btn-disabled geo-cta', disabled: true
          },
            React.createElement('span', null, 'Coming Soon'),
            React.createElement('span', { className: 'btn-arrow' }, '·')
          )
        )
      )
    )
  );
}

// ── About ─────────────────────────────────────────────────────
function AboutStrip() {
  return React.createElement('div', { className: 'about-wrap', id: 'about' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'about-strip' },
        React.createElement('div', { className: 'about-icon' }, '🎓'),
        React.createElement('div', null,
          React.createElement('div', { className: 'about-title' }, 'Built for Climate Research'),
          React.createElement('p',   { className: 'about-text' },
            'Developed as part of PhD research on "Climate Change Impact on Aquatic ' +
            'Groundwater Dependent Ecosystems in Narmada River Basin" at IIT Indore. ' +
            'These tools solve real data processing challenges faced daily by researchers ' +
            'working with IMD gridded datasets.'
          ),
          React.createElement('div', { className: 'about-badges' },
            ['IIT Indore', 'Narmada Basin', 'Remote Sensing',
             'Climate Change', 'GIS', 'Groundwater'].map((b, i) =>
              React.createElement('span', {
                key: b,
                className: `about-badge ${i < 2 ? 'ab-blue' : 'ab-muted'}`
              }, b)
            )
          )
        )
      )
    )
  );
}

// ── Footer ────────────────────────────────────────────────────
function Footer() {
  return React.createElement('footer', { className: 'footer' },
    React.createElement('div', { className: 'container' },
      React.createElement('div', { className: 'footer-inner' },
        React.createElement('div', { className: 'footer-brand' },
          'IMD', React.createElement('span', null, 'Tools'), ' — Climate Data Suite'
        ),
        React.createElement('div', { className: 'footer-links' },
          ['Converters', 'Calculators', 'Geoportal', 'About'].map(label =>
            React.createElement('a', {
              key: label,
              className: 'footer-link',
              href: `#${label.toLowerCase()}`
            }, label)
          )
        ),
        React.createElement('div', { className: 'footer-copy' }, '© 2025 IMDTools · IIT Indore')
      )
    )
  );
}

// ── App Root ──────────────────────────────────────────────────
function App() {
  return React.createElement(React.Fragment, null,
    React.createElement('div', { className: 'bg-wrap' },
      React.createElement('div', { className: 'bg-dots' }),
      React.createElement('div', { className: 'bg-orb-1' }),
      React.createElement('div', { className: 'bg-orb-2' })
    ),
    React.createElement(Navbar),
    React.createElement(Hero),
    React.createElement(TechStrip),
    React.createElement(ConvertersSection),
    React.createElement(CalculatorsSection),
    React.createElement(GeoportalSection),
    React.createElement(AboutStrip),
    React.createElement(Footer)
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(App));