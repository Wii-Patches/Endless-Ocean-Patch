"""Dump every OS thread's state and call chain (dev only): threads.py image seconds [decomp.c]"""
import bisect, re, struct, sys, time
from dolphin_run import Dolphin

def load_syms(path):
    ents = []
    if path:
        for m in re.finditer(r'(?m)^//// ([0-9a-f]{8}) (\S+) size=(\d+)', open(path).read()):
            ents.append((int(m.group(1), 16), m.group(2)))
    ents.sort()
    return ents

def sym(ents, a):
    if not ents:
        return hex(a)
    i = bisect.bisect_right([e[0] for e in ents], a) - 1
    return '%s+0x%x' % (ents[i][1], a - ents[i][0]) if i >= 0 else hex(a)

d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
ents = load_syms(sys.argv[3] if len(sys.argv) > 3 else '')
g = d.start()
u32 = lambda a: struct.unpack('>I', g.read_mem(a, 4))[0]
try:
    g.cont(); time.sleep(float(sys.argv[2])); g.interrupt()
    t = u32(0x800000DC)
    n = 0
    while t and n < 40:
        state = struct.unpack('>H', g.read_mem(t + 0x2C8, 2))[0]
        r1 = u32(t + 4); lr = u32(t + 0x84); prio = u32(t + 0x2D0); q = u32(t + 0x2DC)
        chain = [sym(ents, lr)]
        sp = r1
        for _ in range(10):
            try:
                back = u32(sp)
                if not back or back < 0x80000000: break
                chain.append(sym(ents, u32(back + 4))); sp = back
            except Exception:
                break
        print('thread %08x state %d prio %d waitq %08x' % (t, state, prio, q))
        print('    ' + ' <- '.join(chain))
        t = u32(t + 0x2FC); n += 1
finally:
    g.close(); d.stop()
