#!/usr/bin/env python3
"""
Vendor Intelligence — Data Refresh & Build
============================================
This script handles the LOCAL part of the refresh:
- Merge query results into the right JSON format
- Run build.py
- Audit the output
- Update last_refresh.json

The Snowflake QUERIES are run by a Claude scheduled trigger
(see refresh_prompt.md) which saves raw results to data/raw/.
This script processes those raw results.

Usage:
  python3 refresh_data.py              # process raw → build → audit
  python3 refresh_data.py --status     # show last refresh status
"""

import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
RAW_DIR = SCRIPT_DIR / "data" / "raw"
OUTPUT_DIR = SCRIPT_DIR / "output"
LAST_REFRESH = SCRIPT_DIR / "last_refresh.json"

# ============================================================
# STATUS
# ============================================================

def show_status():
    if LAST_REFRESH.exists():
        with open(LAST_REFRESH) as f:
            status = json.load(f)
        print(f"Last refresh: {status.get('timestamp', 'unknown')}")
        print(f"Status: {status.get('status', 'unknown')}")
        print(f"Varieties: {status.get('varieties', '?')}")
        print(f"Vendors: {status.get('vendors', '?')}")
        print(f"Vendors with categories: {status.get('vendors_with_cats', '?')}")
        if status.get('errors'):
            print(f"Errors: {status['errors']}")
    else:
        print("No refresh has been run yet.")

# ============================================================
# PROCESS RAW QUERY RESULTS
# ============================================================

def process_vendor_profiles(raw_data):
    """Process raw vendor profile query results into vendor_internal_profiles.json"""
    vendors = []
    for row in raw_data:
        name, orders, buyers, gmv_total, gmv_h1_2026, gmv_h1_2025, varieties, categories, cancel, credit, price, repeat_pct = row
        yoy = round((int(float(gmv_h1_2026)) / int(float(gmv_h1_2025)) - 1) * 100, 1) if gmv_h1_2025 and float(gmv_h1_2025) > 0 else None
        vendors.append({
            "name": name, "orders": int(orders), "buyers": int(buyers),
            "gmv_total": int(float(gmv_total)),
            "gmv_h1_2026": int(float(gmv_h1_2026)), "gmv_h1_2025": int(float(gmv_h1_2025)),
            "yoy_pct": yoy,
            "varieties": int(varieties), "categories": int(categories),
            "cancel_pct": float(cancel), "credit_pct": float(credit),
            "avg_price_stem": float(price) if price else 0,
            "repeat_buyer_pct": float(repeat_pct)
        })
    return {"_metadata": {"generated_at": datetime.now().isoformat(), "count": len(vendors)}, "vendors": vendors}


def process_vendor_categories(raw_data, profiles):
    """Process vendor category query and merge with profiles into vendor_complete.json"""
    # Build vendor base from profiles
    vendors = {}
    for p in profiles['vendors']:
        name = p['name']
        r = min(25, max(0, int(25 - p.get('cancel_pct', 0) * 10 - p.get('credit_pct', 0) * 5)))
        l = min(25, int(p.get('repeat_buyer_pct', 0) * 0.25))
        b = min(25, int(p.get('varieties', 0) / 30))
        s = min(25, int(p.get('buyers', 0) / 4))
        price = p.get('avg_price_stem', 0) or 0
        vendors[name] = {
            'name': name, 'quality_score': r + l + b + s,
            'qs_r': r, 'qs_l': l, 'qs_b': b, 'qs_s': s,
            'cancel_pct': p.get('cancel_pct', 0), 'credit_pct': p.get('credit_pct', 0),
            'repeat_pct': p.get('repeat_buyer_pct', 0), 'buyers': p.get('buyers', 0),
            'gmv_total': p.get('gmv_total', 0), 'yoy_pct': p.get('yoy_pct'),
            'total_varieties': p.get('varieties', 0), 'avg_price': price,
            'price_tier': 'PREMIUM' if price > 0.60 else 'MID' if price > 0.30 else 'VALUE',
            'categories': [], 'varieties': [],
            'timeframe_total': {'spot': 0, 'short': 0, 'med': 0, 'fwd': 0, 'deep': 0}
        }

    # Add category data
    for row in raw_data:
        vname, cat, sold, stems, buyers, s_spot, s_short, s_med, s_fwd, s_deep = row
        if vname not in vendors:
            continue
        def _int(v): return int(float(v)) if v != '' else 0
        vendors[vname]['categories'].append({
            'category': cat, 'sold': _int(sold), 'stems': _int(stems), 'buyers': _int(buyers),
            's_spot': _int(s_spot), 's_short': _int(s_short), 's_med': _int(s_med),
            's_fwd': _int(s_fwd), 's_deep': _int(s_deep)
        })
        for k, val in [('spot', s_spot), ('short', s_short), ('med', s_med), ('fwd', s_fwd), ('deep', s_deep)]:
            vendors[vname]['timeframe_total'][k] += _int(val)

    # Compute forward % and sort
    for v in vendors.values():
        total_s = sum(v['timeframe_total'].values())
        v['forward_pct'] = round((v['timeframe_total']['fwd'] + v['timeframe_total']['deep']) / total_s * 100, 1) if total_s > 0 else 0
        v['categories'].sort(key=lambda x: -x['sold'])
        v['categories'] = v['categories'][:10]
        v['top_category_names'] = [c['category'] for c in v['categories'][:5]]

    with_cats = sum(1 for v in vendors.values() if v['categories'])
    return {
        "_metadata": {"generated_at": datetime.now().isoformat(), "vendors": len(vendors), "with_categories": with_cats},
        "vendors": vendors
    }, with_cats


def process_variety_inventory(raw_data):
    """Process variety inventory query into variety data with supply by timeframe"""
    varieties = []
    for row in raw_data:
        name, vendors, total_stems, value, in_stock, d7, d14, d30, d30p, fwd_score = row
        varieties.append({
            "name": name, "vendors": int(vendors), "total_stems": int(total_stems),
            "value": int(float(value)), "in_stock": int(in_stock),
            "arriving_7d": int(d7), "arriving_14d": int(d14),
            "arriving_30d": int(d30), "arriving_30plus": int(d30p),
            "forward_score": fwd_score
        })
    return {"_metadata": {"generated_at": datetime.now().isoformat()}, "varieties": varieties}

# ============================================================
# BUILD + AUDIT
# ============================================================

def run_build():
    """Run build.py and return success/failure"""
    result = subprocess.run(
        ['python3', 'build.py'],
        cwd=str(SCRIPT_DIR),
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, result.stdout


def audit_output():
    """Audit the generated HTML"""
    html_path = OUTPUT_DIR / "vendor_intelligence.html"
    if not html_path.exists():
        return False, "HTML file not found"

    with open(html_path) as f:
        html = f.read()

    import re
    style_end = html.find('</style>')
    body = html[style_end:] if style_end > 0 else html

    checks = {
        'has_5_tabs': len(re.findall(r'id="tab\d"', html)) >= 5,
        'has_varieties': html.count('variety-row') > 50,
        'has_vendors': html.count('vendor-row') > 20,
        'has_tiers': 'Top Vendors' in html,
        'has_search': 'id="search"' in html,
        'has_js': '<script>' in html and '</script>' in html,
        'tags_balanced': (
            len(re.findall(r'<details[\s>]', body)) == len(re.findall(r'</details>', body))
        ),
        'html_complete': '</html>' in html,
    }

    all_pass = all(checks.values())
    failures = [k for k, v in checks.items() if not v]
    return all_pass, failures if failures else "All checks pass"

# ============================================================
# MAIN
# ============================================================

def refresh():
    """Full refresh: process raw data → build → audit → update status"""
    timestamp = datetime.now().isoformat()
    errors = []

    # Check which raw files exist
    raw_files = {
        'vendor_profiles': RAW_DIR / 'vendor_profiles.json',
        'vendor_categories': RAW_DIR / 'vendor_categories.json',
        'variety_inventory': RAW_DIR / 'variety_inventory.json',
        'variety_demand': RAW_DIR / 'variety_demand.json',
    }

    available = {k: v.exists() for k, v in raw_files.items()}
    print(f"Raw data available: {available}")

    # Process what we have
    vendors_count = 0
    vendors_with_cats = 0
    varieties_count = 0

    if available['vendor_profiles']:
        with open(raw_files['vendor_profiles']) as f:
            raw = json.load(f)
        profiles = process_vendor_profiles(raw)
        with open(DATA_DIR / 'vendor_internal_profiles.json', 'w') as f:
            json.dump(profiles, f, indent=2)
        vendors_count = len(profiles['vendors'])
        print(f"  Vendor profiles: {vendors_count}")

        if available['vendor_categories']:
            with open(raw_files['vendor_categories']) as f:
                cat_raw = json.load(f)
            complete, vendors_with_cats = process_vendor_categories(cat_raw, profiles)
            with open(DATA_DIR / 'vendor_complete.json', 'w') as f:
                json.dump(complete, f, indent=2)
            print(f"  Vendor complete: {len(complete['vendors'])} vendors, {vendors_with_cats} with categories")
    else:
        errors.append("vendor_profiles.json not found")

    # Build
    print("Building dashboard...")
    build_ok, build_msg = run_build()
    if not build_ok:
        errors.append(f"Build failed: {build_msg}")
        print(f"  BUILD FAILED: {build_msg}")
    else:
        print(f"  Build OK")

    # Audit
    if build_ok:
        audit_ok, audit_msg = audit_output()
        if not audit_ok:
            errors.append(f"Audit failed: {audit_msg}")
            print(f"  AUDIT FAILED: {audit_msg}")
        else:
            print(f"  Audit OK: {audit_msg}")

    # Update status
    status = {
        "timestamp": timestamp,
        "status": "OK" if not errors else "ERRORS",
        "varieties": varieties_count,
        "vendors": vendors_count,
        "vendors_with_cats": vendors_with_cats,
        "errors": errors if errors else None,
        "raw_available": available,
    }
    with open(LAST_REFRESH, 'w') as f:
        json.dump(status, f, indent=2)

    return not errors


if __name__ == '__main__':
    if '--status' in sys.argv:
        show_status()
    else:
        # Create raw dir if needed
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        success = refresh()
        sys.exit(0 if success else 1)
