"""Button / stick sweep for the GameCube bridge on Blue World (debug-feed image)."""
import struct
import sys
import time

from dolphin_run import Dolphin

STATE = 0x80005C00
K0 = 0x806E0818
BTN = dict(A=0x01000000, B=0x02000000, X=0x04000000, Y=0x08000000, Start=0x10000000, Z=0x00100000,
           R=0x00200000, L=0x00400000, Up=0x00080000, Down=0x00040000, Right=0x00020000, Left=0x00010000)
CC = {0x1: 'UP', 0x2: 'LEFT', 0x4: 'ZR', 0x8: 'X', 0x10: 'A', 0x20: 'Y', 0x40: 'B', 0x80: 'ZL', 0x200: 'R', 0x400: '+',
      0x800: 'HOME', 0x1000: '-', 0x2000: 'L', 0x4000: 'DOWN', 0x8000: 'RIGHT'}


def feed(g, h, l=(128 << 24) | (128 << 16)):
    g.write_mem(STATE + 0x20, struct.pack('>II', 0x00800000 | h, l))


def state(g):
    k = g.read_mem(K0, 0x5C0)
    return k, struct.unpack('>I', k[0x60:0x64])[0], struct.unpack('>ffff', k[0x6C:0x7C]), k[0x5C]


def names(m):
    return '+'.join(n for b, n in CC.items() if m & b) or '-'


def main():
    d = Dolphin(sys.argv[1], '/Users/larsen/eo-work/dolphin-user')
    g = d.start()
    try:
        g.cont()
        time.sleep(float(sys.argv[2]) if len(sys.argv) > 2 else 40)
        g.interrupt()
        for name, bit in BTN.items():
            feed(g, bit | (128 << 8) | 128)
            g.cont(); time.sleep(1.2); g.interrupt()
            k, hold, st, dev = state(g)
            print('%-6s -> dev %d hold 0x%04x %s' % (name, dev, hold & 0xFFFF, names(hold & 0xFFFF)))
        sticks = [('ctrl right', (228 << 8) | 128, (128 << 24) | (128 << 16)), ('ctrl up', (128 << 8) | 228, (128 << 24) | (128 << 16)),
                  ('C right', (128 << 8) | 128, (228 << 24) | (128 << 16)), ('C up', (128 << 8) | 128, (128 << 24) | (228 << 16)),
                  ('ctrl left', (28 << 8) | 128, (128 << 24) | (128 << 16)), ('ctrl down', (128 << 8) | 28, (128 << 24) | (128 << 16))]
        for name, h, l in sticks:
            feed(g, h, l)
            g.cont(); time.sleep(1.2); g.interrupt()
            k, hold, st, dev = state(g)
            print('%-10s -> lstick (%.2f, %.2f) rstick (%.2f, %.2f)' % ((name,) + st))
        g.cont()
    finally:
        g.close()
        d.stop()


if __name__ == '__main__':
    main()
