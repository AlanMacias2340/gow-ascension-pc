# scripts

One folder per platform. Paths are taken from the script's location, so they can be run from anywhere. The build, run and relift scripts need a local `.env` in the repository root (never committed) with the machine's build settings.

| Folder | Scripts |
|---|---|
| `windows/` | `build.ps1`, `build-gpu.ps1`, `run.ps1`, `launcher.ps1`, `relift.ps1`, `snap.ps1`, `test-*.ps1` (`env.ps1` reads `.env`) |
| `linux/` | `build.sh`, `build-gpu.sh`, `run.sh`, `launcher.sh`, `relift.sh` |
| `unix/` | the lifter, the GPU build and `env.sh` (reads `.env`), shared by Linux (and the paused macOS scripts) |
| `mac/` | paused, kept for later: `build.sh`, `build-gpu.sh`, `run.sh`, `launcher.sh`, `relift.sh` |

## macOS (paused)

macOS support is paused. The scripts stay in `mac/`, but CMake stops on Apple unless configured with `-DASCENSION_MACOS=ON`.

| Script | What it does |
|---|---|
| `mac/build.sh [name]` | Apple clang + Ninja into `build/mac`. `CONFIGURE=1` runs CMake again. |
| `mac/build-gpu.sh` | RPCS3's RSX library (MoltenVK). |
| `mac/run.sh` | Mounts the ISO (`ASCENSION_ISO`) at `work/disc` and opens the game. |
| `mac/launcher.sh [--play]` | The launcher. Music plays through `afplay`. |
| `mac/relift.sh ppu\|spu\|jobmods\|fragments\|all` | Lifts the game into `src/`. |

Needs `brew install cmake ninja sdl2 glslang spirv-cross ffmpeg`, and for the GPU `molten-vk vulkan-loader vulkan-headers`.

## Windows

| Script | What it does |
|---|---|
| `windows/build.ps1 [-Name x] [-Configure]` | CMake (the first time, or `-Configure`) and `ninja -C build\win`, log in `build\logs\build[-x].log`. |
| `windows/build-gpu.ps1 [-Configure]` | RPCS3's RSX library with MSVC. |
| `windows/run.ps1` | Runs the game for `-Seconds` (0: until closed), then `tools\log_summary.py`. `-Save fresh\|backup\|keep`, `-Menu` (main menu in ~15 s), `-Level` (first level in ~100 s), `-Rpcs3`, `-CaptureAt`, `-Profile`. |
| `windows/launcher.ps1 [-Play]` | The launcher. |
| `windows/snap.ps1 -Out x.png` | Saves the game window as a PNG, even behind other windows. |
| `windows/relift.ps1 jobmods\|fragments` | Re-lifts SPU job modules or fragments. `-Only <sha>` lifts one module. |
| `windows/test-fifo.ps1` | FIFO drain and recovery regression, headless. |
| `windows/test-spu-launch.ps1`, `test-spu-resolver.ps1` | SPU launch hooks and resolver tests, without the game. |

## Linux

`linux/build.sh`, `linux/build-gpu.sh`, `linux/run.sh`, `linux/launcher.sh` and `linux/relift.sh` build into `build/linux` and work like their macOS counterparts. The disc is an extracted folder at `work/disc`, not a mounted ISO.

## Tools

Python tools in `tools/`:

- `log_summary.py <log>`: fps (`[perf]` lines, the stable-window median), the end-of-loading stall, the cinematic's speed, FIFO errors.
- `frame_timeline.py <log>`: the per-frame chain in time.
- `compare_menu.py <dump dir> <out.png>`: the newest frame dump next to the reference shot.
- `profile_threads.py --pid --dbg`: CPU per thread.
- `decrypt_self.py`: `EBOOT.BIN` to `EBOOT.ELF`, with your keys file.
- `make_ptbr_mod.py`: the PT-BR mod from a US disc (the launcher's Mods page runs it).
- `psarc_replace.py`: reads and rewrites PSARC archives (the launcher's mod recipes).

Examples:

```powershell
.\scripts\windows\build.ps1 -Name vblank
.\scripts\windows\run.ps1 -Save backup -Seconds 90 -Name cin -Env @{ VDEC_TIMELOG = "1" }
```

```sh
scripts/linux/build.sh
```
