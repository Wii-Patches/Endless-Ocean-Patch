"""Boot an image in Dolphin on an isolated user folder with the GDB stub on (dev only).

    from dolphin_run import Dolphin
    d = Dolphin('/path/test.iso', '/path/userdir')
    g = d.start()            # a connected gdbmem.Gdb, halted at boot
"""
import os
import shutil
import subprocess
import time

from gdbmem import Gdb

DOLPHIN = '/Applications/Dolphin.app/Contents/MacOS/Dolphin'
HOME = os.path.expanduser('~/Library/Application Support/Dolphin')

DOLPHIN_INI = """[General]
GDBPort = 2159
ShowLag = False
[Core]
CPUCore = 4
SIDevice0 = {si0}
SIDevice1 = 0
SIDevice2 = 0
SIDevice3 = 0
WiiSDCard = {sd}
WiiSDCardPath = {sdpath}
WiiSDCardAllowWrites = True
SkipIPL = True
OverclockEnable = False
EmulationSpeed = {speed}
[Interface]
ConfirmStop = False
UsePanicHandlers = False
[Display]
Fullscreen = False
RenderToMain = False
"""
WIIMOTE_INI = "[Wiimote1]\nSource = {src}\nExtension = {ext}\n"


class Dolphin:
    def __init__(self, image, user, si0=int(os.environ.get('EO_SI0', 0)), sd=False, sdpath='', wiimote=int(os.environ.get('EO_WIIMOTE', 0)), wiimote_ext=os.environ.get('EO_WIIEXT', 'None'), speed=1.0, extra_ini=''):
        self.image, self.user = image, user
        self.si0, self.sd, self.sdpath, self.wiimote, self.speed = si0, sd, sdpath, wiimote, speed
        self.wiimote_ext = wiimote_ext
        self.extra_ini = extra_ini
        self.proc = None

    def prepare(self):
        shutil.rmtree(self.user, ignore_errors=True)
        os.makedirs(os.path.join(self.user, 'Config'))
        with open(os.path.join(self.user, 'Config', 'Dolphin.ini'), 'w') as f:
            f.write(DOLPHIN_INI.format(si0=self.si0, sd=str(self.sd), sdpath=self.sdpath, speed=self.speed)
                    + self.extra_ini)
        with open(os.path.join(self.user, 'Config', 'WiimoteNew.ini'), 'w') as f:
            f.write(WIIMOTE_INI.format(src=self.wiimote, ext=self.wiimote_ext))
        for n in ('GFX.ini',):
            p = os.path.join(HOME, 'Config', n)
            if os.path.exists(p):
                shutil.copy(p, os.path.join(self.user, 'Config', n))

    def start(self, tries=40):
        self.prepare()
        self.proc = subprocess.Popen([DOLPHIN, '-u', self.user, '-b', '-e', self.image],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        last = None
        for _ in range(tries):
            time.sleep(1.5)
            try:
                return Gdb(timeout=30)
            except OSError as e:
                last = e
        raise RuntimeError('could not connect to the GDB stub: %s' % last)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except Exception:
                self.proc.kill()


def shot(path, owner='Dolphin'):
    """PNG of the emulator window (not the whole screen)."""
    import Quartz
    best = None
    for w in Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID):
        if w.get('kCGWindowOwnerName') == owner and w.get('kCGWindowLayer') == 0:
            b = w['kCGWindowBounds']
            if best is None or b['Width'] * b['Height'] > best[1]:
                best = (w['kCGWindowNumber'], b['Width'] * b['Height'])
    if not best:
        raise RuntimeError('no Dolphin window')
    subprocess.check_call(['screencapture', '-x', '-o', '-l%d' % best[0], path])
