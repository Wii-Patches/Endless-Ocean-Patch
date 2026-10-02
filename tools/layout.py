"""Where the hook trampolines live in the injected low-memory section.

Every patch is a set of hooks: one instruction in the game is replaced by a
branch to a small self-contained routine that runs the displaced instruction and
branches back.  A Gecko code handler stores those routines itself (C2 codes); the
patched DOL needs somewhere to put them, so the patcher adds one text section at
CAVE_BASE.

0x80001800-0x80003000 is the Wii's boot-time scratch area, which neither game
touches.  The first 0x20 bytes are skipped: the word at 0x80001800 is overwritten
by the OS early on.  Each feature gets a fixed window so the patches can be
combined freely.

Variables live in zeroed padding inside the game's own .init text (STATE below),
which every release has.
"""
CAVE_BASE = 0x80001820
CAVE_LIMIT = 0x80003000

GC_BASE = 0x80001820          # GameCube controller hook trampolines
GC_END = 0x80002A00
CC_BASE = 0x80002A00          # Classic Controller (Endless Ocean 1) hook trampolines
CC_END = 0x80003000

WINDOWS = {'gc': (GC_BASE, GC_END), 'cc': (CC_BASE, CC_END)}

STATE = 0x80005C00            # 0x80 bytes of GameCube-pad state (zero padding in both games)
