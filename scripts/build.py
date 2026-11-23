"""
Build the combined dataset and the analysis from the per-operator files.

  data/verified/<OP>.json  (every figure with its report, page and the line as printed)
  data/sources.json        (every report: operator, year, original URL, file name)
→ data/finance.json        (one entry per operator-year, ₹ crore, with sources and restatements)
→ data/finance.csv         (the same, flat)
→ ANALYSIS.md              (tables computed from the data)

A year's figures come from that year's own report; where it is missing, from the next report's
previous-year column. A later report's restated figure is kept beside it (`restated`). Nothing is
estimated: a value the reports do not give stays empty. Derived values are arithmetic on audited
lines: operating cost = total expenses − depreciation − finance cost; operating ratio = operating
cost / revenue from operations; fare-box recovery = fare revenue / operating cost.

usage: python3 scripts/build.py
"""
import csv, json, os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ROOT, *p)

# operator → name, what it runs, the cities (app ids)
OPERATORS = {
    'DMRC': ('Delhi Metro Rail Corporation', 'Delhi Metro', ['delhi']),
    'NMRC': ('Noida Metro Rail Corporation', 'Aqua Line, Noida', ['delhi']),
    'RMGL': ('Rapid MetroRail Gurgaon', 'Rapid Metro Gurugram, phase 1 (PPP)', ['delhi']),
    'RMGSL': ('Rapid MetroRail Gurgaon South', 'Rapid Metro Gurugram, phase 2 (PPP)', ['delhi']),
    'NCRTC': ('National Capital Region Transport Corporation', 'Namo Bharat and Meerut Metro', ['delhi', 'meerut']),
    'BMRCL': ('Bangalore Metro Rail Corporation', 'Namma Metro', ['bengaluru']),
    'CMRL': ('Chennai Metro Rail', 'Chennai Metro', ['chennai']),
    'LTMRHL': ('L&T Metro Rail (Hyderabad)', 'Hyderabad Metro (PPP)', ['hyderabad']),
    'MMOPL': ('Mumbai Metro One', 'Mumbai Line 1 (PPP)', ['mumbai']),
    'MMRCL': ('Mumbai Metro Rail Corporation', 'Mumbai Line 3', ['mumbai']),
    'MMMOCL': ('Maha Mumbai Metro Operation Corporation', 'Mumbai Lines 2A and 7', ['mumbai']),
    'MAHAMETRO': ('Maharashtra Metro Rail Corporation', 'Pune and Nagpur Metro', ['pune', 'nagpur']),
    'GMRC': ('Gujarat Metro Rail Corporation', 'Ahmedabad and Surat Metro', ['ahmedabad', 'surat']),
    'KMRL': ('Kochi Metro Rail', 'Kochi Metro', ['kochi']),
    'JMRC': ('Jaipur Metro Rail Corporation', 'Jaipur Metro', ['jaipur']),
    'KMRCL': ('Kolkata Metro Rail Corporation', 'Kolkata East-West Metro (construction company)', ['kolkata']),
    'UPMRC': ('Uttar Pradesh Metro Rail Corporation', 'Lucknow, Kanpur and Agra Metro', ['lucknow', 'kanpur', 'agra']),
    'MPMRCL': ('Madhya Pradesh Metro Rail Corporation', 'Bhopal and Indore Metro', ['bhopal', 'indore']),
}
FIELDS = ['revenue_from_operations', 'fare_revenue', 'non_fare_revenue', 'other_income', 'total_income', 'employee_cost', 'operating_expenses',
          'finance_cost', 'depreciation', 'other_expenses', 'total_expenses', 'exceptional_items', 'profit_before_tax', 'tax',
          'profit_after_tax', 'annual_ridership_lakh', 'avg_daily_ridership', 'route_km']
NON_CR = {'annual_ridership_lakh', 'avg_daily_ridership', 'route_km'}
DERIVED = ['operating_cost', 'operating_ratio', 'farebox_recovery']

sources = json.load(open(D('data', 'sources.json')))
url_of = {r['filename']: r.get('url') for r in sources}


def val(entry, f):
    v = entry.get(f)
    if not isinstance(v, dict):
        return None
    x = v.get('value') if 'value' in v else v.get('cr')
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def src(entry, f):
    v = entry.get(f) or {}
    file = v.get('file') or entry.get('source_file')
    return {'file': file, 'page': v.get('page'), 'quote': v.get('quote'), 'url': url_of.get(file)}


def build():
    out = []
    for op, (name, runs, cities) in OPERATORS.items():
        path = D('data', 'verified', f'{op}.json')
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        # a file that is not what its name says (e.g. special-purpose statements made for a parent's consolidation) is used last
        bad = {doc.get('file') for doc in d.get('documents', []) if doc.get('is_what_it_says') is False}
        by_fy = {}
        for e in sorted(d.get('years', []), key=lambda e: e.get('source_file') in bad):
            by_fy.setdefault(e['fy'], []).append(e)
        years = []
        for fy in sorted(by_fy):
            if ' ' in fy:  # part years (H1) are not years
                continue
            es = by_fy[fy]
            own = [e for e in es if e.get('column') == 'current' and e.get('source_file') not in bad]
            later = [e for e in es if e.get('column') == 'previous']
            primary = (own or later or es)[0]
            row = {'fy': fy, 'from': 'own report' if own else "next year's report (previous-year column)", 'values': {}, 'sources': {}, 'restated': {}}
            for f in FIELDS:
                v, used = val(primary, f), primary
                if v is None:
                    alt = next((e for e in es if e is not primary and val(e, f) is not None), None)
                    if alt:
                        v, used = val(alt, f), alt
                row['values'][f] = v
                if v is not None:
                    row['sources'][f] = src(used, f)
                    for e in later:
                        rv = val(e, f)
                        if e is not used and rv is not None and abs(rv - v) > 0.5:
                            row['restated'][f] = {'value': rv, **src(e, f)}
            v = row['values']
            oc = round(v['total_expenses'] - (v.get('depreciation') or 0) - (v.get('finance_cost') or 0), 2) if v.get('total_expenses') is not None else None
            v['operating_cost'] = oc
            rfo, fare = v.get('revenue_from_operations'), v.get('fare_revenue')
            v['operating_ratio'] = round(oc / rfo * 100, 1) if oc and rfo else None
            v['farebox_recovery'] = round(fare / oc * 100, 1) if oc and fare else None
            row['notes'] = ' | '.join(x for x in dict.fromkeys(e.get('notes') or '' for e in es) if x)
            years.append(row)
        out.append({'id': op, 'name': name, 'runs': runs, 'cities': cities, 'documents': d.get('documents', []), 'years': years})
    return out


def write(ops):
    json.dump({'generated': date.today().isoformat(), 'unit': '₹ crore', 'operators': ops}, open(D('data', 'finance.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    with open(D('data', 'finance.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['operator', 'runs', 'financial_year', 'from', *FIELDS, *DERIVED, 'restated_fields', 'notes'])
        for o in ops:
            for y in o['years']:
                w.writerow([o['id'], o['runs'], y['fy'], y['from'], *[y['values'].get(f) for f in FIELDS + DERIVED], ';'.join(y['restated']), y['notes']])


# ---------- analysis ----------
def has(y):
    return y['values'].get('total_income') is not None and y['values'].get('total_expenses') is not None


def cr(n):
    if n is None:
        return '—'
    return f"{'−' if n < 0 else ''}{abs(n):,.0f}" if abs(n) >= 10 else f"{'−' if n < 0 else ''}{abs(n):,.1f}"


def pc(n):
    return '—' if n is None else f'{n:,.0f}%'


def analysis(ops):
    L = []
    P = L.append
    acct = [o for o in ops if any(has(y) for y in o['years'])]
    P('# Indian metro finances: the numbers\n')
    P(f'Generated {date.today().isoformat()} from `data/finance.json`. All money in ₹ crore; financial years run April to March. '
      'Every figure is from an audited standalone statement of profit and loss, or arithmetic on one (see METHOD.md). '
      '"—" means the reports do not give it.\n')

    P('## Coverage\n')
    P('| Operator | Runs | Years with accounts | Fare split from |')
    P('|---|---|---|---|')
    for o in ops:
        ys = [y['fy'] for y in o['years'] if has(y)]
        fs = [y['fy'] for y in o['years'] if y['values'].get('fare_revenue') is not None]
        P(f"| {o['id']} | {o['runs']} | {len(ys)} ({ys[0]} to {ys[-1]}) | {fs[0] if fs else '—'} |" if ys else f"| {o['id']} | {o['runs']} | none (turnover only) | — |")
    P('')

    FY = '2024-25'
    rows = [(o, next((y for y in o['years'] if y['fy'] == FY and has(y)), None)) for o in acct]
    rows = [(o, y) for o, y in rows if y]
    P(f'## {FY}, operator by operator\n')
    P('| Operator | Fares | Revenue from operations | Other income | Operating cost | Depreciation | Interest | Profit after tax | Fare-box recovery | Operating ratio |')
    P('|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|')
    tot = {k: 0.0 for k in ('fare_revenue', 'revenue_from_operations', 'other_income', 'operating_cost', 'depreciation', 'finance_cost', 'profit_after_tax')}
    for o, y in sorted(rows, key=lambda r: -(r[1]['values'].get('revenue_from_operations') or 0)):
        v = y['values']
        for k in tot:
            tot[k] += v.get(k) or 0
        P(f"| {o['id']} | {cr(v.get('fare_revenue'))} | {cr(v.get('revenue_from_operations'))} | {cr(v.get('other_income'))} | {cr(v.get('operating_cost'))} | "
          f"{cr(v.get('depreciation'))} | {cr(v.get('finance_cost'))} | {cr(v.get('profit_after_tax'))} | {pc(v.get('farebox_recovery'))} | {pc(v.get('operating_ratio'))} |")
    P(f"| **All {len(rows)}** | {cr(tot['fare_revenue'])} | {cr(tot['revenue_from_operations'])} | {cr(tot['other_income'])} | {cr(tot['operating_cost'])} | "
      f"{cr(tot['depreciation'])} | {cr(tot['finance_cost'])} | {cr(tot['profit_after_tax'])} | {pc(tot['fare_revenue'] / tot['operating_cost'] * 100 if tot['operating_cost'] else None)} | — |")
    P('')
    cover = [(o['id'], y['values']['farebox_recovery']) for o, y in rows if (y['values'].get('farebox_recovery') or 0) >= 100]
    withf = [o for o, y in rows if y['values'].get('farebox_recovery') is not None]
    prof = [o['id'] for o, y in rows if (y['values'].get('profit_after_tax') or 0) > 0]
    P(f"- Fares covered running costs at {len(cover)} of {len(withf)} operators with a fare split: " + (', '.join(f'{i} ({v:.0f}%)' for i, v in cover) or 'none') + '.')
    P(f"- Profit after tax: {len(prof)} of {len(rows)} operators ({', '.join(prof) or 'none'}).")
    P(f"- Depreciation and interest together: ₹{cr(tot['depreciation'] + tot['finance_cost'])} crore, against an operating result "
      f"(revenue from operations − operating cost) of ₹{cr(tot['revenue_from_operations'] - tot['operating_cost'])} crore.\n")

    def series(field, label, fmt=cr, since='2014-15'):
        fys = sorted({y['fy'] for o in acct for y in o['years'] if has(y) and y['fy'] >= since})
        P(f'## {label}, year by year\n')
        P('| Operator | ' + ' | '.join(fys) + ' |')
        P('|---|' + '---:|' * len(fys))
        for o in acct:
            m = {y['fy']: y['values'].get(field) for y in o['years'] if has(y)}
            if any(m.get(f) is not None for f in fys):
                P(f"| {o['id']} | " + ' | '.join(fmt(m.get(f)) for f in fys) + ' |')
        P('')
    series('fare_revenue', 'Fare revenue')
    series('revenue_from_operations', 'Revenue from operations')
    series('operating_cost', 'Operating cost')
    series('farebox_recovery', 'Fare-box recovery', pc)
    series('profit_after_tax', 'Profit or loss after tax')
    series('finance_cost', 'Interest (finance cost)')
    series('depreciation', 'Depreciation')

    P('## Per passenger trip (latest year with accounts and a stated ridership)\n')
    P('| Operator | Year | Riders (lakh) | Fare per trip | Running cost per trip | All costs per trip |')
    P('|---|---|---:|---:|---:|---:|')
    for o in acct:
        for y in sorted(o['years'], key=lambda z: z['fy'], reverse=True):
            v = y['values']
            a, dly = v.get('annual_ridership_lakh'), v.get('avg_daily_ridership')
            riders, est = (a, False) if a else ((dly * 365 / 1e5, True) if dly else (None, False))
            if has(y) and riders and v.get('fare_revenue'):
                n = riders * 1e5
                per = lambda x: '—' if x is None else f'₹{x * 1e7 / n:,.0f}'
                allc = (v.get('operating_cost') or 0) + (v.get('depreciation') or 0) + (v.get('finance_cost') or 0)
                P(f"| {o['id']} | {y['fy']} | {riders:,.1f}{'*' if est else ''} | {per(v.get('fare_revenue'))} | {per(v.get('operating_cost'))} | {per(allc)} |")
                break
    P('\n\\* stated daily average × 365. DMRC counts passenger journeys (each line boarded counts once); the others count trips.\n')

    P('## Restatements\n')
    P('Figures a later report changed. The dataset keeps the year\'s own report; the later figure is in `restated`.\n')
    P('| Operator | Year | Item | Own report | Later report | Restated in |')
    P('|---|---|---|---:|---:|---|')
    for o in ops:
        for y in o['years']:
            for f, r in y['restated'].items():
                P(f"| {o['id']} | {y['fy']} | {f.replace('_', ' ')} | {cr(y['values'].get(f))} | {cr(r['value'])} | {r['file']} |")
    P('')
    P('## Read with care\n')
    P('- DMRC: revenue from operations and expenses include work done for other agencies (deposit works, consultancy, external projects); fare revenue ("traffic earnings") is the like-for-like figure. Up to 2010-11 the accounts are by segment, so employee and other expenses are not shown separately.')
    P('- LTMRHL and Rapid Metro are private (PPP) concessions: their accounts include construction revenue matched by construction cost under service-concession accounting, and LTMRHL\'s revenue from operations includes real-estate income (₹511.73 crore in 2023-24, ₹187.44 crore in 2024-25 from the transfer of a real-estate undertaking).')
    P('- Maha Metro books works for other agencies in revenue from operations with matching costs; grants (such as stamp-duty cess) are in other income.')
    P('- Other income is mostly government grants released to the accounts, and interest. Several operators (CMRL, BMRCL, UPMRC, MMRCL) show large foreign-exchange gains or losses on loans, which move the profit line from year to year.')
    P('- Operators that had not started passenger service (MPMRCL, KMRCL, NCRTC before 2025-26, MMRCL before 2024-25) have no revenue from operations.')
    P('- KMRCL is the company that built the Kolkata East-West Metro; Metro Railway Kolkata (a zone of Indian Railways) runs it and has no separate accounts.\n')
    P('## Not covered\n')
    P('- **Metro Railway Kolkata**: part of Indian Railways; its figures are only in Railway Board publications, which could not be fetched.')
    P('- **Patna Metro**: no published accounts since services began in 2025.')
    P('- **Navi Mumbai Metro**: part of CIDCO\'s accounts, not separated.')
    P('- **Mumbai Line 1 (MMOPL)**: no published accounts after 2021-22 (insolvency proceedings).')
    P('- **Rapid Metro Gurugram**: no published accounts after 2017-18 (taken over in 2019).')
    P('- **Mumbai Lines 2A and 7 (MMMOCL)**: only annual returns with turnover.')
    P('- **Kochi Metro**: 2019-20, 2020-21 and the years before 2017-18 (their reports are on kochimetro.org, which did not respond).')
    open(D('ANALYSIS.md'), 'w').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    ops = build()
    write(ops)
    analysis(ops)
    print(f"{len(ops)} operators, {sum(len(o['years']) for o in ops)} operator-years → data/finance.json, data/finance.csv, ANALYSIS.md")
