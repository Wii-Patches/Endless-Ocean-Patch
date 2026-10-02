"""Read memory words after N seconds: peek.py image seconds addr[:len] ..."""
import struct, sys, time
from dolphin_run import Dolphin
d = Dolphin(sys.argv[1], '/Volumes/SSD/larsen/claude-tmp/eo/dolphin-user')
g = d.start()
try:
    g.cont(); time.sleep(float(sys.argv[2])); g.interrupt()
    for a in sys.argv[3:]:
        addr, _, n = a.partition(':'); addr = int(addr, 16); n = int(n or 4)
        print('%08x: %s' % (addr, g.read_mem(addr, n).hex()))
finally:
    g.close(); d.stop()
