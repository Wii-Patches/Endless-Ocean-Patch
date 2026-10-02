"""Boot an image and save a window shot every N seconds (dev only)."""
import sys, time
from dolphin_run import Dolphin, shot
d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
g = d.start()
try:
    g.cont()
    n, step = int(sys.argv[3]), float(sys.argv[4])
    for i in range(n):
        time.sleep(step)
        shot('%s_%02d.png' % (sys.argv[2], i))
finally:
    g.close(); d.stop()
