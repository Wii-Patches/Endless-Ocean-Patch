"""Build the GameCube controller feature for one release from src/gc/*.

The pad is presented to the game as a Classic Controller (a real one would feed
the same KPAD samples), see gc/gcpad.c.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import cbuild
from layout import GC_BASE, GC_END, STATE
from ops import Blob, Feature, Hook, Patch, b_insn


# Addresses per release.  `poll` is KPADiRead's first instruction (after the
# KPADRead entry stub), `sample` the load of the ring's queued-sample count,
# `probe` WPADProbe's first instruction; `disp_*` are those retail instructions.
SITES = {
    'R4EE01': dict(
        poll=(0x803E2F04, 0x9421FEF0, 'stwu 1,-272(1)'),
        sample=(0x803E307C, 0x881A013B, 'lbz 0,0x13b(26)'),
        probe=(0x803A2EE8, 0x9421FFF0, 'stwu 1,-16(1)'),
        info=(0x803A31DC, 0x9421FFF0, 'stwu 1,-16(1)'),
        infoasync=(0x803A3294, 0x9421FF70, 'stwu 1,-144(1)'),
        scene=(0x800BAE74, 0x386000C0, 'li 3,192'),
        hooks='poll,sample,probe,info,infoasync,scene',
        defs=dict(
            SI_TYPES=0x805FE668, SI_BUSY=0x805FE650, SI_SHADOW=0x805FE654,
            FN_SIGETTYPE=0x8038D2D8, FN_OSDISABLE=0x80353E4C, FN_OSRESTORE=0x80353E74,
            WPAD_TBL=0x806A6310,
            FN_USE_CC=0x8034C388, SCENE_DONE=0x800BB000,
            K_IDX=0x13A, K_CNT=0x13B, K_RING=0x13C, K_EXTLEN=0x4C0, K_EXTBUF=0x4BC,
            SAMPLE_K=26, SAMPLE_CH=25),
    ),
    'RFBE01': dict(
        poll=(0x802D56F0, 0x9421FF40, 'stwu 1,-192(1)'),
        sample=(0x802D57F4, 0x881F010F, 'lbz 0,0x10f(31)'),
        probe=(0x802ABCD8, 0x9421FFF0, 'stwu 1,-16(1)'),
        info=(0x802ABF94, 0x9421FFF0, 'stwu 1,-16(1)'),
        infoasync=(0x802AC04C, 0x9421FF70, 'stwu 1,-144(1)'),
        dpd=(0x802AE64C, 0x9421FFF0, 'stwu 1,-16(1)'),
        hooks='poll,sample,probe,info,infoasync,dpd',
        defs=dict(
            SI_TYPES=0x80483BA8, SI_BUSY=0x80483B90, SI_SHADOW=0x80483B94,
            FN_SIGETTYPE=0x802EE740, FN_OSDISABLE=0x802E57B4, FN_OSRESTORE=0x802E57DC,
            WPAD_TBL=0x8050F9B0,
            K_IDX=0x10E, K_CNT=0x10F, K_RING=0x110, K_EXTLEN=0, K_EXTBUF=0,
            SAMPLE_K=31, SAMPLE_CH=27),
    ),
}


def compile_hook(name, site, defs, debug_feed=False):
    d = ['-DSTATE=0x%08Xu' % STATE, '-DSWAP_STICKS=1', '-DHOOK_' + name.upper()]
    if site[2]:
        d += ['-DDISP_%s=%s' % (name.upper(), site[2])]
    if debug_feed:
        d.append('-DDEBUG_FEED')
    return cbuild.compile_blob(os.path.join(HERE, 'gc'), 'gcpad.c', 'hooks.S', defs, d)


def build(region, dol, debug_feed=False):
    s = SITES[region]
    ops, cur = [], GC_BASE
    for name in os.environ.get('EO_GC_HOOKS', s['hooks']).split(','):
        site, orig, _disp = s[name]
        got = struct.unpack('>I', dol.read(site, 4))[0]
        if got != orig:
            raise SystemExit('%s: %s site 0x%08X is 0x%08X, expected 0x%08X' % (region, name, site, got, orig))
        w = compile_hook(name, s[name], s['defs'], debug_feed)
        if w[-1] != 0x60000000:
            raise SystemExit('%s: hook %s does not end in the branch-back slot' % (region, name))
        w[-1] = 0
        if len(w) % 2:
            w.insert(len(w) - 1, 0x60000000)
        notes = dict(poll='KPADiRead: drive the SI auto-poller for port 1',
                     sample='KPADiRead: queue the pad as Classic Controller samples',
                     probe='WPADProbe: report a Classic Controller while a pad is plugged in',
                     info='WPADGetInfo: answer for the pad (full battery)',
                     infoasync='WPADGetInfoAsync: answer for the pad (full battery)',
                     dpd='WPAD IR-camera-enabled query: yes for the pad (the pointer is made up from the sticks)',
                     scene='controller-check scene: a pad means "use the Classic Controller", no question asked')
        ops.append(Hook(site, orig, w, cur, note=notes[name]))
        cur += (len(w) * 4 + 15) & ~15
    for a in range(STATE, STATE + 0x80, 4):
        if dol.read(a, 4) != b'\0\0\0\0':
            raise SystemExit('%s: state area 0x%08X is not zero' % (region, a))
    if debug_feed:
        # a centred, valid pad answer from the first frame (test images only)
        ops.append(Blob(STATE + 0x20, struct.pack('>II', 0x00808080, 0x80800000), 'debug feed: centred pad'))
    if cur > GC_END:
        raise SystemExit('gc code overflows its window: 0x%X > 0x%X' % (cur, GC_END))
    return Feature('gc', 'GameCube controller', region, ops)
