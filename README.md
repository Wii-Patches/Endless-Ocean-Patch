# Endless Ocean Patch

Play **Endless Ocean** and **Endless Ocean: Blue World** (Wii) with a **GameCube
controller** or a **Classic Controller**, and use **SDHC cards** (over 2 GB) in
Endless Ocean. One patcher, both games.

The patches are applied to your own copy of the game: drop a clean `.wbfs` or
`.iso` onto the patcher and play the result on a Wii (USB loader) or in Dolphin.
Nothing from the games is included in this repository.

## Status

Written and tested in Dolphin only. **Nothing here has been run on a real Wii yet.**

| | Endless Ocean (`RFBE01`, USA) | Blue World (`R4EE01`, USA) |
| --- | --- | --- |
| GameCube controller | built, tested in Dolphin | built, tested in Dolphin |
| Classic Controller | added by this patch | already built into the game |
| SDHC cards | added by this patch (not exercised yet) | already built into the game |
| Forecast Channel weather | not planned | **not done yet** |

Other regions (Europe, Japan) are not supported yet; the patcher refuses them
instead of guessing.

## Controls

Both games steer by pointing and swim while you hold a button. The layout follows
Blue World's own Classic Controller scheme, and Endless Ocean's Classic Controller
patch copies it, so the two games play the same.

### GameCube controller (port 1)

The pad reaches the games as a Classic Controller. Plug it in **before** starting
the game. Blue World asks "Use the Classic Controller?" at start-up; with a pad
plugged in the patch answers yes for you.

| GameCube | Blue World | Endless Ocean |
| --- | --- | --- |
| Control stick | steer (right stick) | steer: puts the pointer on that side of the screen |
| C-stick | cursor (left stick) | pointer too: adds to the control stick |
| L | swim | swim (B) |
| A, R | check / use | check / use (A) |
| B | cancel | swim / cancel (B) |
| X | map | map (1) |
| Y | quick turn | zoom (+) |
| Start | autoswim / shortcut menu (+) | autoswim (−) |
| Z | change view / zoom (−) | change view (2) |
| D-pad | tool menu | tool menu |

### Classic Controller (Endless Ocean only; Blue World has its own)

Same table with the Classic Controller's own buttons: left stick = cursor, right
stick = steer, `L` swim, `A`/`R` check/use, `B` cancel/swim, `X` map, `Y`/`ZR`
zoom in, `+`/`ZL` autoswim / zoom out, `−` change view.

There is no quick-turn button in Endless Ocean (the game turns you around when you
shake the Wii Remote) and a GameCube pad has no HOME button.

## Installing

Needs Python 3 with tkinter and [Wiimms ISO Tool](https://wit.wiimm.de/) (`wit`)
on your `PATH`.

```bash
python3 tools/gui.py
```

Tick what you want, drop the image on the window. The patcher reads the disc id,
patches `sys/main.dol`, rebuilds the image in the same format and replaces your
file, keeping the original next to it as `<name>.bak`. Images already modified by
something else are refused rather than corrupted, and running it again only adds
what is missing.

Command line:

```bash
python3 tools/patch_disc.py "Endless Ocean (USA).wbfs" --cc --gc --sd --ios 58
```

Options that a game does not need are reported and skipped (Blue World ignores
`--cc` and `--sd`).

### SDHC on a real Wii

Endless Ocean asks for IOS 21, which predates SDHC cards. Tick *make the disc ask
for IOS 58* (the rebuilt disc is fake-signed, like any patched image) or set the
game's IOS to 58 in your USB loader. Blue World already asks for IOS 56.

## Building from source

The routines the patcher injects ship pre-assembled in `tools/prebuilt/`. With
[devkitPPC](https://devkitpro.org/) and your own `main.dol` dumps you can rebuild
them:

```bash
EO_DOLS=/dir/with/R4EE01.dol,RFBE01.dol python3 tools/gen_prebuilt.py
```

How the patches work is in [docs/TECHNICAL.md](docs/TECHNICAL.md). Development
tools for testing in Dolphin are in `tools/dev/`.

## Credits

- **Barrel Blast Patch** and the *City Folk* GameCube patch: the Serial Interface
  polling and the idea of presenting the pad as a Classic Controller.
- **Vague Rant** and **crediar**: the Classic Controller hack this one's pointer and
  button translation follow.
- **Bero**: *SDHC Extension*, the fix the SDHC patch follows.

## Contact

quatricsoftware@gmail.com

No support will be provided for this tool.

## License

MIT, see [LICENSE](LICENSE).
