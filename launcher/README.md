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

Saves are copied to `gamedata\save-backups\` before each start (the last ten are kept). The run's output goes to `build\logs\last_run.log`.

The artwork and music are not in the repository. The launcher reads `background*.jpg/png`, `logo.png`, `icon-2.png` and `music.mp3` from `launcher\assets\` or `..\work\data\launcher\`; without them it still works, plainer. `Cinzel-Black.ttf` is the Cinzel typeface (SIL Open Font License, `OFL-Cinzel.txt`).
