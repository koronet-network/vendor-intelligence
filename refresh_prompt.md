# Vendor Intelligence — Refresh Trigger Prompt

This is the prompt for the scheduled Claude trigger that refreshes the Vendor Intelligence dashboard data.

## Instructions

You are refreshing data for the Vendor Intelligence dashboard. Run these 4 Snowflake queries via MCP tools, save results, then run the build script.

### Step 1: Run queries and save raw results

Create directory: `/Users/facu/Koronet_OS/ops/dashboards/vendor_intelligence/data/raw/`

**Query 1: Vendor Profiles** → save to `data/raw/vendor_profiles.json`
```sql
SELECT v.vendor_name, COUNT(*) as total_orders,
  COUNT(DISTINCT pd.company_id) as distinct_buyers,
  ROUND(SUM(pd.total_cost), 0) as total_gmv,
  ROUND(SUM(CASE WHEN pd.shipping_date >= '2026-01-01' THEN pd.total_cost ELSE 0 END), 0) as gmv_h1_2026,
  ROUND(SUM(CASE WHEN pd.shipping_date >= '2025-01-01' AND pd.shipping_date < '2025-07-01' THEN pd.total_cost ELSE 0 END), 0) as gmv_h1_2025,
  COUNT(DISTINCT pd.product_variety) as variety_count,
  COUNT(DISTINCT pd.product_category_name) as category_count,
  ROUND(SUM(CASE WHEN pd.vendor_status = 'Cancelled' THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as cancel_pct,
  ROUND(SUM(CASE WHEN pd.vendor_credit > 0 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as credit_pct,
  ROUND(AVG(CASE WHEN pd.total_stems > 0 AND pd.total_cost > 0 AND pd.total_cost/pd.total_stems BETWEEN 0.05 AND 5.0 THEN pd.total_cost / pd.total_stems END), 3) as avg_price_stem,
  ROUND(COUNT(DISTINCT CASE WHEN buyer_orders >= 3 THEN pd.company_id END) * 1.0 / NULLIF(COUNT(DISTINCT pd.company_id), 0) * 100, 1) as repeat_buyer_pct
FROM PRODUCTION.ANALYTICS.PROCUREMENT_DETAILS pd
JOIN PRODUCTION.ANALYTICS.VENDORS v ON pd.company_id = v.company_id AND pd.vendor_id = v.vendor_id
LEFT JOIN (
  SELECT company_id, vendor_id, COUNT(*) as buyer_orders
  FROM PRODUCTION.ANALYTICS.PROCUREMENT_DETAILS WHERE ks_flag = TRUE AND shipping_date >= DATEADD(MONTH, -12, CURRENT_DATE)
  GROUP BY company_id, vendor_id
) bo ON pd.company_id = bo.company_id AND pd.vendor_id = bo.vendor_id
WHERE pd.ks_flag = TRUE AND pd.shipping_date >= DATEADD(MONTH, -18, CURRENT_DATE)
GROUP BY v.vendor_name HAVING COUNT(*) >= 1000
ORDER BY total_gmv DESC LIMIT 80
```

**Query 2: Vendor Categories × Timeframe** → save to `data/raw/vendor_categories.json`
Use the exact vendor names from Query 1 in the IN clause. Query:
```sql
SELECT v.vendor_name, pd.product_category_name as category,
  ROUND(SUM(pd.total_cost), 0) as sold, SUM(pd.total_stems) as stems,
  COUNT(DISTINCT pd.company_id) as buyers,
  SUM(CASE WHEN pd.audit_creation_date IS NOT NULL AND DATEDIFF(DAY, pd.audit_creation_date, pd.shipping_date) BETWEEN 0 AND 2 THEN pd.total_stems ELSE 0 END) as s_spot,
  SUM(CASE WHEN pd.audit_creation_date IS NOT NULL AND DATEDIFF(DAY, pd.audit_creation_date, pd.shipping_date) BETWEEN 3 AND 7 THEN pd.total_stems ELSE 0 END) as s_short,
  SUM(CASE WHEN pd.audit_creation_date IS NOT NULL AND DATEDIFF(DAY, pd.audit_creation_date, pd.shipping_date) BETWEEN 8 AND 14 THEN pd.total_stems ELSE 0 END) as s_med,
  SUM(CASE WHEN pd.audit_creation_date IS NOT NULL AND DATEDIFF(DAY, pd.audit_creation_date, pd.shipping_date) BETWEEN 15 AND 30 THEN pd.total_stems ELSE 0 END) as s_fwd,
  SUM(CASE WHEN pd.audit_creation_date IS NOT NULL AND DATEDIFF(DAY, pd.audit_creation_date, pd.shipping_date) > 30 THEN pd.total_stems ELSE 0 END) as s_deep
FROM PRODUCTION.ANALYTICS.PROCUREMENT_DETAILS pd
JOIN PRODUCTION.ANALYTICS.VENDORS v ON pd.company_id = v.company_id AND pd.vendor_id = v.vendor_id
WHERE pd.ks_flag = TRUE AND pd.shipping_date >= DATEADD(MONTH, -12, CURRENT_DATE)
  AND pd.product_category_name IS NOT NULL AND pd.product_category_name != ''
  AND v.vendor_name IN ([VENDOR NAMES FROM QUERY 1])
GROUP BY v.vendor_name, category
HAVING SUM(pd.total_cost) >= 500
ORDER BY v.vendor_name, sold DESC
```

**Query 3: Variety Inventory** → save to `data/raw/variety_inventory.json`
```sql
SELECT INITCAP(canonical_norm) as name, COUNT(DISTINCT vendor_name) as vendors,
  SUM(total_stems) as total_stems, ROUND(SUM(total_cost), 0) as value,
  SUM(CASE WHEN awb_arrival_date IS NULL OR awb_arrival_date <= CURRENT_DATE THEN total_stems ELSE 0 END) as in_stock,
  SUM(CASE WHEN awb_arrival_date BETWEEN CURRENT_DATE AND DATEADD(DAY, 7, CURRENT_DATE) THEN total_stems ELSE 0 END) as arriving_7d,
  SUM(CASE WHEN awb_arrival_date BETWEEN DATEADD(DAY, 8, CURRENT_DATE) AND DATEADD(DAY, 14, CURRENT_DATE) THEN total_stems ELSE 0 END) as arriving_14d,
  SUM(CASE WHEN awb_arrival_date BETWEEN DATEADD(DAY, 15, CURRENT_DATE) AND DATEADD(DAY, 30, CURRENT_DATE) THEN total_stems ELSE 0 END) as arriving_30d,
  SUM(CASE WHEN awb_arrival_date > DATEADD(DAY, 30, CURRENT_DATE) THEN total_stems ELSE 0 END) as arriving_30plus,
  CASE WHEN SUM(CASE WHEN awb_arrival_date > DATEADD(DAY, 14, CURRENT_DATE) THEN total_stems ELSE 0 END) > 100000 THEN 'STRONG'
    WHEN SUM(CASE WHEN awb_arrival_date > DATEADD(DAY, 14, CURRENT_DATE) THEN total_stems ELSE 0 END) > 10000 THEN 'MODERATE'
    WHEN SUM(CASE WHEN awb_arrival_date > DATEADD(DAY, 14, CURRENT_DATE) THEN total_stems ELSE 0 END) > 0 THEN 'THIN'
    ELSE 'SPOT_ONLY' END as forward_score
FROM (
  SELECT *, CASE
    WHEN LOWER(TRIM(product_variety)) IN ('israeli ruscus','ruscus israeli','ruscus israel') THEN 'israeli ruscus'
    WHEN LOWER(TRIM(product_variety)) IN ('italian ruscus','ruscus italian') THEN 'italian ruscus'
    WHEN LOWER(TRIM(product_variety)) IN ('high and magic','high & magic') THEN 'high & magic'
    WHEN LOWER(TRIM(product_variety)) = 'mundial' THEN 'mondial'
    WHEN LOWER(TRIM(product_variety)) = 'floyd' THEN 'pink floyd'
    WHEN LOWER(TRIM(product_variety)) = 'freedom red' THEN 'freedom'
    ELSE LOWER(TRIM(product_variety))
  END as canonical_norm
  FROM PRODUCTION.ANALYTICS.INVENTORY_DETAILS
  WHERE ks_flag = TRUE AND company_industry = 'Floral - Importer'
    AND product_variety IS NOT NULL AND product_variety != '' AND total_stems > 0
    AND NOT (LOWER(TRIM(product_variety)) LIKE '(%'
      OR LOWER(TRIM(product_variety)) IN ('assorted','color','mix','mixed','-','n/a','none','unknown','production')
      OR LOWER(TRIM(product_variety)) LIKE '%dozen%' OR LOWER(TRIM(product_variety)) LIKE '%wreath%')
)
GROUP BY canonical_norm HAVING SUM(total_stems) >= 10000
ORDER BY total_stems DESC
```

**Query 4: Variety Demand** → save to `data/raw/variety_demand.json`
```sql
SELECT LOWER(TRIM(product_variety)) as norm, INITCAP(LOWER(TRIM(product_variety))) as name,
  ROUND(SUM(total_cost), 0) as demand_total,
  ROUND(SUM(CASE WHEN sales_channel = 'Procurement' THEN total_cost ELSE 0 END), 0) as demand_online,
  ROUND(SUM(CASE WHEN sales_channel != 'Procurement' THEN total_cost ELSE 0 END), 0) as demand_offline,
  COUNT(DISTINCT company_id) as buyers
FROM PRODUCTION.ANALYTICS.PROCUREMENT_DETAILS
WHERE ks_flag = TRUE AND shipping_date >= DATEADD(MONTH, -12, CURRENT_DATE)
  AND product_variety IS NOT NULL AND product_variety != ''
  AND company_id IN (SELECT company_id FROM PRODUCTION.ANALYTICS.COMPANIES WHERE company_industry = 'Floral - Wholesaler' AND ks_flag = TRUE)
GROUP BY norm HAVING SUM(total_cost) >= 50000
ORDER BY demand_total DESC
```

### Step 2: Save results

For each query, extract the `result_set.data` array and save as a JSON array to the corresponding file in `data/raw/`.

### Step 3: Run refresh

```bash
cd /Users/facu/Koronet_OS/ops/dashboards/vendor_intelligence
python3 refresh_data.py
```

### Step 4: Verify

Check `last_refresh.json` for status. If errors, report them. If OK, the dashboard at `output/vendor_intelligence.html` is updated.
