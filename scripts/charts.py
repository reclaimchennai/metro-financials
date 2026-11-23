"""
Charts for the README, drawn as plain SVG from data/finance.json (no plotting library needed):
docs/charts/*.svg. Run after scripts/build.py.

usage: python3 scripts/charts.py
"""
import json, os
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'docs', 'charts')
os.makedirs(OUT, exist_ok=True)
D = json.load(open(os.path.join(ROOT, 'data', 'finance.json')))
OPS = {o['id']: o for o in D['operators']}

# reference categorical palette (validated: scripts in the dataviz kit), chrome and ink
SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
SURFACE, INK, INK2, MUTED, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#898781', '#e7e6e2'
FONT = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
FY = '2024-25'
SOURCE = 'Source: audited statements of profit and loss in each operator\'s annual reports · github.com/reclaimchennai/metro-financials · metro.reclaim.city/db'


def has(y):
    return y['values'].get('total_income') is not None and y['values'].get('total_expenses') is not None


def year(op, fy):
    return next((y for y in OPS[op]['years'] if y['fy'] == fy and has(y)), None)


def fmt(n, d=0):
    s = f'{abs(n):,.{d}f}'
    return ('−' if n < 0 else '') + s


def svg(w, h, title, sub, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">'
            f'<rect width="{w}" height="{h}" fill="{SURFACE}"/>'
            f'<text x="24" y="34" font-size="19" font-weight="700" fill="{INK}">{escape(title)}</text>'
            f'<text x="24" y="56" font-size="13" fill="{INK2}">{escape(sub)}</text>'
            f'{body}<text x="24" y="{h - 14}" font-size="10.5" fill="{MUTED}">{escape(SOURCE)}</text></svg>')


def nice(v):
    p = 10 ** len(str(int(max(1, v)))) / 10
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if v <= m * p:
            return m * p
    return 10 * p


def legend(x, y, items):
    out, cx = '', x
    for label, color in items:
        out += f'<rect x="{cx}" y="{y - 9}" width="11" height="11" rx="2" fill="{color}"/><text x="{cx + 16}" y="{y}" font-size="12" fill="{INK2}">{escape(label)}</text>'
        cx += 16 + len(label) * 7.6 + 18
    return out


def write(name, s):
    open(os.path.join(OUT, name), 'w').write(s)
    print('docs/charts/' + name)


# 1. fare-box recovery, one year
def farebox():
    rows = [(o['id'], o['runs'], y['values']['farebox_recovery']) for o in D['operators'] if (y := year(o['id'], FY)) and y['values'].get('farebox_recovery')]
    rows.sort(key=lambda r: -r[2])
    W, L, R, top, rh = 900, 250, 70, 84, 30
    H = top + len(rows) * rh + 60
    mx = nice(max(r[2] for r in rows))
    x = lambda v: L + (W - L - R) * v / mx
    b = ''
    for t in range(0, int(mx) + 1, 50):
        b += f'<line x1="{x(t)}" x2="{x(t)}" y1="{top - 8}" y2="{top + len(rows) * rh}" stroke="{GRID}"/><text x="{x(t)}" y="{top + len(rows) * rh + 16}" font-size="11" fill="{MUTED}" text-anchor="middle">{t}%</text>'
    b += f'<line x1="{x(100)}" x2="{x(100)}" y1="{top - 14}" y2="{top + len(rows) * rh}" stroke="{INK2}" stroke-dasharray="4 3"/><text x="{x(100) + 4}" y="{top - 16}" font-size="11" fill="{INK2}">fares = running costs</text>'
    for i, (op, runs, v) in enumerate(rows):
        yy = top + i * rh
        b += (f'<text x="{L - 10}" y="{yy + 16}" font-size="12.5" fill="{INK}" text-anchor="end">{escape(runs.replace(" (PPP)", ""))} <tspan fill="{MUTED}">{op}</tspan></text>'
              f'<rect x="{L}" y="{yy + 5}" width="{x(v) - L}" height="16" rx="3" fill="{SERIES[0]}"/>'
              f'<text x="{x(v) + 6}" y="{yy + 17}" font-size="12" fill="{INK}">{v:.0f}%</text>')
    write('farebox-recovery.svg', svg(W, H, f'How much of the running cost fares paid for, {FY}', 'Fare revenue ÷ operating cost (total expenses less depreciation and interest)', b))


# 2. fares and running costs, ₹ crore, one year
def fares_costs():
    rows = [(o['id'], y['values']) for o in D['operators'] if (y := year(o['id'], FY)) and (y['values'].get('revenue_from_operations') or 0) > 0]
    rows.sort(key=lambda r: -(r[1]['operating_cost'] or 0))
    W, L, R, top, rh = 900, 110, 90, 96, 36
    H = top + len(rows) * rh + 60
    mx = nice(max(max(v['operating_cost'] or 0, v['fare_revenue'] or 0) for _, v in rows))
    x = lambda v: L + (W - L - R) * v / mx
    b = legend(24, 80, [('Running cost', SERIES[1]), ('Fare revenue', SERIES[0])])
    step = mx / 5
    for k in range(6):
        t = step * k
        b += f'<line x1="{x(t)}" x2="{x(t)}" y1="{top - 4}" y2="{top + len(rows) * rh}" stroke="{GRID}"/><text x="{x(t)}" y="{top + len(rows) * rh + 16}" font-size="11" fill="{MUTED}" text-anchor="middle">{fmt(t)}</text>'
    for i, (op, v) in enumerate(rows):
        yy = top + i * rh
        oc, fr = v['operating_cost'] or 0, v['fare_revenue']
        b += (f'<text x="{L - 10}" y="{yy + 20}" font-size="12.5" fill="{INK}" text-anchor="end">{op}</text>'
              f'<rect x="{L}" y="{yy + 3}" width="{max(1, x(oc) - L)}" height="13" rx="3" fill="{SERIES[1]}"/>'
              f'<text x="{x(oc) + 6}" y="{yy + 14}" font-size="11" fill="{INK2}">₹{fmt(oc)} cr</text>')
        if fr:
            b += (f'<rect x="{L}" y="{yy + 18}" width="{max(1, x(fr) - L)}" height="13" rx="3" fill="{SERIES[0]}"/>'
                  f'<text x="{x(fr) + 6}" y="{yy + 29}" font-size="11" fill="{INK2}">₹{fmt(fr)} cr</text>')
    write('fares-and-running-costs.svg', svg(W, H, f'Fares and running costs, {FY}', '₹ crore. Delhi\'s costs include work for other agencies (deposit works, consultancy).', b))


# 3, 4. year by year for the six largest operators
LINES = ['DMRC', 'BMRCL', 'LTMRHL', 'CMRL', 'MAHAMETRO', 'KMRL']


def trend(field, name, title, sub):
    W, L, R, top, bottom = 900, 70, 110, 96, 50
    H = 430
    pts = {op: [(int(y['fy'][:4]) + 1, y['values'][field]) for y in OPS[op]['years'] if has(y) and y['values'].get(field) is not None and int(y['fy'][:4]) >= 2013] for op in LINES}
    allv = [v for s in pts.values() for _, v in s]
    lo, hi = min(0, min(allv)), max(0, max(allv))
    raw = (hi - lo) / 6
    p = 10 ** (len(str(int(raw))) - 1)
    step = next(m * p for m in (1, 2, 2.5, 5, 10) if m * p >= raw)
    import math
    t0, t1 = math.floor(lo / step) * step, math.ceil(hi / step) * step
    x0, x1 = 2014, 2026
    X = lambda yr: L + (W - L - R) * (yr - x0) / (x1 - x0)
    Y = lambda v: top + (H - top - bottom) * (t1 - v) / (t1 - t0)
    b = legend(24, 80, [(op, SERIES[i]) for i, op in enumerate(LINES)])
    t = t0
    while t <= t1 + 1e-9:
        b += f'<line x1="{L}" x2="{W - R}" y1="{Y(t)}" y2="{Y(t)}" stroke="{INK2 if t == 0 else GRID}" stroke-width="{1.2 if t == 0 else 1}"/><text x="{L - 8}" y="{Y(t) + 4}" font-size="11" fill="{MUTED}" text-anchor="end">{fmt(t)}</text>'
        t += step
    for yr in range(x0, x1 + 1, 2):
        b += f'<text x="{X(yr)}" y="{H - bottom + 18}" font-size="11" fill="{MUTED}" text-anchor="middle">{yr - 1}-{str(yr)[2:]}</text>'
    ends = []
    for i, op in enumerate(LINES):
        s = [(yr, v) for yr, v in pts[op] if yr >= x0]
        if not s:
            continue
        d = ' '.join(f'{"M" if k == 0 else "L"}{X(yr):.1f} {Y(v):.1f}' for k, (yr, v) in enumerate(s))
        b += f'<path d="{d}" fill="none" stroke="{SERIES[i]}" stroke-width="2" stroke-linejoin="round"/>'
        b += ''.join(f'<circle cx="{X(yr):.1f}" cy="{Y(v):.1f}" r="3" fill="{SERIES[i]}" stroke="{SURFACE}" stroke-width="1.5"/>' for yr, v in s)
        ends.append([Y(s[-1][1]), X(s[-1][0]), op])
    ends.sort()
    for k in range(1, len(ends)):
        if ends[k][0] - ends[k - 1][0] < 13:
            ends[k][0] = ends[k - 1][0] + 13
    # labels pushed past the plot's foot move back up, keeping their spacing
    if ends:
        ends[-1][0] = min(ends[-1][0], H - bottom - 4)
        for k in range(len(ends) - 2, -1, -1):
            ends[k][0] = min(ends[k][0], ends[k + 1][0] - 13)
    for yy, xx, op in ends:
        b += f'<text x="{xx + 8}" y="{yy + 4}" font-size="11.5" font-weight="600" fill="{INK}">{op}</text>'
    write(name, svg(W, H, title, sub, b))


# 5. where the money comes from, shares, one year
def stacked(name, title, sub, parts):
    rows = []
    for o in D['operators']:
        y = year(o['id'], FY)
        if not y:
            continue
        vals = [max(0, f(y['values']) or 0) for _, f in parts]
        if sum(vals) > 0 and (y['values'].get('revenue_from_operations') or 0) > 0:
            rows.append((o['id'], vals))
    rows.sort(key=lambda r: -r[1][0] / sum(r[1]))
    W, L, R, top, rh = 900, 110, 80, 96, 28
    H = top + len(rows) * rh + 60
    x = lambda v: L + (W - L - R) * v / 100
    b = legend(24, 80, [(lbl, SERIES[i]) for i, (lbl, _) in enumerate(parts)])
    for t in range(0, 101, 25):
        b += f'<text x="{x(t)}" y="{top + len(rows) * rh + 16}" font-size="11" fill="{MUTED}" text-anchor="middle">{t}%</text>'
    for i, (op, vals) in enumerate(rows):
        yy, tot, acc = top + i * rh, sum(vals), 0
        b += f'<text x="{L - 10}" y="{yy + 15}" font-size="12.5" fill="{INK}" text-anchor="end">{op}</text>'
        for k, v in enumerate(vals):
            a, c = acc / tot * 100, (acc + v) / tot * 100
            acc += v
            if c - a > 0:
                b += f'<rect x="{x(a):.1f}" y="{yy + 4}" width="{max(0, x(c) - x(a) - 2):.1f}" height="16" fill="{SERIES[k]}"/>'
                if c - a >= 9:
                    b += f'<text x="{(x(a) + x(c)) / 2:.1f}" y="{yy + 16}" font-size="10.5" fill="{"#0b0b0b" if SERIES[k] in ("#eda100", "#1baf7a", "#e87ba4") else "#ffffff"}" text-anchor="middle">{c - a:.0f}%</text>'
        b += f'<text x="{x(100) + 6}" y="{yy + 16}" font-size="11" fill="{INK2}">₹{fmt(tot)} cr</text>'
    write(name, svg(W, H, title, sub, b))


farebox()
fares_costs()
trend('fare_revenue', 'fare-revenue-by-year.svg', 'Fare revenue, year by year', '₹ crore, six largest operators by fares. Financial years April to March.')
trend('profit_after_tax', 'profit-after-tax-by-year.svg', 'Profit or loss after tax, year by year', '₹ crore, same six operators. Below the line is a loss.')
stacked('where-money-comes-from.svg', f'Where the money comes from, {FY}', 'Share of total income. Other income is mostly government grants released to the accounts, and interest.',
        [('Fares', lambda v: v.get('fare_revenue')), ('Other operating revenue', lambda v: (v.get('revenue_from_operations') or 0) - (v.get('fare_revenue') or 0)), ('Other income', lambda v: v.get('other_income'))])
stacked('where-money-goes.svg', f'Where the money goes, {FY}', 'Share of costs before tax: running the railway and the company, depreciation, interest on loans.',
        [('Running costs', lambda v: v.get('operating_cost')), ('Depreciation', lambda v: v.get('depreciation')), ('Interest', lambda v: v.get('finance_cost'))])
