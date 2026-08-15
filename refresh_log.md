# Vendor Intelligence Refresh Log

## 2026-08-15 13:23 UTC

### Status: SUCCESS (deploy pending)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 965 category rows
- ✅ variety_inventory: 1,246 variety rows (importer inventory)
- ✅ variety_demand: 794 variety rows (wholesaler demand)

### Build:
- ✅ refresh_data.py: OK — 80 vendors, 32 with categories
- ✅ build.py: OK — 640KB dashboard generated
- ✅ Audit: All checks pass

### Files updated:
- data/raw/vendor_profiles.json
- data/raw/vendor_categories.json
- data/raw/variety_inventory.json
- data/raw/variety_demand.json
- data/vendor_internal_profiles.json
- data/vendor_complete.json
- output/vendor_intelligence.html
- dist/index.html

### Git:
- ✅ Committed: 6c8589e "Daily refresh 2026-08-15"
- ✅ Pushed to origin/main

### Script fixes (one-time):
- Fixed hardcoded macOS paths in build.py and refresh_data.py
  (DATA_DIR and all /Users/facu/Koronet_OS/ops/data/* paths now resolve relative to repo root)

### Deploy:
- ❌ grootctl not installed in remote execution environment
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)

