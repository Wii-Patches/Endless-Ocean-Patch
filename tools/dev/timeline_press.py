"""Boot an image, pulse A / Start through the debug feed, shoot every few seconds (dev only).

    timeline_press.py image prefix total_seconds step [buttons...]
"""
import struct, sys, time
from dolphin_run import Dolphin, shot
STATE = 0x80005C00
BTN = dict(A=0x01000000, B=0x02000000, X=0x04000000, Y=0x08000000, Start=0x10000000, Z=0x00100000,
           R=0x00200000, L=0x00400000, Up=0x00080000, Down=0x00040000, Right=0x00020000, Left=0x00010000)
def feed(g, h=0, l=0x80800000):
    g.write_mem(STATE + 0x20, struct.pack('>II', 0x00808080 | h, l))
d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
g = d.start()
total, step = float(sys.argv[3]), float(sys.argv[4])
seq = sys.argv[5:] or ['A']
try:
    g.cont(); t0 = time.time(); i = 0
    time.sleep(step)
    while time.time() - t0 < total:
        b = BTN[seq[i % len(seq)]]
        g.interrupt(); feed(g, b); g.cont(); time.sleep(0.5)
        g.interrupt(); feed(g, 0); g.cont(); time.sleep(step - 0.5)
        shot('%s_%02d.png' % (sys.argv[2], i)); i += 1
finally:
    g.close(); d.stop()
