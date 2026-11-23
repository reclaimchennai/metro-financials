"""
Download the reports listed in data/sources.json into reports/<operator>/ (not kept in git: about
3.4 GB). Files already there are skipped. Some operator sites refuse automated requests or are
slow; failures are listed at the end.

usage: python3 scripts/download.py [OPERATOR ...]
"""
import json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'Mozilla/5.0 (metro-financials; github.com/reclaimchennai/metro-financials)'}
want = set(sys.argv[1:])
failed = []
for r in json.load(open(os.path.join(ROOT, 'data', 'sources.json'))):
    if want and r['metro_id'] not in want:
        continue
    out = os.path.join(ROOT, 'reports', r['metro_id'], r['filename'])
    if os.path.exists(out) and os.path.getsize(out) > 1024:
        continue
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        with urllib.request.urlopen(urllib.request.Request(r['url'], headers=UA), timeout=300) as resp, open(out + '.part', 'wb') as fh:
            while chunk := resp.read(1 << 16):
                fh.write(chunk)
        os.replace(out + '.part', out)
        print('ok  ', r['filename'], flush=True)
    except Exception as e:
        failed.append((r['filename'], r['url'], str(e)))
        print('FAIL', r['filename'], e, flush=True)
print(f'{len(failed)} failed')
for f in failed:
    print(' ', *f)
