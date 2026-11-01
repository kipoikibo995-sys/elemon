"""Publishes a version for the in-device update (packaging/trimui-brick/ota.sh): the files of Apps/Elemon as
scripts/pack_brick.py packs them, committed on the "ota" branch of the GitHub repo with ota.txt (the list) at its
root, tagged ota-<version>, and pushed. Devices read ota.txt from the branch head and each file from the tag, through
raw.githubusercontent.com. Git stores only what changed, so a version costs about the size of its changes.

The branch lives in its own checkout beside the project (D:/INDIEGAME/_ota-repo), never in the project's.
Run pack_brick.py with the same version first (it checks the files; this script makes the same list again).

--r36s publishes the R36S build instead (scripts/pack_r36s.py's files): branch ota-r36s, tag ota-r36s-<version>.

Usage: python scripts/push_ota.py v1.1 [--r36s] [--branch ota-test]   (another branch: for trying an update on a device,
       which reads it when its .ota/branch file names it)
"""
import os, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pack_brick, pack_r36s
from pack_brick import manifest, sha, ROOT

REPO_URL = 'https://github.com/kipoikibo995-sys/elemon.git'
WORK = os.path.join(os.path.dirname(ROOT), '_ota-repo')


def git(*args, check=True):
    print('git', ' '.join(args))
    return subprocess.run(['git', '-C', WORK, *args], check=check, text=True, capture_output=not check)


def main():
    args = sys.argv[1:]
    r36s = '--r36s' in args
    if r36s:
        args.remove('--r36s')
    branch = 'ota-r36s' if r36s else 'ota'
    if '--branch' in args:
        i = args.index('--branch'); branch = args[i + 1]; del args[i:i + 2]
    if len(args) != 1:
        sys.exit(__doc__)
    ver = args[0]
    tag = pack_r36s.ref(ver) if r36s else f'ota-{ver}'
    files = pack_r36s.files if r36s else pack_brick.files
    if not os.path.isdir(os.path.join(WORK, '.git')):
        os.makedirs(WORK, exist_ok=True)
        git('init', '-q')
        git('remote', 'add', 'origin', REPO_URL)
        git('config', 'core.autocrlf', 'false')
    has_remote = git('fetch', '-q', 'origin', branch, check=False).returncode == 0
    if has_remote:
        git('checkout', '-q', '-B', branch, 'FETCH_HEAD')
    else:
        git('checkout', '-q', '--orphan', branch)
    listed = dict(files())
    # the tree: exactly the listed files (copied when they differ) and ota.txt
    for d, dirs, names in os.walk(WORK):
        if '.git' in dirs:
            dirs.remove('.git')
        for n in names:
            rel = os.path.relpath(os.path.join(d, n), WORK).replace(os.sep, '/')
            if rel not in listed and rel != 'ota.txt':
                os.remove(os.path.join(d, n))
    copied = 0
    for rel, src in listed.items():
        dst = os.path.join(WORK, rel)
        if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src) and sha(dst) == sha(src):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        copied += 1
    with open(os.path.join(WORK, 'ota.txt'), 'w', newline='\n') as f:
        f.write(manifest(ver, sorted(listed.items()), tag))
    print(f'{copied} files changed of {len(listed)}')
    git('add', '-A')
    git('commit', '-q', '-m', f'Elemon {ver}', check=False)
    git('tag', '-f', tag)
    git('push', 'origin', f'HEAD:refs/heads/{branch}', f'+refs/tags/{tag}')
    print(f'published {ver}: branch {branch}, tag {tag}')


if __name__ == '__main__':
    main()
