"""EO1: feed the debug pad and dump KPAD channel 0 (dev only): kpad_eo1.py image boot"""
import struct, sys, time
from dolphin_run import Dolphin
STATE = 0x80005C00; K0 = 0x80530098
d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
g = d.start()
def feed(h=0, stick=(128,128), cstick=(128,128)):
    g.write_mem(STATE + 0x20, struct.pack('>II', 0x00800000 | h | (stick[0] << 8) | stick[1], (cstick[0] << 24) | (cstick[1] << 16)))
def dump(tag):
    k = g.read_mem(K0, 0x84)
    f = lambda o: struct.unpack('>f', k[o:o+4])[0]
    print(tag, 'hold %08x dev %02x err %02x dpd %02x fmt %02x' % (struct.unpack('>I', k[0:4])[0], k[0x5c], k[0x5d], k[0x5e], k[0x5f]),
          'pos (%.2f,%.2f)' % (f(0x20), f(0x24)), 'cc hold %08x' % struct.unpack('>I', k[0x60:0x64])[0],
          'L(%.2f,%.2f) R(%.2f,%.2f)' % (f(0x6c), f(0x70), f(0x74), f(0x78)))
try:
    g.cont(); time.sleep(float(sys.argv[2])); g.interrupt(); dump('idle  ')
    for tag, kw in (('A', dict(h=0x01000000)), ('stickDn', dict(stick=(128,67))), ('Cleft', dict(cstick=(40,128))), ('B', dict(h=0x02000000)), ('X', dict(h=0x04000000))):
        feed(**kw); g.cont(); time.sleep(1.5); g.interrupt(); dump(tag.ljust(7))
finally:
    g.close(); d.stop()
