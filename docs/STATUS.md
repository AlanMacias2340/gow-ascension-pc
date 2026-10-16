# Status

Where the experiment stands. Machine: Windows 11, AMD Ryzen 7 5700G, Radeon RX 7600, 16 GB.

| Step | State |
| --- | --- |
| Disc identity | `BCES-01741`, *God of War: Ascension (EU)*, 1.00, firmware 4.31. The image keeps the disc's region table but its sectors are already decrypted. |
| `EBOOT.BIN` | Extracted: 8,586,688 bytes, SHA-256 `0ecbc9c0cd0bf4a493611148e7d7d4a3ba48d7948ecb7969c6e735fca9bb0b9f`, a SELF (version 2, key revision `0x001C`). |
| `EBOOT.BIN` → `EBOOT.ELF` | **Done** (RPCS3): 8,584,256 bytes, SHA-256 `93d94d54ba5dd76ed2d6c86b6558f4f8d2e02355604abca26e0bb71267943be5`. ELF64, big-endian, PowerPC 64, entry OPD `0x808360` (code `0x10410`), TOC `0x81EF60`. No section headers. |
| Imports / NIDs | **Done:** 345 imports from 25 libraries; 308 resolve to a name. About 243 of them are named somewhere in ps3recomp's libraries (an upper bound on what is implemented). |
| Function boundaries | **Done:** 19,199 functions (`find_functions.py`), every `.opd` descriptor a function start; 7,556 OPD entries. Code ends at `0x62C4CC`, right after the import stubs (`0x627954`-`0x62C494`). |
| SPU images | **Done:** only 4 embedded (176 KB, `extract_spu_images.py`), lifted and registered by fingerprint (`build_spu_workloads.py`; 91% of their bytes are code, the rest data in `.text`). The SPURS jobs the game runs most likely come from its data archives (`*.PSARC`): to be looked at. |
| PPU lifting | **Done:** 19,569 functions, 1.8 million lines of C++ (126 MB) in 12 units of 150,000 lines (`--chunk-lines 150000`, so each fits a 16 GB machine), no unknown instruction, 62 jump tables, 676 mid-function entries, 345 import stubs as HLE calls. `--toc 0x81EF60 --code-end 0x62C4CC`; about 20 s. |
| Build | **Done:** `AscensionRecomp.exe`, 55 MB, clang-cl and Ninja with `-j 4`. The project is ps3recomp's `templates/project`, pointed at `../ps3recomp`, `src/recomp` and `src/spu`, plus `dxguid` (the D3D12 backend's DXGI interface IDs). |
| Boot | **The game loop runs.** Run with `PS3_EDGE_ZLIB_HLE=1`. Past the intro loader (which streams its compressed WADs and then frees its memory cleanly), the `Wws_Job` jobs load and run on the SPU, the renderer sets shaders, render targets, textures and blending through the D3D12 backend, and the vblank/flip event loop ticks. No frame on screen confirmed yet. |

## ps3recomp changes

On the branch [`ascension` of the fork `arnaldolima1/ps3recomp`](https://github.com/arnaldolima1/ps3recomp/tree/ascension), the checkout `../ps3recomp` should be on (also kept as `patches/`): `cellSpursInitializeWithAttribute2`, `cellSpursCreateTask2`, `_cellSpursTaskAttribute2Initialize`, `cellSpursCreateTaskset2`, `_cellSpursTasksetAttribute2Initialize`, `cellSpursAttributeEnableSystemWorkload`, `cellGcmMapEaIoAddressWithFlags`; the `sys_lwcond_t` layout; `cellGamePatchCheck`; files past 2 GB; `_cellSpursLFQueuePushBody`; Edge Zlib on the host (with truncated output and the skip offset); the GCM offset tables written through to the guest; the SPU microstep and interpreter fixes; FIFO parks waited on; SPURS2's 32 workloads. The build regenerates the NID table whenever ps3recomp's library sources change (`CMakeLists.txt`).

## Next

- **The frame-end barrier job reads its lock line from EA 0.** With all 19 workloads registered (SPURS2 32-workload support), the frame-end job runs. It is the Wws helper module at VA `0x77C180` (0x900 bytes, header `0x270 / 0x8B0 / C0DEC0DE`, loaded at LS `0x4000`), and it spins at LS `0x41D0`-`0x4204` taking the minimum of six lane progress counters it reads with GETLLAR. The EA it writes to `MFC_EAL` is `r12`, which its own prologue sets to 0 (`fsmbi $12, 0` at LS `0x413C`, the same bytes as on disc), so it reads zeros and waits forever. Meanwhile the PPU waits on the same kind of progress at `0x12600530` (`func_00466E28`). The module is full of `brsl $2 / ai $2,$2,8 / bi $2` hook slots that the policy module presumably rewrites, and one sits right before the GETLLAR: find what the PM patches into them (or what sets `r12`) when it loads this module.
- Diagnose with `YDKJ_SPU_TRACE=1 SPU_STEPCAP=30000000`: the dump shows the loop code, `MFC_EAH`, the line buffer and the registers.
- The idle `Wws_Job` policy module logs every poll: quiet it before longer runs.

## Found so far

- **Edge Zlib:** the queue the first SPU task serves is Edge's zlib inflate queue (`edgezlib_inflate_queue.cpp`, the game's own assert names it). Its request has the layout the Twisted Metal port mapped (+0x00 destination, +0x0C source, +0x10 compressed size, +0x14 in-place buffer, +0x18/+0x24 output size, +0x28 busy), and the queue element carries the same. Inflating on the host, as that port does, unblocks the boot.
- **The `Wws_Job` policy module** is raw SPU code in the executable (12288 bytes at `0x77CA80`, FNV-1a-64 `0xC8D774963A96DCF2`). `tools/extract_spu_pm.py` extracts it and wraps it as an SPU ELF at LS `0xA00` into `meta/spu/`; `build_spu_workloads.py` then lifts it (194 functions) and registers it under that fingerprint, and all fifteen workloads resolve.

- **`sys_lwcond_t` layout (ps3recomp bug):** the runtime wrote the lwmutex as a 64-bit EA at +0x00 and the queue id at +0x08; the PS3 structure is 8 bytes (be32 lwmutex, be32 id). The game reads the first word before waiting, found 0 and never waited, so its FIOS threads deadlocked and no file was opened. Fixed on the fork.
- **Files past 2 GB (ps3recomp bug, Windows):** `cellFsLseek`, `cellFsFstat` and `cellFsStat` used `long` and `struct stat`, 32 bits on Windows. `RESOURCES.PSARC` (2.1 GB) failed to mount with -139 and the init gave up. Fixed with 64-bit helpers.
- **`_cellSpursLFQueuePushBody`** was missing: the PPU's first message to its SPU task never arrived. Implemented on the ring model ps3recomp derived from another title's consumer, under the lock-line lock; the message arrives and wakes the task, but the model does not match this game's consumer (see Next).
- **How the init failure was found:** a temporary `fprintf` after every call in the lifted `func_002AC3D8` (generated code, not kept) showed the archive-mount call returning -139 on the fourth archive.

- **Edge Zlib streaming:** the queue element has an output skip at +0x24 (also the low half of +0x18). The intro loader reads a compressed WAD as a 64-byte chunk header, then its payload, then the next header, each time inflating the same stream and skipping what it already has. Ignored, the first header (`DC_WAD_R_FX`) came back forever, the loader freed its buffers through the wrong heap (`Ice::Render::UnmapMainMemory` on addresses it never mapped, the renderer's memory table driven to -1) and the GCM IO mapping was destroyed: that was the old "iooffset == -1 / MemTable entry not found" stop.
- **GCM offset tables:** `cellGcmGetOffsetTable` gives the game a guest copy that map/unmap never updated. Now written through.
- **WWS interrupt handler:** the job manager acknowledges a DMA list stall from an SPU interrupt whose handler (LS `0xA2C`) builds a register-save stub at `0x3FEC0` at run time. Two runtime bugs killed it: the SMC microstep computed `lqa`/`stqa` addresses as `I16 << 4` (the stub came from the wrong template), and after handing an instruction to the interpreter it did not dispatch back into lifted code, so the policy module quit. The jobs then ran into `dfs` and other ops the interpreter lacked.

- **SPURS2 has 32 workloads.** The runtime stopped at 16, so `EDGE1`, `EDGE2` and `RsxSync` (wid 16-18) were never added. The frame-slot counters at `0x99AAC0` (released by the frame-end job) stayed at 1 and the render thread waited forever. Fixed: the second set of instance fields is used for wid 16-31.

## Gaps the imports show

- **SPURS, second generation:** `cellSpursCreateTaskset2`, `cellSpursCreateTask2`, `cellSpursJoinTask2`, `cellSpursInitializeWithAttribute2`, workload flags, the lock-free queue (`_cellSpursLFQueuePushBody`), 14 of the 45 SPURS imports.
- **PRX loading:** `sys_prx_load_module` and its variants; the game loads modules of its own at run time.
- **Asynchronous file reads** (`cellFsAio*`) and **memory mapping** (`sys_mmapper_*`).
- About 140 imports are network and online (`sceNp*`, `cellHttp`, `cellSsl`, `sys_net`, `cellVoice`, `cellNetCtl`): multiplayer, answered offline.

ps3recomp: `master` at `a2c20108` (v0.14.0).

## What to expect

Of the ports built on ps3recomp, Twisted Metal (2012) is among the furthest: its menus and in-match HUD draw, its 3D world does not yet, held up by SPURS jobs and the Edge geometry ring. Ascension uses the same kind of SPU work, and more of it. The first goal here is the pipeline end to end: a decrypted ELF, its imports and functions, lifted C++ that compiles, and an executable that starts.
