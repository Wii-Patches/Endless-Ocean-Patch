"""Read interrupt / SI / VI registers of a running image (dev only): hwregs.py image seconds"""
import struct, sys, time
from dolphin_run import Dolphin
d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
g = d.start()
def rd(a):
    try: return struct.unpack('>I', g.read_mem(a, 4))[0]
    except Exception as e: return None
try:
    g.cont(); time.sleep(float(sys.argv[2]))
    for k in range(3):
        g.interrupt()
        msr = int(g.cmd('p41')[:8], 16)
        pc = int(g.cmd('p40')[:8], 16)
        f = lambda v: 'n/a' if v is None else '%08x' % v
        print('pc %08x msr %08x (EE=%d)' % (pc, msr, (msr >> 15) & 1))
        print(' PI INTSR', f(rd(0xCC003000)), 'INTMSR', f(rd(0xCC003004)))
        print(' VI DI0', f(rd(0xCC002030)), 'DI1', f(rd(0xCC002034)))
        print(' SI POLL', f(rd(0xCD006430)), 'COMCSR', f(rd(0xCD006434)), 'SR', f(rd(0xCD006438)), 'OUT0', f(rd(0xCD006400)), 'INH', f(rd(0xCD006404)))
        print(' OS interrupt mask 0x800000C4', f(rd(0x800000C4)), 'cur level', f(rd(0x800000C8)))
        g.cont(); time.sleep(2)
finally:
    g.close(); d.stop()
