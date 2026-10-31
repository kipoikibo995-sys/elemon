"""Which files of a new build differ from a copy of the game pulled off the TrimUI Brick (adb pull), so only those are
pushed: python adb_diff.py <new build elemon dir> <pulled Apps/Elemon dir> -> adb-diff.json {push: [...], rm: [...]}.
The Brick's own files (launcher, icon, config, buttons, log) are never pushed nor removed."""
import hashlib, json, os, sys

KEEP = {'buttons.txt', 'log.txt', 'config.json', 'icon.png', 'launch.sh'}


def files(root):
    return {os.path.relpath(os.path.join(d, f), root).replace(os.sep, '/') for d, _, fs in os.walk(root) for f in fs}


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


new, old = sys.argv[1], sys.argv[2]
n, o = files(new), files(old)
push = [f for f in sorted(n) if f not in KEEP and (f not in o or os.path.getsize(f'{new}/{f}') != os.path.getsize(f'{old}/{f}')
                                                  or md5(f'{new}/{f}') != md5(f'{old}/{f}'))]
rm = [f for f in sorted(o - n) if f not in KEEP]
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'adb-diff.json')
json.dump({'push': push, 'rm': rm}, open(out, 'w', encoding='utf-8'), indent=0)
print('push', len(push), 'files', sum(os.path.getsize(f'{new}/{f}') for f in push), 'bytes; rm', len(rm))
for f in push[:40]:
    print('  +', f)
for f in rm[:20]:
    print('  -', f)
