"""Dump the game's pad object for channel 0 under scripted feed (dev only): padobj.py image boot"""
import struct, sys, time
from dolphin_run import Dolphin
STATE = 0x80005C00
d = Dolphin(sys.argv[1], '/Volumes/SSD/larsen/claude-tmp/eo/dolphin-user')
g = d.start()
u32 = lambda a: struct.unpack('>I', g.read_mem(a, 4))[0]
def feed(h=0, stick=(128,128), cstick=(128,128)):
    g.write_mem(STATE + 0x20, struct.pack('>II', 0x00800000 | h | (stick[0] << 8) | stick[1], (cstick[0] << 24) | (cstick[1] << 16)))
def dump(tag):
    pad = u32(0x8064aac0)
    o = g.read_mem(pad, 0x40)
    dev = struct.unpack('>I', o[0x24:0x28])[0]
    print(tag, 'pad', hex(pad), 'chan', o[4:6].hex(), 'btn', o[8:10].hex(), 'sticks', o[0x14:0x1a].hex(), 'dev', hex(dev))
    if 0x80000000 <= dev < 0x81800000:
        dv = g.read_mem(dev, 0x40)
        print('   dev+4', dv[4:6].hex(), '+6', dv[6:7].hex(), '+0x1c..', dv[0x1c:0x20].hex(), 'count', dv[0x1f], 'buf+5c', g.read_mem(dev + 0x20 + 0x5c, 2).hex(), 'buf+60', g.read_mem(dev + 0x20 + 0x60, 4).hex())
try:
    g.cont(); time.sleep(float(sys.argv[2])); g.interrupt(); dump('idle   ')
    for tag, kw in (('A', dict(h=0x01000000)), ('cleft', dict(cstick=(30,128))), ('stickR', dict(stick=(228,128))), ('Start', dict(h=0x10000000))):
        feed(**kw); g.cont(); time.sleep(1.5); g.interrupt(); dump(tag.ljust(7))
finally:
    g.close(); d.stop()
