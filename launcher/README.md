# Launcher

`ascension_launcher.py` (Python 3 with Tk, and Pillow) sets up the game and starts it. Open it with `scripts\launcher.ps1`, or `python launcher\ascension_launcher.py`; `--play` starts the game with the saved settings and no window.

Pages: Home (cross-fading artwork, quick settings), Video, Game, Mods, Advanced. Settings are kept in `%APPDATA%\ascension-launcher\settings.json` and reach the game as ps3recomp environment switches:

| Setting | Switch |
|---|---|
| Display mode, window size | `PS3_FULLSCREEN`, `PS3_WINDOW_SIZE` (F11 or Alt+Enter toggles in game) |
| Language | `PS3_SYS_LANG` (the console language, read when the game makes its system save), and bytes `0x1C` (text) / `0x1D` (voices) of `BCES01741-SYSDATA/SAVEDATA` afterwards |
| Subtitles | byte `0x28` of the same file (the game's `-subtitlesOn` drives the same switch) |
| Confirm button | `PS3_ENTER_BUTTON` |
| Esc closes the game | `PS3_ESC_QUITS` |
| FPS counter | `LD_PERF_OVERLAY` |
| Embedded | `PS3_PARENT_HWND` (the game renders inside the launcher's window) |
| Mods | `PS3_MODS` (enabled folders, first wins; each mirrors `USRDIR`) |
| Icon | `PS3_WINDOW_ICON` (`icon-2.png` as an `.ico`) |

Mods come from two places, listed together in one priority order (first wins): `mods-builtin/` in this repository (shown as included) and the user's mods folder. A mod is a folder that mirrors `USRDIR` (its files replace the disc's), and/or a `mod.json`:

```json
{"name": "Pular intro", "description": "...",
 "psarc_patches": {"GAME.PSARC": {"/INTRO/BOOT_BCES01741.TXT": {"text": ""}}}}
```

`psarc_patches` are recipes for files inside an archive: `{"text": ...}` replaces one, `{"insert_after": <line>, "line": <new line>}` adds a line. At PLAY the launcher builds each patched archive once from the disc's copy (or from the copy the highest-priority mod ships) into `%APPDATA%\ascension-launcher\generated\`, applying every enabled mod's recipes, lowest priority first, and puts that folder first in `PS3_MODS`. Included: **Skip intro** (an empty boot-screen list).

Brazilian Portuguese needs the PT-BR mod, which the Mods page builds from your own US disc (an `.iso` or its extracted folder) with `tools/make_ptbr_mod.py`; with it on, the language list offers Português (Brasil).

Saves are copied to `gamedata\save-backups\` before each start (the last ten are kept). The run's output goes to `build\logs\last_run.log`.

The artwork and music are not in the repository. The launcher reads `background*.jpg/png`, `logo.png`, `icon-2.png` and `music.mp3` from `launcher\assets\` or `..\work\data\launcher\`; without them it still works, plainer. `Cinzel-Black.ttf` is the Cinzel typeface (SIL Open Font License, `OFL-Cinzel.txt`).
