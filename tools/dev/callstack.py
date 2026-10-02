"""Sample the PPC call stack a few times (dev only): callstack.py image seconds-before samples"""
import struct, sys, time
from dolphin_run import Dolphin
d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
g = d.start()
def regs():
    r = g.cmd('g'); return [int(r[i*8:(i+1)*8], 16) for i in range(len(r)//8)]
try:
    g.cont(); time.sleep(float(sys.argv[2]))
    for n in range(int(sys.argv[3])):
        g.interrupt()
        r = g.cmd('g'); R = [int(r[i*8:(i+1)*8], 16) for i in range(len(r)//8)]
        # gdb ppc: r0-31, f0-31 (64-bit each = 16 hex), pc, msr, cr, lr, ctr, xer...
        # 32 gprs*8 hex = 256 chars; 32 fprs*16 = 512 chars; then pc,msr,cr,lr,ctr,xer,fpscr
        gpr = [int(r[i*8:(i+1)*8], 16) for i in range(32)]
        pc, msr, cr, lr, ctr = [int(g.cmd('p%x' % n)[:8], 16) for n in (0x40, 0x41, 0x42, 0x43, 0x44)]
        chain = []; sp = gpr[1]
        for _ in range(12):
            try:
                back = struct.unpack('>I', g.read_mem(sp, 4))[0]
                lrs = struct.unpack('>I', g.read_mem(back + 4, 4))[0] if back else 0
            except Exception:
                break
            chain.append(hex(lrs)); sp = back
            if not back: break
        print('pc', hex(pc), 'lr', hex(lr), 'chain', chain)
        g.cont(); time.sleep(1.5)
finally:
    g.close(); d.stop()
