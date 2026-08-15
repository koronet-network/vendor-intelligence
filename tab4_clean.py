"""Tab 4: Seasonality — real data from procurement by month × category"""
import json

def fmt_money(val):
    if not val or val == 0: return "$0"
    if val >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if val >= 1_000: return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"

def generate_tab4(seasonality_data):
    zones = seasonality_data.get('zones', {})
    if not zones:
        return '<p>No seasonality data loaded.</p>'

    h = []
    h.append('<div class="info-box">Monthly demand by category from the last 24 months of wholesaler procurement. Helps CS reps anticipate what their wholesalers will need and when to source forward.</div>')

    # Combine all zones into one view (since zone breakdown was mostly "Other")
    all_months = set()
    all_cats = set()
    combined = {}
    for zone, cats in zones.items():
        for cat, months in cats.items():
            all_cats.add(cat)
            if cat not in combined:
                combined[cat] = {}
            for month, sold in months.items():
                all_months.add(month)
                combined[cat][month] = combined[cat].get(month, 0) + sold

    sorted_months = sorted(all_months)[-12:]  # last 12 months
    # Sort categories by total volume
    cat_totals = {cat: sum(months.values()) for cat, months in combined.items()}
    sorted_cats = sorted(all_cats, key=lambda c: -cat_totals.get(c, 0))[:15]

    # Compute monthly index per category (month value / avg monthly value)
    h.append('<h2 style="margin-bottom:.5rem;">Demand by Month (last 12 months)</h2>')
    h.append('<p style="font-size:.8rem;color:var(--ink-3);margin-bottom:1rem;">Darker = higher demand. Use this to anticipate when your wholesaler will need specific categories.</p>')

    # Heatmap table
    h.append('<div class="tablewrap"><table style="text-align:center;">')
    h.append('<thead><tr><th style="text-align:left;">Category</th>')
    for m in sorted_months:
        month_label = m[5:7]  # just the month number
        month_names = {'01':'Jan','02':'Feb','03':'Mar','04':'Apr','05':'May','06':'Jun',
                      '07':'Jul','08':'Aug','09':'Sep','10':'Oct','11':'Nov','12':'Dec'}
        h.append(f'<th>{month_names.get(month_label, month_label)}</th>')
    h.append('<th>Total</th></tr></thead><tbody>')

    for cat in sorted_cats:
        months = combined.get(cat, {})
        values = [months.get(m, 0) for m in sorted_months]
        avg = sum(values) / len(values) if values else 1
        total = sum(values)

        h.append(f'<tr><td style="text-align:left;"><b>{cat}</b></td>')
        for val in values:
            if avg > 0:
                index = val / avg
                if index > 1.5:
                    bg, fg = '#0F766E', 'white'  # peak
                elif index > 1.1:
                    bg, fg = '#14B8A6', 'white'  # high
                elif index > 0.7:
                    bg, fg = '#CCFBF1', '#0B5F58'  # normal
                elif index > 0:
                    bg, fg = '#F7FAF9', '#6B7A78'  # low
                else:
                    bg, fg = 'var(--surface)', 'var(--ink-3)'  # zero
            else:
                bg, fg = 'var(--surface)', 'var(--ink-3)'

            h.append(f'<td style="background:{bg};color:{fg};font-size:.7rem;font-weight:600;">{fmt_money(val)}</td>')
        h.append(f'<td class="num" style="font-weight:700;">{fmt_money(total)}</td>')
        h.append('</tr>')

    h.append('</tbody></table></div>')

    # Key events
    h.append('<h3 style="margin-top:1.5rem;">Key events that drive demand</h3>')
    h.append('<div class="tablewrap"><table><thead><tr><th>When</th><th>Event</th><th>Categories impacted</th><th>Start sourcing</th></tr></thead><tbody>')
    events = [
        ('Feb 14', "Valentine's Day", 'Rose (peak), Carnation, Tulip', '4 weeks ahead (mid-Jan)'),
        ('May (2nd Sun)', "Mother's Day", 'Rose, Carnation, Hydrangea, Peony', '3-4 weeks ahead (mid-Apr)'),
        ('May-Oct', 'Wedding season', 'Peony, Ranunculus, Hydrangea, Lisianthus', 'March-April for peak'),
        ('Nov-Dec', 'Holiday season', 'Greens, Rose, Carnation, Poms/Mums', 'October-November'),
    ]
    for when, event, cats, sourcing in events:
        h.append(f'<tr><td><b>{when}</b></td><td>{event}</td><td>{cats}</td><td>{sourcing}</td></tr>')
    h.append('</tbody></table></div>')

    h.append('<div class="info-box" style="margin-top:1rem;"><b>Coming in v2:</b> Zone-level breakdown (Northeast, Southeast, Midwest, Southwest, West) once buyer state data coverage improves.</div>')

    return '\n'.join(h)

if __name__ == '__main__':
    with open('/Users/facu/Koronet_OS/ops/data/seasonality.json') as f:
        data = json.load(f)
    html = generate_tab4(data)
    import sys
    print(f"Generated Tab 4: {len(html)} chars", file=sys.stderr)
