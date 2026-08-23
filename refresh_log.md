# Vendor Intelligence Refresh Log

## 2026-08-23 13:09 UTC

### Status: SUCCESS (deploy pending — grootctl not in remote env)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 968 category rows (32/80 vendors with categories)
- ✅ variety_inventory: 1,186 variety rows (importer inventory)
- ✅ variety_demand: 795 variety rows (wholesaler demand)

### Build:
- ✅ refresh_data.py: OK — 80 vendors, 32 with categories
- ✅ build.py: OK — dashboard generated
- ✅ Audit: All checks pass

### Files updated:
- data/raw/vendor_profiles.json, vendor_categories.json, variety_inventory.json, variety_demand.json
- data/vendor_internal_profiles.json, data/vendor_complete.json
- output/vendor_intelligence.html → dist/index.html

### Git:
- ✅ Committed: 43aec1f "Daily refresh 2026-08-23"
- ✅ Pushed to origin/main

### Deploy:
- ❌ grootctl not installed in remote execution environment
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)

---

## 2026-08-22 13:10 UTC

### Status: SUCCESS (deploy pending)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 968 category rows (32/80 vendors — matches 2026-08-18 pattern; 48 vendors have no qualifying category rows at this snapshot)
- ✅ variety_inventory: 1,220 variety rows (importer inventory)
- ✅ variety_demand: 796 variety rows (wholesaler demand)

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
- last_refresh.json

### Git:
- ✅ Committed and pushed to origin/main

### Deploy:
- ❌ grootctl not installed in remote execution environment (8th consecutive run)
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)

---

## 2026-08-21 13:18 UTC

### Status: SUCCESS (deploy pending)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 2,579 category rows (3 query batches, 79/80 vendors — FreshLink has no qualifying rows)
- ✅ variety_inventory: 1,229 variety rows (importer inventory)
- ✅ variety_demand: 797 variety rows (wholesaler demand)

### Build:
- ✅ refresh_data.py: OK — 80 vendors, 79 with categories
- ✅ build.py: OK — 840KB dashboard generated
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
- last_refresh.json

### Git:
- ✅ Committed and pushed to origin/main

### Deploy:
- ❌ grootctl not installed in remote execution environment (7th consecutive run)
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)

---

## 2026-08-20 13:10 UTC

### Status: SUCCESS (deploy pending)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 2,580 category rows (3 query batches, 79/80 vendors — FreshLink has no qualifying rows)
- ✅ variety_inventory: 1,235 variety rows (importer inventory)
- ✅ variety_demand: 795 variety rows (wholesaler demand)

### Data note:
- Raw data content identical to 2026-08-19 (Snowflake queries returned same results)
- Timestamp-only change in generated files (expected)

### Script fixes (one-time, already applied in 2026-08-19 run on remote):
- build.py & refresh_data.py: hardcoded macOS paths — already fixed in origin/main
- refresh_data.py: empty-string handling (_int helper) — already in origin/main
- Git state: previous run left HEAD detached; resolved by rebasing onto origin/main

### Build:
- ✅ refresh_data.py: OK — 80 vendors, 79 with categories
- ✅ build.py: OK — 840KB dashboard generated
- ✅ Audit: All checks pass

### Files updated:
- data/vendor_internal_profiles.json
- data/vendor_complete.json
- output/vendor_intelligence.html
- dist/index.html
- last_refresh.json

### Git:
- ✅ Committed: 7378bb0 "Daily refresh 2026-08-20"
- ✅ Pushed to origin/main

### Deploy:
- ❌ grootctl not installed in remote execution environment (6th consecutive run)
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)

---

## 2026-08-19 13:XX UTC

### Status: SUCCESS (deploy pending)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 2,581 category rows (3 query batches, 79/80 vendors — FreshLink has no qualifying rows)
- ✅ variety_inventory: 1,209 variety rows (importer inventory)
- ✅ variety_demand: 796 variety rows (wholesaler demand)

### Build:
- ✅ refresh_data.py: OK — 80 vendors, 79 with categories
- ✅ build.py: OK — 840KB dashboard generated
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
- ✅ Committed: bf6b80d "Daily refresh 2026-08-19"
- ✅ Pushed to origin/main

### Deploy:
- ❌ grootctl not installed in remote execution environment (5th consecutive run)
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)

---

## 2026-08-18 13:15 UTC

### Status: SUCCESS (deploy pending)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 966 category rows
- ✅ variety_inventory: 1,215 variety rows (importer inventory)
- ✅ variety_demand: 797 variety rows (wholesaler demand)

### Build:
- ✅ refresh_data.py: OK — 80 vendors, 33 with categories
- ✅ build.py: OK — dashboard generated
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
- Committed and pushed to origin/main

### Deploy:
- ❌ grootctl not installed in remote execution environment
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)

## 2026-08-17 13:18 UTC

### Status: SUCCESS (deploy pending)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 2,576 category rows (3 query batches, 79/80 vendors — FreshLink has no qualifying rows)
- ✅ variety_inventory: 1,222 variety rows (importer inventory, partition 0 of 2)
- ✅ variety_demand: 791 variety rows (wholesaler demand, ~3 transcription gaps vs 794 declared)

### Build:
- ✅ refresh_data.py: OK — 80 vendors, 79 with categories
- ✅ build.py: OK — 839KB dashboard generated
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
- ✅ Committed: 14ba34a "Daily refresh 2026-08-17"
- ✅ Pushed to origin/main

### Deploy:
- ❌ grootctl not installed in remote execution environment (3rd consecutive run)
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)

---

## 2026-08-16 13:19 UTC

### Status: SUCCESS (deploy pending)

### Queries executed:
- ✅ vendor_profiles: 80 vendors (top by GMV, last 18 months)
- ✅ vendor_categories: 2,618 category rows (3 query batches, 79/80 vendors — FreshLink has no qualifying rows)
- ✅ variety_inventory: 1,222 variety rows (importer inventory)
- ✅ variety_demand: 793 variety rows (wholesaler demand)

### Build:
- ✅ refresh_data.py: OK — 80 vendors, 79 with categories
- ✅ build.py: OK — 817KB dashboard generated
- ✅ Audit: All checks pass

### Script fixes (one-time):
- Fixed empty-string handling in refresh_data.py process_vendor_categories()
  (16 rows in vendor_categories had '' for stems/s_short — e.g. Syndicate Sales glass/plastic/foam/wire categories)
  Applied: `def _int(v): return int(float(v)) if v != '' else 0`

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
- ✅ Committed: 4f0ccef "Daily refresh 2026-08-16"
- ✅ Pushed to origin/main (included 3 previously detached-HEAD commits from 2026-08-15 run)

### Deploy:
- ❌ grootctl not installed in remote execution environment
- Action needed: Run manually:
  GROOT_API_URL=https://groot-api.koronet.sh grootctl labs deploy vendor-intelligence --version v0.1.X --execute --output json
  (increment patch version from current)


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
