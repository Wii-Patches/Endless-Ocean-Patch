import struct, sys, time
from dolphin_run import Dolphin
d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
g = d.start()
u32 = lambda a: struct.unpack('>I', g.read_mem(a, 4))[0]
try:
    g.cont(); time.sleep(float(sys.argv[2])); g.interrupt()
    for pad in (0x80647d40, 0x80648860):
        o = g.read_mem(pad, 0x60)
        print('pad %08x:' % pad, o.hex())
        dev = struct.unpack('>I', o[0x24:0x28])[0]
        if 0x80000000 <= dev < 0x81800000:
            print('   dev %08x:' % dev, g.read_mem(dev, 0x40).hex())
    print('flags 80640f40', g.read_mem(0x80640f40, 4).hex(), ' r13-0x2530:', g.read_mem(0x807c3a80 - 0x2530, 4).hex())
finally:
    g.close(); d.stop()
