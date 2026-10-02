"""Build the Classic Controller feature (Endless Ocean, first game) from src/cc/*."""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import cbuild
from layout import CC_BASE, CC_END
from ops import Feature, Hook

# `buttons` is the `andi. r0,r7,0x9fff` in KPADiRead's sample loop, `pointer` the
# `bl` to the IR routine there.  Blue World plays with a Classic Controller natively.
SITES = {
    'RFBE01': dict(
        buttons=(0x802D5CA4, 0x70E09FFF, 'andi. 0,7,0x9fff'),
        pointer=(0x802D5DA8, 0x4BFFEF2D, ''),
    ),
}


def _decode_bl(word, at):
    li = word & 0x03FFFFFC
    if li & 0x02000000:
        li -= 0x04000000
    return (at + li) & 0xFFFFFFFF


def build(region, dol):
    s = SITES[region]
    ops, cur = [], CC_BASE
    for name in ('buttons', 'pointer'):
        site, orig, disp = s[name]
        got = struct.unpack('>I', dol.read(site, 4))[0]
        if got != orig:
            raise SystemExit('%s: %s site 0x%08X is 0x%08X, expected 0x%08X' % (region, name, site, got, orig))
        defs, extra = {}, ['-DHOOK_' + name.upper()]
        if disp:
            extra.append('-DDISP_%s=%s' % (name.upper(), disp))
        if name == 'pointer':
            if (orig >> 26) != 18 or not orig & 1:
                raise SystemExit('%s: 0x%08X is not a bl' % (region, site))
            defs['FN_IR'] = _decode_bl(orig, site)
        w = cbuild.compile_blob(os.path.join(HERE, 'cc'), 'cc.c', 'hooks.S', defs, extra, hard_float=True)
        if w[-1] != 0x60000000:
            raise SystemExit('%s: hook %s does not end in the branch-back slot' % (region, name))
        w[-1] = 0
        if len(w) % 2:
            w.insert(len(w) - 1, 0x60000000)
        notes = dict(buttons='KPAD sample loop: Classic Controller buttons -> Wii Remote buttons',
                     pointer='KPAD sample loop: Classic Controller sticks -> pointer')
        ops.append(Hook(site, orig, w, cur, note=notes[name]))
        cur += (len(w) * 4 + 15) & ~15
    if cur > CC_END:
        raise SystemExit('cc code overflows its window: 0x%X > 0x%X' % (cur, CC_END))
    return Feature('cc', 'Classic Controller', region, ops)
