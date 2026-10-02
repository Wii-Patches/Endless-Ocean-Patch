"""Dolphin check of the GameCube bridge on Blue World (needs a --debug-feed test image).

    python3 tools/dev/test_gc_bw.py /path/bw_gc_debug.iso [seconds-to-boot]
"""
import struct
import sys
import time

from dolphin_run import Dolphin

STATE = 0x80005C00
K0 = 0x806E0818          # KPAD channel 0 state (stride 0x5C0)


def u32(g, a):
    return struct.unpack('>I', g.read_mem(a, 4))[0]


def main():
    image = sys.argv[1]
    boot = float(sys.argv[2]) if len(sys.argv) > 2 else 45
    d = Dolphin(image, '/Users/larsen/eo-work/dolphin-user')
    g = d.start()
    try:
        print('stop reply:', g.cmd('?'))
        print('disc', g.read_mem(0x80000000, 6))
        g.cont()
        time.sleep(boot)
        g.interrupt()
        print('hook sites:', [hex(u32(g, a)) for a in (0x803E2F04, 0x803E307C, 0x803A2EE8)])
        # a centred pad, A held: INBUFH = valid | A | sticks 128,128 ; INBUFL = C-stick 128,128
        h = 0x00800000 | 0x01000000 | (128 << 8) | 128
        l = (128 << 24) | (128 << 16)
        g.write_mem(STATE + 0x20, struct.pack('>II', h, l))
        g.cont()
        time.sleep(3)
        g.interrupt()
        k = g.read_mem(K0, 0x5C0)
        print('dev type k[0x5c] =', hex(k[0x5C]), ' idx', k[0x13A], 'cnt', k[0x13B])
        print('hold', hex(struct.unpack('>I', k[0:4])[0]), 'ex hold', hex(struct.unpack('>I', k[0x60:0x64])[0]))
        print('lstick', struct.unpack('>ff', k[0x6C:0x74]), 'rstick', struct.unpack('>ff', k[0x74:0x7C]))
        ring = [k[0x13C + i * 0x38:0x13C + (i + 1) * 0x38] for i in range(16)]
        for i, s in enumerate(ring[:4]):
            print(i, s.hex())
        g.cont()
        time.sleep(1)
    finally:
        g.close()
        d.stop()


if __name__ == '__main__':
    main()
