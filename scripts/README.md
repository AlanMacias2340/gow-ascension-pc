# scripts

One folder per platform. Paths are taken from the script's location, so they can be run from anywhere.

| Folder | Scripts |
|---|---|
| `windows/` | `build.ps1`, `run.ps1`, `launcher.ps1`, `relift.ps1` |
| `linux/` | `build.sh`, `build-gpu.sh`, `run.sh`, `launcher.sh`, `relift.sh` |
| `unix/` | the lifter and the GPU build shared by Linux (and the paused macOS scripts) |
| `mac/` | paused, kept for later: `build.sh`, `build-gpu.sh`, `run.sh`, `launcher.sh`, `relift.sh` |

## macOS (paused)

macOS support is paused. The scripts stay in `mac/`, but CMake stops on Apple unless configured with `-DASCENSION_MACOS=ON`.

| Script | What it does |
|---|---|
| `mac/build.sh [name]` | Apple clang + Ninja into `build/mac`. `RPCS3=1` also links RPCS3's RSX. |
| `mac/build-gpu.sh` | RPCS3's RSX into `work/gpu-build` (MoltenVK). Run before `RPCS3=1`. |
| `mac/run.sh` | Mounts the ISO (`ASCENSION_ISO`) at `work/disc` and opens the game. |
| `mac/launcher.sh [--play]` | The launcher. Music plays through `afplay`. |
| `mac/relift.sh ppu\|spu\|jobmods\|fragments\|all` | Lifts the game into `src/`. |

Needs `brew install cmake ninja sdl2 glslang spirv-cross ffmpeg`, and for the GPU `molten-vk vulkan-loader vulkan-headers`.

## Windows

| Script | What it does |
|---|---|
| `windows/build.ps1 [-Name x]` | `vcvars64` + `ninja -C build\win`, log in `build\logs\build[-x].log`. |
| `windows/run.ps1` | Runs the game, then `tools\log_summary.py`. `-Menu`, `-CaptureAt`, `-Profile`. |
| `windows/launcher.ps1 [-Play]` | The launcher. |
| `windows/snap.ps1 -Out x.png` | Saves the game window as a PNG, even behind other windows. |
| `windows/relift.ps1 jobmods\|fragments` | Re-lifts SPU job modules or fragments. `-Only <sha>` lifts one module. |

## Linux

Same steps as the macOS scripts (`linux/build.sh`, `linux/run.sh`, `linux/launcher.sh`, `linux/relift.sh`, `linux/build-gpu.sh`), into `build/linux`. The disc is an extracted folder at `work/disc`, not a mounted ISO.

Python tools used with the run script (`tools\`):

- `log_summary.py <log>`: fps, the end-of-loading stall, the cinematic's speed, histograms.
- `frame_timeline.py <log>`: the per-frame chain in time.
- `compare_menu.py <dump dir> <out.png>`: the newest frame dump next to the reference shot.
- `profile_threads.py --pid --dbg`: CPU per thread.

Examples:

```powershell
.\scripts\windows\build.ps1 -Name vblank
.\scripts\windows\run.ps1 -Save backup -Seconds 90 -Name cin -Env @{ VDEC_TIMELOG = "1" }
```

```sh
scripts/linux/build.sh
```
