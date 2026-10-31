import sys, bisect
log, rssf = sys.argv[1], sys.argv[2]
probes = [l.split()[2:] for l in open(log, errors='replace') if l.startswith('js: memprobe')]
rss = [tuple(map(int, l.split())) for l in open(rssf) if l.strip()]
ts = [t for t, _ in rss]
phase = {}
for clk, fr, mode, pix, voices in probes:
    i = min(bisect.bisect_left(ts, int(clk)), len(rss) - 1)
    m = rss[i][1] // 1024
    a = phase.setdefault(mode, [m, m, int(fr), int(fr), float(pix), float(pix)])
    a[0] = min(a[0], m); a[1] = max(a[1], m); a[3] = int(fr); a[4] = min(a[4], float(pix)); a[5] = max(a[5], float(pix))
print(f'  {"man":24} {"khung":>11}  {"RSS MB":>9}  {"anh dang giu MB":>15}')
for mode, (lo, hi, f0, f1, plo, phi) in phase.items(): print(f'  {mode:24} {f0:5}-{f1:5}  {lo:4}-{hi:4}  {plo:7.1f}-{phi:6.1f}')
print('  dinh RSS:', max(r for _, r in rss) // 1024, 'MB; giong da doc:', probes[-1][4] if probes else '?')
for l in open(log, errors='replace'):
    if 'error' in l.lower() or 'too many' in l or 'missing' in l: print('  LOG:', l.rstrip()[:160])
