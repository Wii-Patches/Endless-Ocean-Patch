"""Boot and play back a scripted input list through the debug feed (dev only).

    interact.py image prefix wait_boot  'A:0.5' 'wait:5' 'Left:0.3' 'cstick=228,128:2' ...
Each step is NAME:seconds-held, wait:seconds, or cstick=x,y:seconds / stick=x,y:seconds.
A window shot is taken after every step.
"""
import struct, sys, time
from dolphin_run import Dolphin, shot
STATE = 0x80005C00
BTN = dict(A=0x01000000, B=0x02000000, X=0x04000000, Y=0x08000000, Start=0x10000000, Z=0x00100000,
           R=0x00200000, L=0x00400000, Up=0x00080000, Down=0x00040000, Right=0x00020000, Left=0x00010000)
def feed(g, h=0, stick=(128, 128), cstick=(128, 128)):
    hh = 0x00800000 | h | (stick[0] << 8) | stick[1]
    ll = (cstick[0] << 24) | (cstick[1] << 16)
    g.write_mem(STATE + 0x20, struct.pack('>II', hh, ll))
d = Dolphin(sys.argv[1], '/Volumes/SSD/larsen/claude-tmp/eo/dolphin-user')
g = d.start()
try:
    g.cont(); time.sleep(float(sys.argv[3]))
    for n, step in enumerate(sys.argv[4:]):
        name, _, secs = step.rpartition(':'); secs = float(secs)
        g.interrupt()
        if name == 'wait': feed(g)
        elif name.startswith('cstick='):
            x, y = map(int, name[7:].split(',')); feed(g, cstick=(x, y))
        elif name.startswith('stick='):
            x, y = map(int, name[6:].split(',')); feed(g, stick=(x, y))
        else: feed(g, BTN[name])
        g.cont(); time.sleep(secs)
        g.interrupt(); feed(g); g.cont(); time.sleep(1.5)
        shot('%s_%02d.png' % (sys.argv[2], n))
finally:
    g.close(); d.stop()
