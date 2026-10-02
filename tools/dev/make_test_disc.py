#!/usr/bin/env python3
"""Build a patched test image for Dolphin (dev only).

    python3 tools/dev/make_test_disc.py "Endless Ocean - Blue World (USA).wbfs" out.iso gc [--debug-feed]

Extracts the disc once into <out>.fst (reused), builds the requested features
straight from src/ (not from tools/prebuilt, so --debug-feed can be used: the
pad's response is then read from STATE+0x20, which a debugger writes), patches
sys/main.dol and rebuilds an .iso.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'src'))
from dol import Dol
from ops import apply_static
from regions import REGIONS


def main():
    image, out, feats = sys.argv[1], sys.argv[2], [a for a in sys.argv[3:] if not a.startswith('--')]
    debug = '--debug-feed' in sys.argv
    fst = out + '.fst'
    if not os.path.isdir(fst):
        subprocess.check_call(['wit', 'extract', image, '--dest', fst, '--psel', 'data', '-q'])
    dolp = os.path.join(fst, 'sys', 'main.dol')
    if not os.path.exists(dolp + '.orig'):
        shutil.copyfile(dolp, dolp + '.orig')
    with open(os.path.join(fst, 'sys', 'boot.bin'), 'rb') as f:
        disc_id = f.read(6).decode()
    if disc_id not in REGIONS:
        sys.exit('unknown disc %s' % disc_id)
    dol = Dol(dolp + '.orig')
    built = []
    for name in feats:
        mod = __import__('gen_' + name)
        kw = {'debug_feed': True} if (debug and name == 'gc') else {}
        built.append(mod.build(disc_id, dol, **kw))
    apply_static(dol, built)
    dol.save(dolp)
    subprocess.check_call(['wit', 'copy', fst, '--dest', out, '--iso', '--overwrite', '-q'])
    print('built', out, disc_id, feats, 'debug-feed' if debug else '')


if __name__ == '__main__':
    main()
