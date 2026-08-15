"""Tab 5: Account View — priority accounts with connections and gaps"""
import json

def fmt_money(val):
    if not val or val == 0: return "$0"
    if val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if val >= 1_000: return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"

def generate_tab5(accounts_data):
    accounts = accounts_data.get('accounts', [])
    if not accounts:
        return '<p>No account data loaded.</p>'

    h = []
    h.append('<div class="info-box">Priority wholesaler accounts with their vendor connections and buying patterns. Click an account to see their vendors and identify gaps. Start with accounts that have low online % — that\'s where the opportunity is.</div>')

    # Search
    h.append('<input type="text" id="account-search" class="search-box" placeholder="Search account name..." style="margin-bottom:1rem;">')

    h.append(f'<p style="font-size:.85rem;color:var(--ink-3);margin-bottom:.75rem;">{len(accounts)} Core wholesaler accounts. Sorted by total buy volume.</p>')

    for a in accounts:
        name = a['name']
        buy = a.get('buy', 0)
        online = a.get('online', 0)
        online_pct = a.get('online_pct', 0)
        state = a.get('state', '')
        system = a.get('system', '')
        vendors = a.get('vendors', [])
        vendor_count = a.get('vendor_count', 0)
        varieties = a.get('varieties', 0)
        categories = a.get('categories', 0)

        # Online % color
        if online_pct > 10:
            online_color = '#059669'
            online_label = 'Active online'
        elif online_pct > 0:
            online_color = '#B45309'
            online_label = 'Minimal online'
        else:
            online_color = '#E11D48'
            online_label = 'Offline only'

        search_text = f"{name} {state}".lower().replace('"', '')

        h.append(f'<details class="account-row" data-search="{search_text}" style="margin-bottom:.35rem;">')

        # Summary
        h.append(f'<summary style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;padding:.55rem .75rem;">')
        h.append(f'<span style="flex:1;min-width:200px;"><b>{name}</b>')
        if state:
            h.append(f' <span style="font-size:.7rem;color:var(--ink-3);">({state})</span>')
        h.append('</span>')
        h.append(f'<span style="font-size:.8rem;font-weight:600;">{fmt_money(buy)}</span>')
        h.append(f'<span style="font-size:.75rem;color:{online_color};font-weight:600;">{online_pct:.1f}% online</span>')
        h.append(f'<span style="font-size:.75rem;color:var(--ink-3);">{vendor_count} vendors</span>')
        h.append(f'<span style="font-size:.75rem;color:var(--ink-3);">{varieties:,} var</span>')
        h.append('</summary>')

        # Expand
        h.append('<div style="padding:.75rem 1rem;border-top:1px solid var(--line);background:var(--surface);">')

        # Account summary
        h.append('<div style="display:flex;gap:1rem 2rem;flex-wrap:wrap;font-size:.8rem;color:var(--ink-2);margin-bottom:.75rem;">')
        h.append(f'<span><b>Total buy (H1 2026):</b> {fmt_money(buy)}</span>')
        h.append(f'<span><b>Online:</b> {fmt_money(online)} ({online_pct:.1f}%)</span>')
        h.append(f'<span><b>Offline:</b> {fmt_money(buy - online)}</span>')
        h.append(f'<span><b>System:</b> {system}</span>')
        h.append(f'<span><b>Varieties bought:</b> {varieties:,}</span>')
        h.append(f'<span><b>Categories:</b> {categories}</span>')
        h.append('</div>')

        # Opportunity callout
        if online_pct < 5 and buy > 1_000_000:
            offline_val = buy - online
            h.append(f'<div style="background:#FEF3C7;border-radius:6px;padding:.5rem .75rem;font-size:.8rem;color:#92400E;margin-bottom:.75rem;">')
            h.append(f'<b>Opportunity:</b> {fmt_money(offline_val)} in offline buying. If 10% moves online = {fmt_money(offline_val * 0.1)} incremental.')
            h.append('</div>')

        # Vendor connections
        if vendors:
            active_vendors = [v for v in vendors if v.get('buy_h1', 0) > 0]
            inactive_vendors = [v for v in vendors if v.get('buy_h1', 0) == 0]

            if active_vendors:
                h.append(f'<h3 style="font-size:.8rem;margin:0 0 .4rem;">Active vendor connections ({len(active_vendors)} buying)</h3>')
                h.append('<div class="tablewrap"><table class="sub-table"><thead><tr>')
                h.append('<th>Vendor</th><th>Buy H1 ($)</th><th>Categories</th>')
                h.append('</tr></thead><tbody>')
                for v in active_vendors[:10]:
                    h.append(f'<tr><td><b>{v["vendor"]}</b></td>')
                    h.append(f'<td class="num">{fmt_money(v["buy_h1"])}</td>')
                    h.append(f'<td class="num">{v["categories"]}</td></tr>')
                h.append('</tbody></table></div>')

            if inactive_vendors:
                h.append(f'<details style="margin-top:.5rem;border:1px dashed var(--line);">')
                h.append(f'<summary style="font-size:.75rem;color:var(--ink-3);padding:.4rem .75rem;">Inactive connections ({len(inactive_vendors)} connected, $0 purchased)</summary>')
                h.append('<div style="padding:.4rem .75rem;font-size:.75rem;color:var(--ink-3);">')
                inactive_names = [v['vendor'] for v in inactive_vendors[:10]]
                h.append(', '.join(inactive_names))
                if len(inactive_vendors) > 10:
                    h.append(f' + {len(inactive_vendors)-10} more')
                h.append('</div></details>')
        else:
            h.append('<p style="font-size:.8rem;color:var(--ink-3);">No vendor connection data available for this account.</p>')

        h.append('</div></details>')

    # JS for search
    h.append("""<script>
(function(){
  var s=document.getElementById('account-search');
  if(s)s.addEventListener('input',function(e){
    var q=e.target.value.toLowerCase();
    document.querySelectorAll('.account-row').forEach(function(r){
      r.style.display=(q===''||r.dataset.search.indexOf(q)>=0)?'':'none';
    });
  });
})();
</script>""")

    return '\n'.join(h)

if __name__ == '__main__':
    with open('/Users/facu/Koronet_OS/ops/data/accounts_priority.json') as f:
        data = json.load(f)
    html = generate_tab5(data)
    import sys
    print(f"Generated Tab 5: {len(data['accounts'])} accounts, {len(html)} chars", file=sys.stderr)
