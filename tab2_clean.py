"""Clean Tab 2 generator — reads vendor_complete.json"""
import json, sys

def fmt_money(val):
    if not val or val == 0: return "$0"
    if val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if val >= 1_000: return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"

def fmt_stems(val):
    if not val or val == 0: return "&mdash;"
    if val >= 1_000_000: return f"{val/1_000_000:.2f}M"
    if val >= 1_000: return f"{val/1_000:.0f}K"
    return f"{val:,}"

def generate_tab2(vendors_dict):
    vendors = sorted(vendors_dict.values(), key=lambda x: -x.get('quality_score', 0))
    h = []

    # Banner
    h.append('<div class="info-box">Vendors scored 0-100 based on <b>reliability</b> (low cancellations), <b>buyer loyalty</b> (repeat purchases), <b>catalog breadth</b>, and <b>adoption</b> (how many wholesalers buy from them). Click any vendor to see details.</div>')

    # Filters
    h.append('<div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-bottom:1rem;align-items:center;">')
    h.append('<input type="text" id="vendor-search" class="search-box" style="width:auto;flex:1;min-width:200px;margin:0;" placeholder="Search vendor or category...">')
    h.append('<div class="filters" style="margin:0;"><span class="pill active" data-group="quality" data-filter="all">All</span><span class="pill" data-group="quality" data-filter="high">High (70+)</span><span class="pill" data-group="quality" data-filter="mid">Mid (40-70)</span></div>')
    h.append('<div class="filters" style="margin:0;"><span class="pill active" data-group="vfwd" data-filter="all">All</span><span class="pill" data-group="vfwd" data-filter="forward">Has forward</span><span class="pill" data-group="vfwd" data-filter="spot">Spot only</span></div>')
    h.append('</div>')

    # Tier groups
    tiers = [
        ('Top Vendors', [v for v in vendors if v.get('quality_score',0) >= 70], 'Reliable, broad catalog, well-adopted.', True),
        ('Good Options', [v for v in vendors if 40 <= v.get('quality_score',0) < 70], 'Solid vendors with some trade-offs.', False),
        ('Use with Caution', [v for v in vendors if v.get('quality_score',0) < 40], 'Higher cancel rates or limited data.', False),
    ]

    for tier_name, tier_vendors, tier_desc, tier_open in tiers:
        if not tier_vendors:
            continue
        h.append(f'<details{" open" if tier_open else ""} style="margin-bottom:1rem;">')
        h.append(f'<summary style="font-size:1rem;font-weight:700;padding:.6rem .75rem;">{tier_name} <span style="font-size:.8rem;font-weight:400;color:var(--ink-3);">({len(tier_vendors)} &mdash; {tier_desc})</span></summary>')
        h.append('<div style="padding:.25rem 0;">')

        for v in tier_vendors:
            qs = v.get('quality_score', 0)
            cancel = v.get('cancel_pct', 0)
            repeat = v.get('repeat_pct', 0)
            buyers = v.get('buyers', 0)
            price_tier = v.get('price_tier', 'VALUE')
            fwd_pct = v.get('forward_pct', 0)
            gmv = v.get('gmv_total', 0)
            cats = v.get('top_category_names', [])
            categories = v.get('categories', [])
            total_var = v.get('total_varieties', 0)
            avg_price = v.get('avg_price', 0)

            has_forward = 'forward' if fwd_pct > 0 else 'spot'
            quality_tier = 'high' if qs >= 70 else 'mid' if qs >= 40 else 'low'
            cancel_style = 'color:#E11D48;font-weight:600;' if cancel > 1 else ''

            # Category chips
            cat_chips = ''.join(f'<span style="font-size:.6rem;background:#CCFBF1;color:#0B5F58;padding:.1rem .35rem;border-radius:3px;margin-right:.2rem;">{c}</span>' for c in cats[:4])

            # Best for
            bf = []
            if cats:
                bf.append(' + '.join(cats[:3]))
            if fwd_pct > 20:
                bf.append('forward planning')
            elif fwd_pct == 0:
                bf.append('spot buying')
            bf.append(price_tier.lower() + ' price')
            best_for = ', '.join(bf)

            # Score circle
            score_bg = '#D1FAE5' if qs >= 70 else '#FEF3C7' if qs >= 40 else '#FFE4E6'
            score_fg = '#065F46' if qs >= 70 else '#92400E' if qs >= 40 else '#9F1239'

            search_text = f"{v['name']} {' '.join(cats)}".lower().replace('"', '')

            h.append(f'<details class="vendor-row" data-quality="{quality_tier}" data-vfwd="{has_forward}" data-search="{search_text}" style="margin-bottom:.35rem;">')
            h.append(f'<summary style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;padding:.55rem .75rem;">')
            h.append(f'<span style="display:inline-flex;align-items:center;justify-content:center;width:2.2rem;height:2.2rem;border-radius:50%;background:{score_bg};color:{score_fg};font-family:var(--display);font-size:.85rem;font-weight:700;flex-shrink:0;">{qs}</span>')
            h.append(f'<span style="flex:1;min-width:180px;"><b>{v["name"]}</b> {cat_chips}<br><span style="font-size:.72rem;color:var(--ink-3);">Best for: {best_for}</span></span>')
            h.append(f'<span class="badge {price_tier.lower()}" style="font-size:.55rem;">{price_tier}</span>')
            if fwd_pct > 0:
                h.append(f'<span style="font-size:.75rem;color:#059669;font-weight:600;">{fwd_pct:.0f}% fwd</span>')
            else:
                h.append(f'<span style="font-size:.75rem;color:var(--ink-3);">spot</span>')
            h.append(f'<span style="font-size:.75rem;{cancel_style}">{cancel:.1f}% canc</span>')
            h.append(f'<span style="font-size:.75rem;color:var(--ink-3);">{repeat:.0f}% rpt</span>')
            h.append(f'<span style="font-size:.75rem;color:var(--ink-3);">{buyers} buy</span>')
            h.append('</summary>')

            # EXPAND
            h.append('<div style="padding:.75rem 1rem;border-top:1px solid var(--line);background:var(--surface);">')

            # Quality signals
            r_icon = '✅' if cancel < 1 else '⚠️' if cancel < 3 else '🔴'
            l_icon = '✅' if repeat > 75 else '⚠️' if repeat > 50 else '🔴'
            h.append('<div style="display:flex;gap:.75rem 1.5rem;flex-wrap:wrap;font-size:.8rem;color:var(--ink-2);margin-bottom:.6rem;">')
            h.append(f'<span>{r_icon} {cancel:.2f}% cancelled</span>')
            h.append(f'<span>{l_icon} {repeat:.0f}% repeat buyers</span>')
            h.append(f'<span>{"✅" if total_var > 500 else "📦"} {total_var:,} varieties</span>')
            h.append(f'<span>{"✅" if buyers > 20 else "📊"} {buyers} wholesalers</span>')
            h.append(f'<span>💰 ${avg_price:.2f}/stem</span>')
            h.append(f'<span>{fmt_money(gmv)} GMV</span>')
            h.append('</div>')

            # Timeframe bar
            tf = v.get('timeframe_total', {})
            tf_total = sum(tf.values()) or 1
            spot_pct = round(tf.get('spot', 0) / tf_total * 100)
            short_pct = round(tf.get('short', 0) / tf_total * 100)
            med_pct = round(tf.get('med', 0) / tf_total * 100)
            fwd_total_pct = round((tf.get('fwd', 0) + tf.get('deep', 0)) / tf_total * 100)

            if sum(tf.values()) > 0:
                h.append('<div style="margin-bottom:.75rem;">')
                h.append('<div style="display:flex;height:14px;border-radius:6px;overflow:hidden;margin-bottom:.25rem;">')
                if spot_pct > 1:
                    h.append(f'<div style="width:{spot_pct}%;background:#ef4444;display:flex;align-items:center;justify-content:center;font-size:.55rem;color:white;font-weight:600;">{spot_pct}%</div>')
                if short_pct > 1:
                    h.append(f'<div style="width:{short_pct}%;background:#f97316;display:flex;align-items:center;justify-content:center;font-size:.55rem;color:white;font-weight:600;">{short_pct}%</div>')
                if med_pct > 1:
                    h.append(f'<div style="width:{med_pct}%;background:#eab308;display:flex;align-items:center;justify-content:center;font-size:.55rem;color:white;font-weight:600;">{med_pct}%</div>')
                if fwd_total_pct > 1:
                    h.append(f'<div style="width:{fwd_total_pct}%;background:#059669;display:flex;align-items:center;justify-content:center;font-size:.55rem;color:white;font-weight:600;">{fwd_total_pct}%</div>')
                h.append('</div>')
                h.append('<div style="display:flex;gap:.75rem;font-size:.65rem;color:var(--ink-3);">')
                h.append('<span>🔴 Spot</span><span>🟠 Short (3-7d)</span><span>🟡 Med (8-14d)</span><span>🟢 Forward (15+d)</span>')
                h.append('</div></div>')

            # Categories
            if categories:
                h.append('<h3 style="font-size:.8rem;margin:0 0 .4rem;color:var(--ink);">What they sell (by category × timeframe)</h3>')
                h.append('<div class="tablewrap"><table class="sub-table">')
                h.append('<thead><tr><th>Category</th><th>Sold</th><th>Buyers</th><th>Spot</th><th>3-7d</th><th>8-14d</th><th>15-30d</th><th>30+d</th></tr></thead><tbody>')
                for c in categories[:10]:
                    has_fwd = (c.get('s_fwd', 0) + c.get('s_deep', 0)) > 0
                    fs = 'font-weight:600;color:#059669;' if has_fwd else ''
                    h.append(f'<tr><td><b>{c["category"]}</b></td>')
                    h.append(f'<td class="num">{fmt_money(c["sold"])}</td>')
                    h.append(f'<td class="num">{c["buyers"]}</td>')
                    h.append(f'<td class="num">{fmt_stems(c.get("s_spot",0))}</td>')
                    h.append(f'<td class="num">{fmt_stems(c.get("s_short",0))}</td>')
                    h.append(f'<td class="num">{fmt_stems(c.get("s_med",0))}</td>')
                    h.append(f'<td class="num" style="{fs}">{fmt_stems(c.get("s_fwd",0))}</td>')
                    h.append(f'<td class="num" style="{fs}">{fmt_stems(c.get("s_deep",0))}</td></tr>')
                h.append('</tbody></table></div>')
            else:
                h.append(f'<p style="font-size:.8rem;color:var(--ink-3);">Category detail not available yet. Profile based on {total_var:,} varieties across {buyers} buyers.</p>')

            h.append('</div></details>')  # close vendor

        h.append('</div></details>')  # close tier

    # JS
    h.append("""<script>
(function(){
  var s=document.getElementById('vendor-search');
  if(s)s.addEventListener('input',function(e){
    var q=e.target.value.toLowerCase();
    document.querySelectorAll('.vendor-row').forEach(function(r){r.style.display=(q===''||r.dataset.search.indexOf(q)>=0)?'':'none';});
  });
  document.querySelectorAll('.panel-2 .pill').forEach(function(p){
    p.addEventListener('click',function(){
      var g=this.dataset.group;
      document.querySelectorAll('.panel-2 .pill[data-group="'+g+'"]').forEach(function(x){x.classList.remove('active');});
      this.classList.add('active');
      var qf=document.querySelector('.panel-2 .pill[data-group="quality"].active').dataset.filter;
      var ff=document.querySelector('.panel-2 .pill[data-group="vfwd"].active').dataset.filter;
      document.querySelectorAll('.vendor-row').forEach(function(r){
        r.style.display=(qf==='all'||r.dataset.quality===qf)&&(ff==='all'||r.dataset.vfwd===ff)?'':'none';
      });
    });
  });
})();
</script>""")

    return '\n'.join(h)

if __name__ == '__main__':
    with open('/Users/facu/Koronet_OS/ops/data/vendor_complete.json') as f:
        data = json.load(f)
    html = generate_tab2(data['vendors'])
    vs = list(data['vendors'].values())
    print(f"Generated: {len(vs)} vendors, {sum(1 for v in vs if v.get('categories'))} with categories", file=sys.stderr)
    for k, v in {'search':'vendor-search','pills':'pill','details':'<details','category table':'sub-table','timeframe':'time-bar' if 'time-bar' in html else '14px','quality':'cancelled','tiers':'Top Vendors','best for':'Best for'}.items():
        print(f"  {'✅' if v in html else '❌'} {k}", file=sys.stderr)
