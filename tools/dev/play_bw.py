"""Boot the debug-feed image, press Start now and then, save window shots (dev only)."""
import struct, sys, time
from dolphin_run import Dolphin, shot

STATE = 0x80005C00
def feed(g, h, l=(128 << 24) | (128 << 16)):
    g.write_mem(STATE + 0x20, struct.pack('>II', 0x00800000 | h, l))

d = Dolphin(sys.argv[1], '/Volumes/SSD/larsen/claude-tmp/eo/dolphin-user')
g = d.start()
out = sys.argv[2]
try:
    g.cont(); time.sleep(float(sys.argv[3]) if len(sys.argv) > 3 else 40)
    g.interrupt(); feed(g, (128 << 8) | 128); g.cont(); time.sleep(2)
    shot(out + '_0.png')
    for i in range(1, 5):
        g.interrupt(); feed(g, 0x10000000 | (128 << 8) | 128)   # Start
        g.cont(); time.sleep(0.4)
        g.interrupt(); feed(g, (128 << 8) | 128); g.cont(); time.sleep(3)
        shot('%s_%d.png' % (out, i))
finally:
    g.close(); d.stop()
