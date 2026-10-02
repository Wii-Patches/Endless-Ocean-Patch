"""Find instances of the pad classes in RAM (dev only): findobj.py image boot"""
import struct, sys, time
from dolphin_run import Dolphin
d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
g = d.start()
try:
    g.cont(); time.sleep(float(sys.argv[2])); g.interrupt()
    want = {0x8060bea0: 'remote?', 0x8060bea8: 'remote', 0x8060bee0: 'cc?', 0x8060bee8: 'cc', 0x8060bea4: 'r4', 0x8060bee4: 'c4'}
    for base in range(0x80600000, 0x81700000, 0x10000):
        try: buf = g.read_mem(base, 0x10000)
        except Exception as e: continue
        for i in range(0, len(buf) - 3, 4):
            v = struct.unpack('>I', buf[i:i+4])[0]
            if v in want and not (0x8060be00 <= base + i < 0x8060c000):
                print('%08x -> %s (%08x)' % (base + i, want[v], v))
finally:
    g.close(); d.stop()
