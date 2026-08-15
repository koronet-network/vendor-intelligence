#!/usr/bin/env python3
"""
Vendor Intelligence Dashboard — Builder
========================================
Reads data JSONs → generates HTML dashboard.

Usage:
  python3 build.py                    # builds to output/
  python3 build.py --open             # builds and opens in browser

Data sources (in data/):
  variety_master.json          — 1,171 varieties with demand, supply, balance, grades, vendor detail
  vendor_internal_profiles.json — 10 vendor profiles with quality scores
  canonical_category_map.json  — category normalization

Output:
  output/vendor_intelligence.html

Maintenance:
  - To refresh data: re-run Snowflake queries, save new JSONs, run build.py
  - To add features: modify the generate_* functions below
  - To publish: copy output/ to Labs or TX Dashboard repo
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from collections import defaultdict
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "vendor_intelligence.html"

# Source data files
VARIETY_MASTER = DATA_DIR / "variety_master.json"
VENDOR_PROFILES = DATA_DIR / "vendor_internal_profiles.json"
CATEGORY_MAP = DATA_DIR / "canonical_category_map.json"
VENDOR_VARIETY_DETAIL = DATA_DIR / "vendor_variety_detail.json"

# Display config
MAX_VENDORS_PER_VARIETY = 15
CATEGORIES_OPEN_BY_DEFAULT = ["Rose"]  # highest demand categories open
BUILD_DATE = datetime.now().strftime("%Y-%m-%d %H:%M")

# ============================================================
# DATA LOADING
# ============================================================

def load_data():
    """Load all data sources, return as dict."""
    data = {}

    with open(VARIETY_MASTER) as f:
        data['varieties'] = json.load(f)

    with open(VENDOR_PROFILES) as f:
        data['vendors'] = json.load(f)

    with open(CATEGORY_MAP) as f:
        data['categories'] = json.load(f)

    vendor_complete_path = DATA_DIR / "vendor_complete.json"
    if vendor_complete_path.exists():
        with open(vendor_complete_path) as f:
            data['vendor_complete'] = json.load(f)
    else:
        data['vendor_complete'] = {'vendors': {}}

    # Seasonality
    seasonality_path = DATA_DIR / "seasonality.json"
    if seasonality_path.exists():
        with open(seasonality_path) as f:
            data['seasonality'] = json.load(f)
    else:
        data['seasonality'] = {}

    # Accounts
    accounts_path = DATA_DIR / "accounts_priority.json"
    if accounts_path.exists():
        with open(accounts_path) as f:
            data['accounts'] = json.load(f)
    else:
        data['accounts'] = {}

    # Compute stats
    all_vars = [v for cat in data['varieties']['categories'].values() for v in cat]
    data['stats'] = {
        'total_varieties': len(all_vars),
        'with_demand': sum(1 for v in all_vars if v.get('demand_total', 0) > 0),
        'with_vendor_detail': sum(1 for v in all_vars if 'vendor_detail' in v),
        'with_grades': sum(1 for v in all_vars if 'grades' in v),
        'hot': sum(1 for v in all_vars if v.get('priority') == 'HOT'),
        'relevant': sum(1 for v in all_vars if v.get('priority') == 'RELEVANT'),
        'categories': len(data['varieties']['categories']),
    }

    # Build vendor quality lookup for inline display
    vendor_quality = {}
    for v in data['vendors'].get('vendors', []):
        name_lower = v['name'].lower()
        r = min(25, max(0, int(25 - v.get('cancel_pct',0)*10 - v.get('credit_pct',0)*5)))
        l = min(25, int(v.get('repeat_buyer_pct', 0) * 0.25))
        b = min(25, int(v.get('varieties', 0) / 30))
        s = min(25, int(v.get('buyers', 0) / 4))
        vendor_quality[name_lower] = {
            'score': r + l + b + s,
            'cancel_pct': v.get('cancel_pct', 0),
            'repeat_pct': v.get('repeat_buyer_pct', 0),
            'price_tier': 'PREMIUM' if v.get('avg_price_stem', 0) > 0.60 else 'MID' if v.get('avg_price_stem', 0) > 0.30 else 'VALUE'
        }
    data['vendor_quality'] = vendor_quality

    print(f"Loaded: {data['stats']['total_varieties']} varieties, "
          f"{data['stats']['with_demand']} with demand, "
          f"{data['stats']['with_vendor_detail']} with vendor detail, "
          f"{data['stats']['categories']} categories")

    return data

# ============================================================
# FORMATTERS
# ============================================================

def fmt_money(val):
    """Format dollar amount: $10.7M / $914K / $0"""
    if not val or val == 0:
        return "$0"
    if val >= 1_000_000:
        return f"${val/1_000_000:.1f}M"
    if val >= 1_000:
        return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"

def fmt_stems(val):
    """Format stem count: 5.18M / 287K / 0"""
    if not val or val == 0:
        return "&mdash;"
    if val >= 1_000_000:
        return f"{val/1_000_000:.2f}M"
    if val >= 1_000:
        return f"{val/1_000:.0f}K"
    return f"{val:,}"

def fmt_pct(val):
    """Format percentage"""
    if val is None:
        return "&mdash;"
    return f"{val:.1f}%"

# ============================================================
# CSS
# ============================================================

def generate_css():
    return """
:root{
  --ground:#FFFFFF;--surface:#F7FAF9;--surface-2:#EEF4F3;--line:#DDE7E5;--line-strong:#C3D3D0;
  --ink:#141918;--ink-2:#3F4B49;--ink-3:#6B7A78;
  --accent:#14B8A6;--accent-text:#0F766E;--tint:#CCFBF1;--tint-ink:#0B5F58;
  --warn:#B45309;--warn-tint:#FEF3C7;--warn-line:#F59E0B;
  --pass:#059669;--pass-tint:#D1FAE5;--pass-ink:#065F46;
  --new:#6366F1;--new-tint:#E0E7FF;--new-ink:#3730A3;
  --correct:#E11D48;--correct-tint:#FFE4E6;--correct-ink:#9F1239;
  --shadow:0 1px 2px rgba(20,25,24,.05),0 8px 24px -16px rgba(20,25,24,.25);
  --display:'Sora','Inter',-apple-system,sans-serif;
  --body:'Inter',-apple-system,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,monospace;
}
@media(prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#111;--surface:#181C1B;--surface-2:#1F2523;--line:#2C3533;--line-strong:#3E4947;
    --ink:#EDF2F1;--ink-2:#B4C1BF;--ink-3:#849492;
    --accent:#14B8A6;--accent-text:#2DD4BF;--tint:#0F2E2A;--tint-ink:#7FE9DC;
    --warn:#FBBF24;--warn-tint:#2E2308;--warn-line:#B45309;
    --pass:#34D399;--pass-tint:#0D3326;--pass-ink:#6EE7B7;
    --new:#818CF8;--new-tint:#1E1B4B;--new-ink:#A5B4FC;
    --correct:#FB7185;--correct-tint:#4C0519;--correct-ink:#FDA4AF;
    --shadow:none;
  }
}
*{box-sizing:border-box;}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.5;-webkit-font-smoothing:antialiased;}
.wrap{max-width:80rem;margin:0 auto;padding:2.5rem 1.5rem 4rem;}
h1,h2,h3{font-family:var(--display);margin:0;}
h1{font-size:clamp(1.6rem,3vw,2.2rem);font-weight:700;letter-spacing:-.02em;line-height:1.15;}
h2{font-size:1.25rem;font-weight:700;letter-spacing:-.01em;}
h3{font-size:1rem;font-weight:600;}
p{margin:0;}
a{color:var(--accent-text);text-decoration:none;}

/* Header */
.eyebrow{font-size:.6875rem;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--accent-text);}
.lede{font-size:1rem;color:var(--ink-2);max-width:44rem;margin-top:.5rem;}
.metaline{display:flex;flex-wrap:wrap;gap:.4rem 1.25rem;font-size:.8rem;color:var(--ink-3);border-top:1px solid var(--line);padding-top:.75rem;margin-top:.75rem;}
.metaline b{color:var(--ink-2);font-weight:600;}
header{border-top:3px solid var(--accent);padding-top:1.5rem;}

/* Stat strip */
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-top:1.5rem;}
.stat{background:var(--surface);padding:.85rem 1rem;display:flex;flex-direction:column;gap:.1rem;}
.stat .n{font-family:var(--display);font-size:1.5rem;font-weight:700;line-height:1;letter-spacing:-.03em;font-variant-numeric:tabular-nums;}
.stat .n.on{color:var(--accent-text);}
.stat .l{font-size:.7rem;letter-spacing:.05em;text-transform:uppercase;color:var(--ink-3);font-weight:600;}

/* Tabs */
.tabs{margin-top:2rem;}
.tabs input[type="radio"]{display:none;}
.tab-labels{display:flex;gap:0;border-bottom:2px solid var(--line);overflow-x:auto;}
.tab-labels label{padding:.65rem 1.1rem;font-size:.85rem;font-weight:600;color:var(--ink-3);cursor:pointer;white-space:nowrap;border-bottom:2px solid transparent;margin-bottom:-2px;transition:color .15s;}
.tab-labels label:hover{color:var(--ink);}
.tab-panels{margin-top:1.5rem;}
.tab-panel{display:none;}
#tab1:checked ~ .tab-panels .panel-1,
#tab2:checked ~ .tab-panels .panel-2,
#tab3:checked ~ .tab-panels .panel-3,
#tab4:checked ~ .tab-panels .panel-4,
#tab5:checked ~ .tab-panels .panel-5 {display:block;}
#tab1:checked ~ .tab-labels label[for="tab1"],
#tab2:checked ~ .tab-labels label[for="tab2"],
#tab3:checked ~ .tab-labels label[for="tab3"],
#tab4:checked ~ .tab-labels label[for="tab4"],
#tab5:checked ~ .tab-labels label[for="tab5"] {color:var(--accent-text);border-bottom-color:var(--accent);}

/* Search */
.search-box{width:100%;padding:.6rem .9rem;font-size:.9rem;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink);font-family:var(--body);margin-bottom:1rem;}
.search-box:focus{outline:2px solid var(--accent);border-color:var(--accent);}

/* Filter pills */
.filters{display:flex;gap:.4rem;margin-bottom:1rem;flex-wrap:wrap;}
.pill{padding:.3rem .7rem;border:1px solid var(--line);border-radius:999px;font-size:.75rem;font-weight:600;cursor:pointer;background:var(--surface);color:var(--ink-2);transition:all .15s;}
.pill:hover{border-color:var(--ink-3);}
.pill.active{background:var(--accent);color:white;border-color:var(--accent);}

/* Tables */
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--surface);}
table{border-collapse:collapse;width:100%;font-size:.8rem;}
th,td{text-align:left;padding:.5rem .7rem;border-bottom:1px solid var(--line);vertical-align:top;}
th{font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-3);font-weight:600;background:var(--surface-2);position:sticky;top:0;z-index:1;}
tbody tr:last-child td{border-bottom:none;}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:500;}
tr.has-detail{cursor:pointer;}
tr.has-detail:hover{background:var(--surface-2);}
tr.vendor-expand{display:none;}
tr.vendor-expand td{padding:.5rem .7rem;background:var(--surface-2);}
.sub-table{width:100%;font-size:.75rem;margin:.25rem 0;}
.sub-table th{font-size:.6rem;background:var(--surface);position:static;}
.sub-table td{padding:.35rem .6rem;}

/* Badges */
.badge{font-size:.6rem;font-weight:700;padding:.12rem .35rem;border-radius:3px;display:inline-block;text-transform:uppercase;letter-spacing:.03em;}
.badge.hot{background:var(--correct-tint);color:var(--correct-ink);}
.badge.relevant{background:var(--warn-tint);color:var(--warn);}
.badge.niche{background:var(--surface-2);color:var(--ink-3);}
.badge.desert{background:var(--correct-tint);color:var(--correct-ink);}
.badge.undersupplied{background:#FFEDD5;color:#9A3412;}
.badge.tight{background:var(--warn-tint);color:var(--warn);}
.badge.balanced{background:var(--pass-tint);color:var(--pass-ink);}
.badge.oversupplied{background:var(--new-tint);color:var(--new-ink);}
.badge.nodata{background:var(--surface-2);color:var(--ink-3);}
.badge.value{background:#DBEAFE;color:#1E40AF;}
.badge.mid{background:var(--warn-tint);color:#92400E;}
.badge.premium{background:#F3E8FF;color:#7C3AED;}

/* Forward bar */
.fwd-bar{display:inline-block;height:6px;background:var(--accent);border-radius:3px;min-width:2px;vertical-align:middle;margin-left:.3rem;}

/* Details / collapsible */
details{border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:.75rem;}
details summary{cursor:pointer;padding:.7rem 1rem;background:var(--surface-2);font-size:.85rem;font-weight:600;color:var(--ink-2);list-style:none;display:flex;align-items:center;gap:.5rem;}
details summary::before{content:'▸';display:inline-block;transition:transform .15s;font-size:.7rem;color:var(--ink-3);}
details[open] summary::before{transform:rotate(90deg);}
details summary::-webkit-details-marker{display:none;}
details .detail-body{padding:0;}
details .detail-body table{border:none;border-radius:0;}

/* Inline detail expand — pops out as overlay panel */
td.has-expand{position:relative;}
.inline-detail{border:none !important;margin:0 !important;}
.inline-detail summary{padding:0 !important;background:none !important;font-weight:700;color:var(--ink) !important;font-size:inherit !important;}
.inline-detail summary::before{content:'▸ ' !important;color:var(--accent-text);}
.inline-detail[open] summary::before{content:'▾ ' !important;}
.inline-detail[open] > .expand-panel{
  position:absolute;left:-1rem;top:100%;z-index:20;
  width:calc(100vw - 6rem);max-width:72rem;
  background:var(--ground);border:1px solid var(--line);border-radius:8px;
  box-shadow:0 4px 24px rgba(0,0,0,.12);padding:1rem;
}

/* Vendor cards */
.vendor-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(22rem,1fr));gap:1rem;}
.vendor-card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:1.1rem 1.25rem;display:flex;flex-direction:column;gap:.6rem;box-shadow:var(--shadow);}
.vendor-card h3{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;}
.qs-bar{height:8px;background:var(--surface-2);border-radius:4px;overflow:hidden;margin:.3rem 0;}
.qs-fill{height:100%;background:var(--accent);border-radius:4px;transition:width .3s;}
.qs-breakdown{font-size:.7rem;color:var(--ink-3);display:flex;gap:.75rem;}
.time-bar{display:flex;height:8px;border-radius:4px;overflow:hidden;margin:.3rem 0;}
.time-bar div{min-width:2px;}
.vendor-meta{font-size:.8rem;color:var(--ink-2);display:flex;flex-wrap:wrap;gap:.5rem 1rem;}
.vendor-meta b{color:var(--ink);}
.best-for{font-size:.8rem;color:var(--ink-2);font-style:italic;border-top:1px solid var(--line);padding-top:.5rem;margin-top:auto;}

/* Info box */
.info-box{background:var(--tint);border-radius:8px;padding:1rem 1.25rem;font-size:.85rem;color:var(--ink-2);margin-bottom:1rem;}
.info-box b{color:var(--tint-ink);}

/* Panels */
.panel{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:1rem 1.15rem;}

/* Footer */
footer{margin-top:3rem;border-top:1px solid var(--line);padding-top:1rem;display:grid;grid-template-columns:repeat(auto-fit,minmax(16rem,1fr));gap:1rem;font-size:.75rem;color:var(--ink-3);}
footer b{color:var(--ink-2);font-weight:600;display:block;margin-bottom:.2rem;}

/* Responsive */
@media(max-width:48rem){table{font-size:.75rem;}th,td{padding:.4rem .5rem;}.vendor-grid{grid-template-columns:1fr;}}
@media(max-width:36rem){.wrap{padding:1.5rem .75rem 3rem;}.stats{grid-template-columns:repeat(2,1fr);}}
"""

# ============================================================
# JAVASCRIPT
# ============================================================

def generate_js():
    return """
// Search
document.getElementById('search').addEventListener('input', function(e) {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('.variety-row').forEach(row => {
    const match = row.dataset.variety.toLowerCase().includes(q) ||
                  (row.dataset.category && row.dataset.category.toLowerCase().includes(q));
    row.style.display = match || q === '' ? '' : 'none';
    // Hide expand row too
    const next = row.nextElementSibling;
    if (next && next.classList.contains('vendor-expand') && !match && q !== '') {
      next.style.display = 'none';
    }
  });
  // Open all categories when searching
  if (q.length > 0) {
    document.querySelectorAll('.panel-1 details').forEach(d => d.open = true);
  }
});

// Filter pills
document.querySelectorAll('.pill').forEach(pill => {
  pill.addEventListener('click', function() {
    const group = this.dataset.group;
    // Deactivate same group
    document.querySelectorAll(`.pill[data-group="${group}"]`).forEach(p => p.classList.remove('active'));
    this.classList.add('active');
    applyFilters();
  });
});

function applyFilters() {
  const priorityPill = document.querySelector('.pill[data-group="priority"].active');
  const forwardPill = document.querySelector('.pill[data-group="forward"].active');
  const pFilter = priorityPill ? priorityPill.dataset.filter : 'all';
  const fFilter = forwardPill ? forwardPill.dataset.filter : 'all';

  document.querySelectorAll('.variety-row').forEach(row => {
    const pMatch = pFilter === 'all' || row.dataset.priority === pFilter;
    const fMatch = fFilter === 'all' || row.dataset.forward === fFilter;
    row.style.display = pMatch && fMatch ? '' : 'none';
    const next = row.nextElementSibling;
    if (next && next.classList.contains('vendor-expand') && !(pMatch && fMatch)) {
      next.style.display = 'none';
    }
  });
  // Open all categories
  document.querySelectorAll('.panel-1 details').forEach(d => d.open = true);
}

// Expandable rows
document.querySelectorAll('.has-detail').forEach(row => {
  row.addEventListener('click', function() {
    const next = this.nextElementSibling;
    if (next && next.classList.contains('vendor-expand')) {
      next.style.display = next.style.display === 'none' ? '' : 'none';
    }
  });
});

// Sort by column
document.querySelectorAll('th[data-sort]').forEach(th => {
  th.style.cursor = 'pointer';
  th.addEventListener('click', function() {
    const table = this.closest('table');
    const tbody = table.querySelector('tbody');
    const col = this.dataset.sort;
    const rows = Array.from(tbody.querySelectorAll('tr.variety-row'));
    const asc = this.dataset.dir !== 'asc';
    this.dataset.dir = asc ? 'asc' : 'desc';

    rows.sort((a, b) => {
      let va = parseFloat(a.dataset[col]) || 0;
      let vb = parseFloat(b.dataset[col]) || 0;
      return asc ? va - vb : vb - va;
    });

    rows.forEach(row => {
      const expand = row.nextElementSibling;
      tbody.appendChild(row);
      if (expand && expand.classList.contains('vendor-expand')) {
        tbody.appendChild(expand);
      }
    });

    // Update sort indicators
    table.querySelectorAll('th[data-sort]').forEach(h => {
      h.textContent = h.textContent.replace(/ [▲▼]/, '');
    });
    this.textContent += asc ? ' ▲' : ' ▼';
  });
});
"""

# ============================================================
# TAB 1: SUPPLY INTELLIGENCE (demand-first)
# ============================================================

def generate_tab1(data):
    stats = data['stats']
    categories = data['varieties']['categories']
    vendor_quality = data.get('vendor_quality', {})

    html = []

    # Search
    html.append('<input type="text" id="search" class="search-box" placeholder="Search variety or category (e.g., Freedom, Ranunculus, Hydrangea...)">')

    # Filter pills
    html.append('<div class="filters">')
    html.append('<span style="font-size:.75rem;color:var(--ink-3);font-weight:600;margin-right:.25rem;">Priority:</span>')
    html.append('<span class="pill active" data-group="priority" data-filter="all">All</span>')
    html.append('<span class="pill" data-group="priority" data-filter="HOT">HOT</span>')
    html.append('<span class="pill" data-group="priority" data-filter="RELEVANT">Relevant</span>')
    html.append('<span style="font-size:.75rem;color:var(--ink-3);font-weight:600;margin-left:.75rem;margin-right:.25rem;">Forward:</span>')
    html.append('<span class="pill active" data-group="forward" data-filter="all">All</span>')
    html.append('<span class="pill" data-group="forward" data-filter="yes">Has forward</span>')
    html.append('<span class="pill" data-group="forward" data-filter="no">Spot only</span>')
    html.append('</div>')

    # Split: with demand vs without
    demand_cats = {}
    nodemand_cats = {}

    for cat_name, varieties in categories.items():
        with_d = [v for v in varieties if v.get('demand_total', 0) > 0]
        without_d = [v for v in varieties if v.get('demand_total', 0) == 0]
        if with_d:
            demand_cats[cat_name] = sorted(with_d, key=lambda v: -v['demand_total'])
        if without_d:
            nodemand_cats[cat_name] = sorted(without_d, key=lambda v: -v['total_stems'])

    # Sort categories by total demand
    sorted_demand_cats = sorted(demand_cats.items(), key=lambda x: -sum(v['demand_total'] for v in x[1]))
    sorted_nodemand_cats = sorted(nodemand_cats.items(), key=lambda x: -sum(v['total_stems'] for v in x[1]))

    # SECTION A: High demand varieties by category
    total_demand_vars = sum(len(vs) for vs in demand_cats.values())
    html.append(f'<h2 style="margin-bottom:.75rem;">High Demand Varieties <span style="font-size:.85rem;color:var(--ink-3);font-weight:400;">({total_demand_vars} varieties with demand data)</span></h2>')

    for cat_name, varieties in sorted_demand_cats:
        cat_demand = sum(v['demand_total'] for v in varieties)
        cat_strong = sum(1 for v in varieties if v.get('forward_score') == 'STRONG')
        cat_hot = sum(1 for v in varieties if v.get('priority') == 'HOT')
        is_open = cat_name in CATEGORIES_OPEN_BY_DEFAULT

        html.append(f'<details{"  open" if is_open else ""}>')
        summary_parts = [f'{cat_name} &mdash; {len(varieties)} varieties, {fmt_money(cat_demand)} demand']
        if cat_hot:
            summary_parts.append(f'{cat_hot} HOT')
        if cat_strong:
            summary_parts.append(f'{cat_strong} STRONG forward')
        html.append(f'<summary>{", ".join(summary_parts)}</summary>')
        html.append('<div class="detail-body"><div class="tablewrap">')
        html.append('<table>')
        html.append('<thead><tr>')
        html.append('<th>Priority</th>')
        html.append('<th>Variety</th>')
        html.append('<th data-sort="demand">Demand (12mo)</th>')
        html.append('<th data-sort="buyers">Buyers</th>')
        html.append('<th data-sort="arrived">In Stock</th>')
        html.append('<th>7d</th>')
        html.append('<th>14d</th>')
        html.append('<th data-sort="fwd15">15-30d</th>')
        html.append('<th data-sort="fwd30">30+d</th>')
        html.append('<th></th>')
        html.append('</tr></thead><tbody>')

        for v in varieties:
            has_detail = 'vendor_detail' in v or 'grades' in v
            arrived = v.get('in_stock', 0)
            d7 = v.get('arriving_7d', 0)
            d14 = v.get('arriving_14d', 0)
            d30 = v.get('arriving_30d', 0)
            d30p = v.get('arriving_30plus', 0)
            has_forward = 'yes' if (d30 + d30p) > 0 else 'no'

            pri = v.get('priority', 'NICHE')
            pri_class = pri.lower()
            demand_style = 'font-weight:700;' if pri == 'HOT' else ''

            row_class = 'variety-row'

            html.append(f'<tr class="{row_class}" '
                       f'data-variety="{v["name"]}" data-category="{cat_name}" '
                       f'data-priority="{pri}" data-forward="{has_forward}" '
                       f'data-demand="{v.get("demand_total", 0)}" data-buyers="{v.get("buyer_count", 0)}">')
            html.append(f'<td><span class="badge {pri_class}">{pri}</span></td>')

            if has_detail:
                demand_total = v.get('demand_total', 0)
                fwd_total = d30 + d30p
                html.append(f'<td class="has-expand"><details class="inline-detail">')
                html.append(f'<summary>{v["name"]}</summary>')
                html.append('<div class="expand-panel">')

                # Demand/Supply context bar
                if demand_total > 0:
                    weekly = demand_total / 52
                    html.append(f'<div style="display:flex;gap:1.25rem;flex-wrap:wrap;margin-bottom:.75rem;font-size:.8rem;color:var(--ink-2);padding:.5rem .75rem;background:var(--surface-2);border-radius:6px;">')
                    html.append(f'<span><b>Demand:</b> {fmt_money(demand_total)} / 12mo (~{fmt_money(weekly)}/wk, {v.get("buyer_count",0)} buyers)</span>')
                    html.append(f'<span><b>In stock:</b> {fmt_stems(arrived)} stems</span>')
                    if fwd_total > 0:
                        html.append(f'<span><b>Forward:</b> {fmt_stems(fwd_total)} stems arriving 15+d</span>')
                    html.append('</div>')

                if 'vendor_detail' in v:
                    # Dedup vendors
                    seen = set()
                    deduped = []
                    for vd in v['vendor_detail'][:MAX_VENDORS_PER_VARIETY]:
                        vn = vd['vendor'].strip().lower()
                        if vn not in seen:
                            seen.add(vn)
                            deduped.append(vd)
                    sorted_vendors = sorted(deduped,
                        key=lambda vd: -(vd.get('d30',0)+vd.get('d30p',0)))

                    html.append('<p style="font-size:.7rem;color:var(--ink-3);margin-bottom:.3rem;">Supply sources (farm-level)</p>')
                    html.append('<div class="tablewrap"><table class="sub-table"><thead><tr>')
                    html.append('<th>Source</th><th>$/stem</th><th>In Stock</th><th>7d</th><th>14d</th><th>15-30d</th><th>30+d</th><th>Total</th>')
                    html.append('</tr></thead><tbody>')
                    for vd in sorted_vendors:
                        total = vd.get('stems', vd.get('arrived',0)+vd.get('d7',0)+vd.get('d14',0)+vd.get('d30',0)+vd.get('d30p',0))

                        html.append(f'<tr>')
                        html.append(f'<td><b>{vd["vendor"]}</b></td>')
                        html.append(f'<td class="num">${vd.get("price", 0):.3f}</td>' if vd.get('price') else '<td class="num">&mdash;</td>')
                        html.append(f'<td class="num">{fmt_stems(vd.get("arrived", vd.get("in_stock", 0)))}</td>')
                        html.append(f'<td class="num">{fmt_stems(vd.get("d7", 0))}</td>')
                        html.append(f'<td class="num">{fmt_stems(vd.get("d14", 0))}</td>')
                        html.append(f'<td class="num">{fmt_stems(vd.get("d30", 0))}</td>')
                        html.append(f'<td class="num">{fmt_stems(vd.get("d30p", vd.get("d30plus", 0)))}</td>')
                        html.append(f'<td class="num">{fmt_stems(total)}</td>')
                        html.append('</tr>')
                    html.append('</tbody></table></div>')

                if 'grades' in v:
                    html.append('<div class="tablewrap" style="margin-top:.5rem;"><table class="sub-table"><thead><tr>')
                    html.append('<th>Grade</th><th>Stems</th><th>Vendors</th><th>Avg $/stem</th><th>Range</th>')
                    html.append('</tr></thead><tbody>')
                    for g in sorted(v['grades'].keys()):
                        gd = v['grades'][g]
                        html.append(f'<tr><td><b>{g}</b></td>')
                        html.append(f'<td class="num">{fmt_stems(gd["total_stems"])}</td>')
                        html.append(f'<td class="num">{gd["vendor_count"]}</td>')
                        html.append(f'<td class="num">${gd["avg_price"]:.3f}</td>')
                        html.append(f'<td class="num">${gd["min_price"]:.3f}&ndash;${gd["max_price"]:.3f}</td>')
                        html.append('</tr>')
                    html.append('</tbody></table></div>')

                html.append('</div></details></td>')
            else:
                html.append(f'<td>{v["name"]}</td>')

            # These columns are the same for both expandable and non-expandable
            html.append(f'<td class="num" style="{demand_style}">{fmt_money(v.get("demand_total", 0))}</td>')
            html.append(f'<td class="num">{v.get("buyer_count", 0)}</td>')
            html.append(f'<td class="num">{fmt_stems(arrived)}</td>')
            html.append(f'<td class="num">{fmt_stems(d7)}</td>')
            html.append(f'<td class="num">{fmt_stems(d14)}</td>')
            html.append(f'<td class="num">{fmt_stems(d30)}</td>')
            html.append(f'<td class="num">{fmt_stems(d30p)}</td>')

            html.append('</tr>')

        html.append('</tbody></table></div></div></details>')

    # SECTION B: No demand data
    total_nodemand = sum(len(vs) for vs in nodemand_cats.values())
    html.append(f'<details style="margin-top:2rem;">')
    html.append(f'<summary>More Supply &mdash; no demand data matched ({total_nodemand} varieties)</summary>')
    html.append('<div class="detail-body">')
    html.append('<div class="info-box"><b>Note:</b> These varieties are in importer inventory but demand data hasn\'t matched yet (naming differences between buyer and seller systems). Use search to find specific varieties.</div>')

    for cat_name, varieties in sorted_nodemand_cats:
        html.append(f'<details><summary>{cat_name} &mdash; {len(varieties)} varieties, {fmt_stems(sum(v["total_stems"] for v in varieties))} stems</summary>')
        html.append('<div class="detail-body"><div class="tablewrap"><table>')
        html.append('<thead><tr><th>Variety</th><th>Supply</th><th>Forward 15+d</th><th>FWD Score</th><th>Vendors</th></tr></thead><tbody>')
        for v in varieties[:50]:  # cap at 50 per category to keep size manageable
            fwd = v.get('arriving_30d', 0) + v.get('arriving_30plus', 0)
            has_fwd = 'yes' if fwd > 0 else 'no'
            html.append(f'<tr class="variety-row" data-variety="{v["name"]}" data-category="{cat_name}" data-priority="NICHE" data-forward="{has_fwd}" data-demand="0" data-buyers="0" data-stems="{v["total_stems"]}" data-fwdready="{v.get("forward_readiness",0)}" data-fwdstems="{fwd}">')
            html.append(f'<td>{v["name"]}</td>')
            html.append(f'<td class="num">{fmt_stems(v["total_stems"])}</td>')
            html.append(f'<td class="num">{fmt_stems(fwd)}</td>')
            html.append(f'<td class="num">{v.get("forward_readiness", 0)}</td>')
            html.append(f'<td class="num">{v.get("vendors", 0)}</td>')
            html.append('</tr>')
        if len(varieties) > 50:
            html.append(f'<tr><td colspan="5" style="color:var(--ink-3);font-style:italic;">+ {len(varieties)-50} more (use search)</td></tr>')
        html.append('</tbody></table></div></div></details>')

    html.append('</div></details>')

    return '\n'.join(html)

# ============================================================
# TAB 2: VENDOR PROFILES
# ============================================================

def generate_tab2(data):
    from tab2_clean import generate_tab2 as _clean_tab2
    vc = data.get('vendor_complete', {}).get('vendors', {})
    if not vc:
        return '<p>No vendor data loaded.</p>'
    return _clean_tab2(vc)

def _OLD_generate_tab2(data):
    """OLD — not called."""
    html = []
    html.append('UNUSED')

    # Filters
    html.append('<div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-bottom:1rem;align-items:center;">')
    html.append('<input type="text" id="vendor-search" class="search-box" style="width:auto;flex:1;min-width:200px;margin:0;" placeholder="Search vendor or variety...">')
    html.append('<div class="filters" style="margin:0;">')
    html.append('<span class="pill active" data-group="quality" data-filter="all">All quality</span>')
    html.append('<span class="pill" data-group="quality" data-filter="high">High (70+)</span>')
    html.append('<span class="pill" data-group="quality" data-filter="mid">Mid (40-70)</span>')
    html.append('<span class="pill" data-group="quality" data-filter="low">Low (&lt;40)</span>')
    html.append('</div>')
    html.append('<div class="filters" style="margin:0;">')
    html.append('<span class="pill active" data-group="vfwd" data-filter="all">All</span>')
    html.append('<span class="pill" data-group="vfwd" data-filter="forward">Has forward</span>')
    html.append('<span class="pill" data-group="vfwd" data-filter="spot">Spot only</span>')
    html.append('</div>')
    html.append('</div>')

    html.append(f'<p style="font-size:.85rem;color:var(--ink-3);margin-bottom:.75rem;">{len(vendors_list)} vendors. Click to expand. 32 with category breakdown, 80 with quality profile.</p>')

    for v in vendors_list:
        qs = v.get('quality_score', 0)
        cancel = v.get('cancel_pct', 0)
        cancel_style = 'color:var(--correct);' if cancel > 1 else ''
        tier = v.get('price_tier', 'VALUE')
        fwd = v.get('forward_pct', 0)
        has_forward = 'forward' if fwd > 0 else 'spot'
        quality_tier = 'high' if qs >= 70 else 'mid' if qs >= 40 else 'low'
        cats = v.get('top_category_names', [])
        cat_chips = ''.join(f'<span style="font-size:.6rem;background:var(--tint);color:var(--tint-ink);padding:.1rem .3rem;border-radius:3px;margin-right:.2rem;">{c}</span>' for c in cats[:4])
        search_text = f"{v['name']} {' '.join(cats)}".lower()

        # Timeframe bar
        tf = v.get('timeframe_total', {})
        tf_total = sum(tf.values()) or 1
        bar_html = '<div class="time-bar">'
        for key, color in [('spot','#ef4444'),('short','#f97316'),('med','#eab308'),('fwd','#22c55e'),('deep','#14b8a6')]:
            pct = tf.get(key, 0) / tf_total * 100
            if pct > 0:
                bar_html += f'<div style="width:{pct}%;background:{color};" title="{key} {pct:.0f}%"></div>'
        bar_html += '</div>'

        html.append(f'<details class="vendor-row" data-vendor="{v["name"].lower()}" '
                    f'data-quality="{quality_tier}" data-vfwd="{has_forward}" '
                    f'data-search="{search_text}" style="margin-bottom:.3rem;">')

        html.append(f'<summary style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;padding:.5rem .75rem;">')
        html.append(f'<b style="font-size:.95rem;min-width:2.2rem;">{qs}</b>')
        html.append(f'<span style="flex:1;min-width:180px;"><b>{v["name"]}</b> {cat_chips}</span>')
        html.append(f'<span class="badge {tier.lower()}" style="font-size:.55rem;">{tier}</span>')
        html.append(f'<span style="font-size:.75rem;color:var(--ink-3);min-width:3.5rem;">{fwd:.0f}% fwd</span>')
        html.append(f'<span style="font-size:.75rem;{cancel_style}min-width:3.5rem;">{cancel:.1f}% canc</span>')
        html.append(f'<span style="font-size:.75rem;color:var(--ink-3);min-width:3.5rem;">{v.get("repeat_pct",0):.0f}% rpt</span>')
        html.append(f'<span style="font-size:.75rem;color:var(--ink-3);min-width:3rem;">{v.get("buyers",0)} buy</span>')
        html.append('</summary>')

        html.append('<div style="padding:.75rem 1rem;border-top:1px solid var(--line);">')

        # Quality + GMV + timeframe bar
        html.append('<div style="display:flex;gap:1.25rem;flex-wrap:wrap;margin-bottom:.5rem;font-size:.78rem;color:var(--ink-2);">')
        html.append(f'<span><b>Reliability:</b> {v["qs_r"]}/25</span>')
        html.append(f'<span><b>Loyalty:</b> {v["qs_l"]}/25</span>')
        html.append(f'<span><b>Breadth:</b> {v["qs_b"]}/25 ({v.get("total_varieties",0):,} var)</span>')
        html.append(f'<span><b>Scale:</b> {v["qs_s"]}/25 ({v.get("buyers",0)} buyers)</span>')
        html.append(f'<span><b>Price:</b> ${v.get("avg_price",0):.2f}/stem</span>')
        html.append(f'<span><b>GMV:</b> {fmt_money(v.get("gmv_total",0))}</span>')
        html.append('</div>')
        html.append(f'<div style="font-size:.7rem;color:var(--ink-3);margin-bottom:.75rem;">Timeframe mix: {bar_html}</div>')

        # Categories with timeframe breakdown
        categories = v.get('categories', [])
        if categories:
            html.append('<div class="tablewrap"><table class="sub-table"><thead><tr>')
            html.append('<th>Category</th><th>Sold ($)</th><th>Buyers</th><th>Spot</th><th>3-7d</th><th>8-14d</th><th>15-30d</th><th>30+d</th>')
            html.append('</tr></thead><tbody>')
            for c in categories[:10]:
                fwd_style = 'font-weight:600;color:var(--accent-text);' if (c.get('s_fwd',0)+c.get('s_deep',0)) > 0 else ''
                html.append(f'<tr>')
                html.append(f'<td><b>{c["category"]}</b></td>')
                html.append(f'<td class="num">{fmt_money(c["sold"])}</td>')
                html.append(f'<td class="num">{c["buyers"]}</td>')
                html.append(f'<td class="num">{fmt_stems(c.get("s_spot",0))}</td>')
                html.append(f'<td class="num">{fmt_stems(c.get("s_short",0))}</td>')
                html.append(f'<td class="num">{fmt_stems(c.get("s_med",0))}</td>')
                html.append(f'<td class="num" style="{fwd_style}">{fmt_stems(c.get("s_fwd",0))}</td>')
                html.append(f'<td class="num" style="{fwd_style}">{fmt_stems(c.get("s_deep",0))}</td>')
                html.append('</tr>')
            html.append('</tbody></table></div>')
        else:
            html.append(f'<p style="font-size:.8rem;color:var(--ink-3);">Category breakdown not available yet. Quality profile based on {v.get("total_varieties",0):,} varieties across {v.get("buyers",0)} buyers.</p>')

        html.append('</div></details>')

    # JS
    html.append("""<script>
document.getElementById('vendor-search').addEventListener('input', function(e) {
  const q = e.target.value.toLowerCase();
  document.querySelectorAll('.vendor-row').forEach(row => {
    row.style.display = (q === '' || row.dataset.search.includes(q)) ? '' : 'none';
  });
});
document.querySelectorAll('.panel-2 .pill').forEach(pill => {
  pill.addEventListener('click', function() {
    const group = this.dataset.group;
    document.querySelectorAll(`.panel-2 .pill[data-group="${group}"]`).forEach(p => p.classList.remove('active'));
    this.classList.add('active');
    const qf = document.querySelector('.panel-2 .pill[data-group="quality"].active').dataset.filter;
    const ff = document.querySelector('.panel-2 .pill[data-group="vfwd"].active').dataset.filter;
    document.querySelectorAll('.vendor-row').forEach(row => {
      const qMatch = qf === 'all' || row.dataset.quality === qf;
      const fMatch = ff === 'all' || row.dataset.vfwd === ff;
      row.style.display = qMatch && fMatch ? '' : 'none';
    });
  });
});
</script>""")

    return '\n'.join(html)

# ============================================================
# TAB 3: DEFINITIONS
# ============================================================

def generate_tab3(data):
    html = []

    html.append('<h2>How to use this tool</h2>')
    html.append('<div class="info-box">')
    html.append('<ol style="margin:0;padding-left:1.2rem;display:flex;flex-direction:column;gap:.3rem;">')
    html.append('<li><b>Search</b> for what your wholesaler buys (variety or category name)</li>')
    html.append('<li><b>Check demand</b> — HOT = high demand, many buyers buy this</li>')
    html.append('<li><b>Check balance</b> — is there enough supply? UNDERSUPPLIED = limited options</li>')
    html.append('<li><b>Click to expand</b> — see which vendors have it, at what price, at what timeframe</li>')
    html.append('<li><b>Use filters</b> — show only HOT varieties, or only those with forward supply</li>')
    html.append('<li><b>Check vendor profile</b> (Tab 2) — quality score, cancel rate, specialty</li>')
    html.append('</ol></div>')

    html.append('<h2 style="margin-top:1.5rem;">Definitions</h2>')
    html.append('<div class="tablewrap"><table style="min-width:20rem;">')
    html.append('<thead><tr><th>Term</th><th>Definition</th></tr></thead><tbody>')

    defs = [
        ('Demand (12mo)', 'Total wholesaler procurement in this variety over 12 months, ALL channels (online + offline). Source: PROCUREMENT_DETAILS. Note: demand and supply are different timeframes — demand is annual, supply is a daily snapshot. They are context for each other, not directly comparable.'),
        ('Buyers', 'Number of distinct wholesaler companies that purchased this variety in the last 12 months.'),
        ('Arrived', 'Stems already at the importer location. Available for purchase now. Source: INVENTORY_DETAILS snapshot.'),
        ('7d / 14d', 'Stems arriving at the importer within 7 or 8-14 days, based on AWB (airway bill) arrival dates.'),
        ('15-30d / 30+d', 'Forward supply — stems arriving in 15-30 or 30+ days. This is what enables planned buying ahead instead of spot.'),
        ('Priority', 'HOT = &gt;$1M demand + 50+ buyers. RELEVANT = &gt;$200K + 20+ buyers. NICHE = everything else.'),
        ('Grade', 'Stem length in cm (for roses). 40cm = short, 50-60cm = standard, 70cm+ = premium. Longer &ne; better — different product for different use cases.'),
        ('$/stem', 'Median price per stem from procurement transactions. Filtered to remove outliers (&lt;$0.05 or &gt;$5.00). Shown in the vendor drill-down when you expand a variety.'),
        ('Quality Score v1', 'Vendor quality from internal signals only: Reliability (/25, from cancel+credit rate), Loyalty (/25, repeat buyer %), Breadth (/25, variety count), Scale (/25, buyer count). Out of 100. v2 will add external signals (certifications, brand, Instagram).'),
        ('Price tier', 'VALUE = avg &lt;$0.30/stem. MID = $0.30-0.60. PREMIUM = &gt;$0.60. Shown on vendor profile cards.'),
    ]
    for term, defn in defs:
        html.append(f'<tr><td><b>{term}</b></td><td>{defn}</td></tr>')

    html.append('</tbody></table></div>')

    # Category map
    cat_map = data['categories']
    if 'canonical_categories' in cat_map:
        html.append('<h2 style="margin-top:1.5rem;">Category Normalization Map</h2>')
        html.append('<div class="tablewrap"><table style="min-width:30rem;">')
        html.append('<thead><tr><th>Category</th><th>ID</th><th>Aliases</th><th>Fresh cut?</th></tr></thead><tbody>')
        for cat in cat_map['canonical_categories']:
            aliases = ', '.join(cat.get('aliases', [])[:5])
            fresh = '✓' if cat.get('is_fresh_cut') else '✗'
            html.append(f'<tr><td><b>{cat["canonical_name"]}</b></td><td class="num">{cat["canonical_id"]}</td><td>{aliases}</td><td>{fresh}</td></tr>')
        html.append('</tbody></table></div>')

    return '\n'.join(html)

# ============================================================
# TABS 4-5: PLACEHOLDERS
# ============================================================

def generate_tab4(data=None):
    from tab4_clean import generate_tab4 as _clean_tab4
    seasonality = data.get('seasonality', {}) if data else {}
    if seasonality and seasonality.get('zones'):
        return _clean_tab4(seasonality)
    # Fallback to mockup
    categories = ['Rose', 'Carnation', 'Hydrangea', 'Ranunculus', 'Peony', 'Tulip', 'Greens', 'Lisianthus']
    months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    # Rough demand index by category × month (1=low, 2=medium, 3=high, 4=peak)
    heat = {
        'Rose':        [3,4,3,3,4,3,2,2,2,2,3,3],
        'Carnation':   [2,3,2,2,3,2,2,2,2,2,2,3],
        'Hydrangea':   [1,2,2,3,3,4,4,3,3,2,1,1],
        'Ranunculus':  [3,3,3,4,3,2,1,1,1,2,3,3],
        'Peony':       [1,1,2,4,4,3,1,1,1,1,1,1],
        'Tulip':       [3,4,3,3,2,1,1,1,1,2,3,3],
        'Greens':      [2,3,2,2,3,3,2,2,2,2,2,3],
        'Lisianthus':  [1,2,2,3,3,4,4,3,2,1,1,1],
    }
    colors = {1:'var(--surface-2)',2:'#CCFBF1',3:'#5EEAD4',4:'#0F766E'}
    text_colors = {1:'var(--ink-3)',2:'var(--tint-ink)',3:'white',4:'white'}
    events = {1:'Valentine\'s prep',4:'Mother\'s Day',5:'Wedding season starts',9:'Fall events',11:'Thanksgiving/Holiday'}

    html = []
    html.append('<h2>Seasonality Preview</h2>')
    html.append('<div class="info-box"><b>Mockup</b> — estimated demand intensity by category and month. Based on industry patterns, not yet computed from our data. v2 will use actual procurement history × buyer state/region.</div>')

    html.append('<div class="tablewrap"><table style="min-width:40rem;text-align:center;">')
    html.append('<thead><tr><th style="text-align:left;">Category</th>')
    for i, m in enumerate(months):
        event = events.get(i, '')
        title = f' title="{event}"' if event else ''
        html.append(f'<th{title}>{m}</th>')
    html.append('</tr></thead><tbody>')

    for cat in categories:
        html.append('<tr>')
        html.append(f'<td style="text-align:left;"><b>{cat}</b></td>')
        for val in heat[cat]:
            bg = colors[val]
            fg = text_colors[val]
            label = {1:'Low',2:'Med',3:'High',4:'Peak'}[val]
            html.append(f'<td style="background:{bg};color:{fg};font-size:.7rem;font-weight:600;">{label}</td>')
        html.append('</tr>')
    html.append('</tbody></table></div>')

    # Events timeline
    html.append('<div style="margin-top:1rem;"><h3>Key events that drive demand</h3>')
    html.append('<div class="tablewrap"><table style="min-width:20rem;"><thead><tr><th>When</th><th>Event</th><th>Categories impacted</th><th>Forward sourcing starts</th></tr></thead><tbody>')
    events_list = [
        ('Feb 14', "Valentine's Day", 'Rose (peak), Carnation, Tulip', 'Mid-January (4 weeks ahead)'),
        ('May (2nd Sun)', "Mother's Day", 'Rose, Carnation, Hydrangea, Peony', 'Mid-April (3-4 weeks)'),
        ('May-Oct', 'Wedding season', 'Peony, Ranunculus, Hydrangea, Lisianthus, Garden Rose', 'March-April for peak months'),
        ('Sep-Oct', 'Fall events', 'Carnation, Greens, Mums', 'August'),
        ('Nov-Dec', 'Thanksgiving + Holiday', 'Greens, Rose, Carnation, Poinsettia', 'October-November'),
        ('Year-round', 'Funerals & sympathy', 'Rose, Carnation, Lily, Gladiolus', 'Always — steady baseline'),
    ]
    for when, event, cats, sourcing in events_list:
        html.append(f'<tr><td><b>{when}</b></td><td>{event}</td><td>{cats}</td><td>{sourcing}</td></tr>')
    html.append('</tbody></table></div></div>')

    html.append('<div class="info-box" style="margin-top:1rem;"><b>What v2 will add:</b> Actual demand curves from 12-24 months of procurement data. Broken down by buyer state/region (Northeast, Southeast, Midwest, Southwest, West). Show when to source forward for each region × category combination.</div>')

    return '\n'.join(html)

def generate_tab5(data=None):
    from tab5_clean import generate_tab5 as _clean_tab5
    accounts = data.get('accounts', {}) if data else {}
    if accounts and accounts.get('accounts'):
        return _clean_tab5(accounts)
    # Fallback to mockup
    html = []
    html.append('<h2>Account View Preview</h2>')
    html.append('<div class="info-box"><b>Mockup</b> — what the account-specific view will look like. This example uses Zeidler Floral. v2 will be dynamic for any wholesaler.</div>')

    # Account header
    html.append('<div style="background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:1.25rem;margin-bottom:1rem;">')
    html.append('<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;">')
    html.append('<div><h3 style="margin:0;">Zeidler Floral</h3><span style="font-size:.8rem;color:var(--ink-3);">Wholesaler · WH_CORE · Niagara Falls, NY</span></div>')
    html.append('<div style="display:flex;gap:1rem;font-size:.85rem;">')
    html.append('<div><b>$76.4K</b><br><span style="color:var(--ink-3);font-size:.7rem;">Procurement 6mo</span></div>')
    html.append('<div><b>9</b><br><span style="color:var(--ink-3);font-size:.7rem;">Vendors connected</span></div>')
    html.append('<div><b>5</b><br><span style="color:var(--ink-3);font-size:.7rem;">for 81% coverage</span></div>')
    html.append('</div></div></div>')

    # Current vendors
    html.append('<h3 style="margin-top:1rem;">Current Vendor Mix</h3>')
    html.append('<div class="tablewrap"><table><thead><tr><th>Vendor</th><th>Amount</th><th>% of basket</th><th>Cumulative</th><th>Quality</th></tr></thead><tbody>')
    vendors = [
        ('Sole Farms', '$17,422', '22.8%', '22.8%', '77/100'),
        ('Fresca Farms', '$12,631', '16.5%', '39.3%', '82/100'),
        ('Continental Farms', '$11,668', '15.3%', '54.6%', '82/100'),
        ('Choice Farms', '$10,544', '13.8%', '68.4%', '—'),
        ('Equiflor Corp', '$9,811', '12.8%', '81.2%', '—'),
        ('Riverdale Farms', '$6,339', '8.3%', '89.5%', '—'),
        ('US Greens Corp', '$3,962', '5.2%', '94.7%', '—'),
        ('Galleria Farms', '$3,361', '4.4%', '99.1%', '—'),
        ('Welyflor', '$684', '0.9%', '100%', '—'),
    ]
    for name, amt, pct, cum, qs in vendors:
        html.append(f'<tr><td><b>{name}</b></td><td class="num">{amt}</td><td class="num">{pct}</td><td class="num">{cum}</td><td class="num">{qs}</td></tr>')
    html.append('</tbody></table></div>')

    # Gaps
    html.append('<h3 style="margin-top:1.5rem;">Category Gaps — what Zeidler buys offline but has no online vendor for</h3>')
    html.append('<div class="tablewrap"><table><thead><tr><th>Category</th><th>Offline demand</th><th>Connected vendors</th><th>Gap</th><th>Recommended vendor</th></tr></thead><tbody>')
    gaps = [
        ('Hydrangea', '$8.2K', '0', '<span class="badge desert">DESERT</span>', 'Bella Blossom (187K, 82/100)'),
        ('Tulips', '$4.1K', '0', '<span class="badge desert">DESERT</span>', 'Jet Fresh (54K, 72/100)'),
        ('Lisianthus', '$3.5K', '0', '<span class="badge desert">DESERT</span>', 'Jet Fresh (39K, 72/100)'),
        ('Peony', '$2.8K', '0', '<span class="badge desert">DESERT</span>', 'Allure Farms (52K) — only source'),
        ('Greens', '$1.9K', '1 (US Greens)', '<span class="badge undersupplied">LIMITED</span>', 'Add foliage specialist'),
    ]
    for cat, demand, connected, gap, rec in gaps:
        html.append(f'<tr><td><b>{cat}</b></td><td class="num">{demand}</td><td class="num">{connected}</td><td>{gap}</td><td>{rec}</td></tr>')
    html.append('</tbody></table></div>')

    # Forward opportunity
    html.append('<h3 style="margin-top:1.5rem;">Forward Buying Opportunity</h3>')
    html.append('<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:1rem;">')

    html.append('<div class="panel"><h3>Current pattern</h3><p style="font-size:.85rem;color:var(--ink-2);">Zeidler buys from <b>5 vendors</b> covering 81% of basket. Concentrated — if Sole Farms or Fresca have issues, 39% of supply is at risk.</p></div>')

    html.append('<div class="panel"><h3>Recommendation</h3><ul style="font-size:.85rem;color:var(--ink-2);margin:0;padding-left:1rem;">')
    html.append('<li><b>Connect to Bella Blossom</b> for Hydrangea — $187K market, 82/100 quality</li>')
    html.append('<li><b>Connect to Jet Fresh</b> for Tulips + Lisianthus — covers 2 gaps with 1 vendor</li>')
    html.append('<li><b>Explore Allure Farms</b> for Peony — only online source, seasonal (Apr-Jun)</li>')
    html.append('</ul></div>')

    html.append('<div class="panel"><h3>Seasonal alert</h3><p style="font-size:.85rem;color:var(--ink-2);"><b>Valentine\'s prep:</b> Zeidler buys $17.4K of roses from Sole Farms. Sole has 13% forward supply. For 2-week planning, also source from <b>Continex</b> (95% at 30+d, $0.29/stem VALUE) or <b>Royal Flowers</b> (94% at 30+d).</p></div>')

    html.append('</div>')

    html.append('<div class="info-box" style="margin-top:1.5rem;"><b>What v2 will add:</b> Dynamic account lookup for any wholesaler. Real gap analysis from their procurement data × K2K connections. Personalized vendor recommendations based on their buying patterns. Requires ID crosswalk (vendor_id → global company_id).</div>')

    return '\n'.join(html)

# ============================================================
# MAIN BUILD
# ============================================================

def build(data):
    stats = data['stats']

    html_parts = []

    # DOCTYPE + HEAD
    html_parts.append(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vendor Intelligence v1</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
<style>{generate_css()}</style>
</head>
<body>
<div class="wrap">

  <header>
    <span class="eyebrow">TX &middot; Vendor Intelligence v1</span>
    <h1>Supply Intelligence for CS &amp; Implementation</h1>
    <p class="lede">What wholesalers buy, who supplies it, at what timeframe and price. Demand-first.</p>
    <div class="metaline">
      <span><b>Built</b> {BUILD_DATE}</span>
      <span><b>Data</b> Snowflake INVENTORY_DETAILS + PROCUREMENT_DETAILS</span>
      <span><b>Varieties</b> {stats['total_varieties']:,} normalized, {stats['with_demand']} with demand</span>
      <span><b>Vendors</b> {stats['with_vendor_detail']} with drill-down</span>
    </div>
  </header>

  <div class="stats">
    <div class="stat"><span class="n">{stats['with_demand']}</span><span class="l">With demand data</span></div>
    <div class="stat"><span class="n on">{stats['hot']}</span><span class="l">HOT priority</span></div>
    <div class="stat"><span class="n">{stats['relevant']}</span><span class="l">Relevant</span></div>
    <div class="stat"><span class="n">{stats['with_vendor_detail']}</span><span class="l">Vendor drill-down</span></div>
    <div class="stat"><span class="n">{stats['categories']}</span><span class="l">Categories</span></div>
  </div>

  <div class="tabs">
    <input type="radio" name="tabs" id="tab1" checked>
    <input type="radio" name="tabs" id="tab2">
    <input type="radio" name="tabs" id="tab3">
    <input type="radio" name="tabs" id="tab4">
    <input type="radio" name="tabs" id="tab5">
    <div class="tab-labels">
      <label for="tab1">What to Recommend</label>
      <label for="tab2">Vendor Profiles</label>
      <label for="tab3">Definitions</label>
      <label for="tab4">Seasonality</label>
      <label for="tab5">Account View</label>
    </div>
    <div class="tab-panels">
      <div class="tab-panel panel-1">{generate_tab1(data)}</div>
      <div class="tab-panel panel-2">{generate_tab2(data)}</div>
      <div class="tab-panel panel-3">{generate_tab3(data)}</div>
      <div class="tab-panel panel-4">{generate_tab4(data)}</div>
      <div class="tab-panel panel-5">{generate_tab5(data)}</div>
    </div>
  </div>

  <footer>
    <div><b>How to use</b> Search a variety or category. Check demand and balance. Click to see vendors with price and timeframe. Use Vendor Profiles for quality.</div>
    <div><b>Coming in v2</b> External vendor quality (certs, brand). Seasonality by region. Account-specific view. Daily refresh. Vendor quality inline in drill-down.</div>
    <div><b>Data note</b> Demand = 12mo procurement (all channels). Supply = inventory snapshot ({BUILD_DATE}). Balance is directional. {stats['with_demand']}/{stats['total_varieties']} demand matched &mdash; gap is naming differences.</div>
  </footer>

</div>
<script>{generate_js()}</script>
</body>
</html>""")

    return '\n'.join(html_parts)

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':
    print(f"Building Vendor Intelligence Dashboard...")

    # Create output dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Symlink data dir for convenience
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    data = load_data()

    # Build HTML
    html = build(data)

    # Write
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html)

    lines = html.count('\n')
    size_kb = len(html) / 1024
    print(f"Written: {OUTPUT_FILE} ({lines:,} lines, {size_kb:.0f}KB)")

    # Also copy to reports for easy access
    import shutil
    report_copy = SCRIPT_DIR / "dist" / "index.html"
    report_copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUTPUT_FILE, report_copy)
    print(f"Copied to: {report_copy}")

    # Open if requested
    if '--open' in sys.argv:
        subprocess.run(['open', str(OUTPUT_FILE)])
        print("Opened in browser.")
