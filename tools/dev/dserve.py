"""Persistent Dolphin session for interactive exploration (dev only).

    python3 dserve.py image [--rtc EPOCH] [--port 5599]      # runs until told to quit
    python3 dctl.py '{"op":"input","h":["A"],"secs":0.5}'    # from another process

Ops: input {h:[button names], stick:[x,y], cstick:[x,y], secs}, wait {secs}, shot {path},
mem {addr, len}, snap {path} (all of MEM1), write {addr, hex}, quit.
The game is left running between commands.
"""
import json
import socket
import struct
import sys
import time

from dolphin_run import Dolphin, shot

STATE = 0x80005C00
BTN = dict(A=0x01000000, B=0x02000000, X=0x04000000, Y=0x08000000, Start=0x10000000, Z=0x00100000,
           R=0x00200000, L=0x00400000, Up=0x00080000, Down=0x00040000, Right=0x00020000, Left=0x00010000)


def main():
    image = sys.argv[1]
    port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 5599
    extra = ''
    if '--rtc' in sys.argv:
        extra = '\nCustomRTC = True\nCustomRTCValue = %d\n' % int(sys.argv[sys.argv.index('--rtc') + 1])
    d = Dolphin(image, '/Users/larsen/eo-work/dolphin-user', extra_ini=extra)
    g = d.start()
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', port))
    srv.listen(1)
    g.cont()
    print('ready', flush=True)

    def feed(h=0, stick=(128, 128), cstick=(128, 128)):
        data = struct.pack('>II', 0x00800000 | h | (stick[0] << 8) | stick[1], (cstick[0] << 24) | (cstick[1] << 16))
        # the stub refuses writes (E00) while the CPU is stopped somewhere without
        # address translation: let it run a moment and stop again
        for _ in range(40):
            try:
                g.write_mem(STATE + 0x20, data)
                return
            except RuntimeError:
                g.cont()
                time.sleep(0.03)
                g.interrupt()
        raise RuntimeError('could not write the pad feed')

    try:
        while True:
            c, _ = srv.accept()
            req = json.loads(c.makefile().readline())
            op, out = req['op'], {'ok': True}
            try:
                if op == 'input':
                    h = 0
                    for b in req.get('h', []):
                        h |= BTN[b]
                    g.interrupt()
                    feed(h, tuple(req.get('stick', (128, 128))), tuple(req.get('cstick', (128, 128))))
                    g.cont()
                    time.sleep(req.get('secs', 0.5))
                    g.interrupt()
                    feed()
                    g.cont()
                elif op == 'wait':
                    time.sleep(req['secs'])
                elif op == 'shot':
                    shot(req['path'])
                elif op in ('mem', 'snap', 'write'):
                    g.interrupt()
                    try:
                        if op == 'mem':
                            out['hex'] = g.read_mem(req['addr'], req['len']).hex()
                        elif op == 'write':
                            g.write_mem(req['addr'], bytes.fromhex(req['hex']))
                        else:
                            with open(req['path'], 'wb') as f:
                                for a in range(0x80000000, 0x81800000, 0x10000):
                                    f.write(g.read_mem(a, 0x10000))
                    finally:
                        g.cont()
                elif op == 'quit':
                    c.sendall((json.dumps(out) + '\n').encode())
                    break
            except Exception as e:
                out = {'ok': False, 'error': repr(e)}
            c.sendall((json.dumps(out) + '\n').encode())
            c.close()
    finally:
        g.close()
        d.stop()


if __name__ == '__main__':
    main()
