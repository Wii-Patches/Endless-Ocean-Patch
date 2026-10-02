# Technical notes

How the patches work and where they hook. Addresses are the USA `main.dol`s
(`RFBE01` Endless Ocean, `R4EE01` Blue World). The discs this was built against are
the Wiimmfi-patched dumps; none of the sites are touched by that.

## One data set, one patched `main.dol`

Every feature is a list of operations on one release's `main.dol` (see
`tools/ops.py`): **Patch** (overwrite bytes), **Blob** (new bytes in zero padding) and
**Hook** (replace one instruction with a branch to a self-contained routine that runs
the displaced instruction and branches back). `tools/prebuilt/<feature>_<disc id>.json`
holds them, including the retail bytes expected at every site; the patcher refuses a
`main.dol` that does not match. The hook routines are placed in one new text section at
`0x80001820` (the Wii's boot-time scratch area, never touched by these games);
variables live in zero padding inside the game's own `.init` text.

`src/gen_*.py` build the features (devkitPPC compiles the C in `src/gc` and
`src/cc`); `tools/gen_prebuilt.py` writes the JSON.

## GameCube controller (both games)

Both games link the Serial Interface library but nothing polls the pads, and a Wii
game with no Wii Remote has no KPAD sample to read. Following the City Folk port, the
pad is presented as a **Classic Controller** so each game's own Classic Controller path
does the rest. Hooks (`src/gc/gcpad.c`):

| Hook | What it does |
| --- | --- |
| `KPADiRead` entry | drives the SI hardware's auto-polling for port 1, re-probes a replugged pad, acknowledges latched errors |
| `KPADiRead`, at the queued-sample count | queues two Classic Controller samples per frame in KPAD's ring (the game's controller class reads the second one) |
| `WPADProbe` | reports a Classic Controller on channel 0 while a pad is plugged in |
| `WPADGetInfo` / `WPADGetInfoAsync` | answers for the pad (full battery). `WPADGetInfo` sleeps until the Wii Remote's reply arrives; a pad has no radio, so the game hung forever on its controller-check scene without this |
| IR-camera-enabled query (Endless Ocean) | says yes. The game ignores the pointer unless WPAD says the IR camera is on |
| controller-check scene (Blue World, `0x800BAE74`) | with a pad plugged in, runs the game's "use the Classic Controller" routine (`0x8034C388`) and leaves the scene, skipping the "Use the Classic Controller?" prompt, which is answered with the Wii Remote's pointer |

Stick values are `(raw − 128) × 3`, capped at 308, which is what both games' Classic
Controller code expects (dead zone 60, full scale 308). The GameCube control stick
becomes the Classic Controller's right stick and the C-stick its left stick (swim
direction and cursor in Blue World).

KPAD ring layout: Blue World `+0x13A` write index, `+0x13B` queued count, `+0x13C`
samples of `0x38` bytes (an optional extra buffer from `+0x4BC`, length `+0x4C0`);
Endless Ocean `+0x10E`, `+0x10F`, `+0x110` (fixed ring of 16). Blue World needs at least
two queued samples (it keeps the newest as the next call's reference); Endless Ocean
processes any.

Hook sites:

| | Endless Ocean | Blue World |
| --- | --- | --- |
| `KPADiRead` entry | `0x802D56F0` | `0x803E2F04` |
| sample count load | `0x802D57F4` | `0x803E307C` |
| `WPADProbe` | `0x802ABCD8` | `0x803A2EE8` |
| `WPADGetInfo` / `Async` | `0x802ABF94` / `0x802AC04C` | `0x803A31DC` / `0x803A3294` |
| IR-camera query | `0x802AE64C` | – |
| KPAD channel 0 struct | `0x80530098` (stride `0x524`) | `0x806E0818` (stride `0x5C0`) |

## Classic Controller (Endless Ocean)

The game only knows the Wii Remote. Two hooks in `KPADiRead`'s per-sample loop
(`src/cc/cc.c`):

- before `andi. r0,r7,0x9FFF` (`0x802D5CA4`): translate the sample's Classic Controller
  buttons into the Wii Remote buttons the game reads (table in the README);
- after the `bl` to the IR routine (`0x802D5DA8`): put the pointer at
  `clamp(left stick + right stick)` and mark it valid. A stick fully to one side puts
  the pointer on that edge of the screen, which is how this game turns.

A real Classic Controller and the GameCube pad both go through this.

## SDHC (Endless Ocean)

Endless Ocean links the same Nintendo `PFD` SD driver as *Animal Crossing: City Folk*,
instruction for instruction at every site, so Bero's SDHC Extension carries over
unchanged (`src/gen_sd.py`): read the SDHC bit IOS reports in
`ISD_GetDeviceStatus`, use block addresses instead of byte addresses, and the CSD v2
capacity formula. Helpers and trampolines live in zero padding at `0x800058C0`.

Blue World's driver is newer and already does all of this: its multi-block read/write
shifts the address by 9 only when the IOS status word's `0x100000` bit is clear, and its
`get_total_sectors` handles CSD v2. It asks for IOS 56, which supports SDHC.

## How it was tested

Dolphin, with its GDB stub reading KPAD while a debug build (`--debug-feed`) takes the
pad's answer from memory instead of the SI hardware (Dolphin's input injection did not
deliver in earlier ports). `tools/dev/` has the harness: `make_test_disc.py` builds a
test image, `interact.py` plays scripted input and saves window shots.

- Blue World: every button and both sticks reach KPAD as a Classic Controller; boot
  passes the controller-check scene, the intro, and the title screen, where the
  cursor follows the C-stick.
- Endless Ocean: buttons and pointer reach KPAD; with the IR-camera hook the pointer is
  drawn, follows the stick, and `A` clicks "Create Save Data", after which the game
  starts. The patched production image boots with no pad attached.
- Not exercised: a real Wii, the SDHC patch with an SDHC image, swimming and the tool
  menu in-game, a Wii Remote connected alongside the pad.
