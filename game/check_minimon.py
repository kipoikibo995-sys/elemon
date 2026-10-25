"""What MiniMon's demo (scripts/evo_app.html, scripts/build_evo_app.py) changed since the game last took it in
(game/minimon-base.html, saved by build_game.py), so the new behaviour can be merged into game/src/game.js.
Interface pictures need no merging: build_game.py takes them from the demo build every time.
Usage: python game/check_minimon.py          (prints the changed lines of the page, or that nothing changed)
"""
import difflib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    base = os.path.join(HERE, 'minimon-base.html')
    page = os.path.join(ROOT, 'scripts', 'evo_app.html')
    if not os.path.exists(base):
        print('no merged copy yet: run python game/build_game.py')
        return
    a = open(base, encoding='utf-8').read().splitlines()
    b = open(page, encoding='utf-8').read().splitlines()
    diff = list(difflib.unified_diff(a, b, 'merged', 'demo now', n=2, lineterm=''))
    builder = os.path.getmtime(os.path.join(ROOT, 'scripts', 'build_evo_app.py')) > os.path.getmtime(base)
    if not diff:
        print('the demo page is the same as the merged copy' + (' (build_evo_app.py is newer: rebuild the game)' if builder else ''))
        return
    print(f'{sum(1 for l in diff if l[:1] in "+-" and l[:3] not in ("+++", "---"))} changed lines'
          + (' · build_evo_app.py is newer too' if builder else ''))
    print('\n'.join(diff))


if __name__ == '__main__':
    main()
