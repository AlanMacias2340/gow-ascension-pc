# scripts

PowerShell helpers for the Windows build. Run them from anywhere; paths are taken from the script's location.

| Script | What it does |
|---|---|
| `build.ps1 [-Name x]` | `vcvars64` + `ninja -C build\win`, log in `build\logs\build[-x].log`; prints the time, the error lines and the last line. |
| `run.ps1 [-Seconds 120] [-Save fresh\|backup\|keep] [-Name run] [-Env @{...}] [-Profile [-ProfileAt 45]]` | Runs the game with the window visible for a while, then kills it and prints `tools\log_summary.py`. `fresh` (default) moves the save aside so the first-use menus show; `backup` puts `work\save-backup` in place (straight to the cinematic). `-Profile` samples the busiest threads with `tools\profile_threads.py`. |
| `launcher.ps1 [-Play]` | Opens the launcher (`launcherscension_launcher.py`): window, language, mods, music; `-Play` starts the game with the saved settings. |
| `relift.ps1 jobmods [-Only <sha>]` | Re-lifts the SPU job modules with `tools\jobmods_extra_funcs.json`; `-Only` re-lifts one module and copies only its sources, so only it recompiles. |
| `relift.ps1 fragments` | Lifts `tools\job_fragments.json` position-independently into `src\spu\pic_*`. |

Python tools used with them (`tools\`):

- `log_summary.py <log>`: fps, the end-of-loading stall, the cinematic's speed (`VDEC_TIMELOG=1`), interpreted SPU code (`SPU_INTERP_HIST=1`), the HLE/syscall/poll histograms and error-like lines.
- `frame_timeline.py <log>`: the per-frame chain (GPU report, RsxSync, MeshProc, EDGE, video picture) in time; see its docstring for the variables to set.
- `profile_threads.py --pid --dbg`: CPU per thread, then `prof` on the busiest through `PS3_DEBUG`, resolved with `maprva.py`.

Examples:

```powershell
.\scripts\build.ps1 -Name vblank
.\scripts\run.ps1 -Save backup -Seconds 90 -Name cin -Env @{ VDEC_TIMELOG = "1" }
.\scripts\run.ps1 -Seconds 80 -Name menus -Profile -ProfileAt 45
.\scripts\run.ps1 -Save backup -Seconds 75 -Name tl -Env @{ SPU_ATOM_EA = "99AA80"; SPU_ATOM_EA_MAX = "1"; PPU_WWATCH = "99AA80"; PPU_WWATCH_LEN = "0x80"; PPU_WWATCH_MAX = "300000"; GCM_REPORTLOG = "1000000"; VDEC_TIMELOG = "1" }
python tools\frame_timeline.py build\logs\tl.log
```
