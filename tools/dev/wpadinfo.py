"""Dump the game's WPAD channel-0 block and info struct: wpadinfo.py image seconds"""
import struct, sys, time
from dolphin_run import Dolphin
d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
g = d.start()
u32 = lambda a: struct.unpack('>I', g.read_mem(a, 4))[0]
try:
    g.cont(); time.sleep(float(sys.argv[2])); g.interrupt()
    blk = u32(0x806a6310)
    print('block', hex(blk))
    b = g.read_mem(blk, 0xA00)
    for off in (0x8BC, 0x8C0, 0x8C1, 0x8DC, 0x988, 0x98C):
        print(' +%x' % off, b[off:off+4].hex())
    print(' info struct 0x80634ce0:', g.read_mem(0x80634ce0, 0x20).hex())
    print(' flags 80640f40', g.read_mem(0x80640f40, 4).hex())
    print(' kpad0 dev', hex(g.read_mem(0x806E0818 + 0x5C, 1)[0]))
finally:
    g.close(); d.stop()
