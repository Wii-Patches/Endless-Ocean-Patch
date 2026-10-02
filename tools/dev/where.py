import struct, sys, time
from dolphin_run import Dolphin, shot
d = Dolphin(sys.argv[1], '/Volumes/SSD/larsen/claude-tmp/eo/dolphin-user')
g = d.start()
try:
    g.cont(); time.sleep(float(sys.argv[2]))
    print(g.interrupt())
    r = g.cmd('g')
    regs = [int(r[i*8:(i+1)*8], 16) for i in range(len(r)//8)]
    print('pc/lr', [hex(x) for x in regs[64:72]] if len(regs) > 72 else r[:80])
    print('r1', hex(regs[1]), 'r3', hex(regs[3]))
    st = g.read_mem(0x80005C00, 0x30); print(st.hex())
    k = g.read_mem(0x806E0818, 0x80); print('dev', hex(k[0x5c]))
    shot(sys.argv[3] if len(sys.argv) > 3 else '/Volumes/SSD/larsen/claude-tmp/eo/w.png')
finally:
    g.close(); d.stop()
