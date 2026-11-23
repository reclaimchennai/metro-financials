# Indian metro finances

The audited accounts of India's metro rail operators, year by year, read from their annual
reports: fare and other revenue, running costs, depreciation, interest and profit or loss, with
ridership and route length where the reports state them. Every figure carries the report, page
and line it comes from.

Charts and comparison tools: [metro.reclaimchennai.city/db](https://metro.reclaimchennai.city/db/)
(also metro.reclaim.city/db).

## Files

| File | What |
|---|---|
| `data/verified/<OP>.json` | Every figure read from each report: value, page, the line as printed, unit, checks, restatements |
| `data/finance.json` | One entry per operator and year, ₹ crore, with sources and later restatements |
| `data/finance.csv` | The same, flat |
| `data/sources.json` | Every report used: operator, year, original URL, file name |
| `ANALYSIS.md` | Tables computed from the data: each year by operator, trends, per trip, restatements |
| `METHOD.md` | How the figures were read and checked, and the definitions used |
| `scripts/build.py` | Builds `finance.json`, `finance.csv` and `ANALYSIS.md` from the verified files |
| `scripts/download.py` | Downloads the reports listed in `sources.json` into `reports/` (not in git) |

## Operators

Delhi (DMRC), Noida (NMRC), Rapid Metro Gurugram (RMGL, RMGSL), Namo Bharat (NCRTC), Bengaluru
(BMRCL), Chennai (CMRL), Hyderabad (LTMRHL), Mumbai Line 1 (MMOPL), Mumbai Line 3 (MMRCL),
Mumbai Lines 2A and 7 (MMMOCL, turnover only), Pune and Nagpur (Maha Metro), Ahmedabad and Surat
(GMRC), Kochi (KMRL), Jaipur (JMRC), Kolkata East-West (KMRCL), Lucknow, Kanpur and Agra (UPMRC),
Bhopal and Indore (MPMRCL). Years covered and gaps per operator are in `ANALYSIS.md`.

Not covered: Metro Railway Kolkata (part of Indian Railways, no separate published accounts),
Patna (no published accounts yet) and Navi Mumbai (inside CIDCO's accounts).

## Rebuild

```
python3 scripts/download.py        # optional: the source PDFs
python3 scripts/build.py
```

## Licence

Data: the operators' published annual reports. Compilation and code by
[@reclaimchennai](https://x.com/reclaimchennai), CC BY 4.0.
