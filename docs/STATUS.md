# Status

Where the experiment stands. Machine: Windows 11, AMD Ryzen 7 5700G, Radeon RX 7600, 16 GB.

| Step | State |
| --- | --- |
| Disc identity | `BCES-01741`, *God of War: Ascension (EU)*, 1.00, firmware 4.31. The image keeps the disc's region table but its sectors are already decrypted. |
| `EBOOT.BIN` | Extracted: 8,586,688 bytes, SHA-256 `0ecbc9c0cd0bf4a493611148e7d7d4a3ba48d7948ecb7969c6e735fca9bb0b9f`, a SELF (version 2, key revision `0x001C`). |
| `EBOOT.BIN` → `EBOOT.ELF` | **Done** (RPCS3): 8,584,256 bytes, SHA-256 `93d94d54ba5dd76ed2d6c86b6558f4f8d2e02355604abca26e0bb71267943be5`. ELF64, big-endian, PowerPC 64, entry OPD `0x808360` (code `0x10410`), TOC `0x81EF60`. No section headers. |
| Imports / NIDs | **Done:** 345 imports from 25 libraries; 308 resolve to a name. About 243 of them are named somewhere in ps3recomp's libraries (an upper bound on what is implemented). |
| Function boundaries | **Done:** 19,199 functions (`find_functions.py`), every `.opd` descriptor a function start; 7,556 OPD entries. Code ends at `0x62C4CC`, right after the import stubs (`0x627954`-`0x62C494`). |
| SPU images | **Done:** only 4 embedded (176 KB, `extract_spu_images.py`). The SPURS jobs the game runs most likely come from its data archives (`*.PSARC`): to be looked at. |
| PPU lifting | Next: `ppu_lifter.py` with `--toc 0x81EF60 --code-end 0x62C4CC`. |
| Build | Not started: the project (CMake, boot scaffold) comes from ps3recomp's `templates/project`. |
| Boot | Not started. |

## Gaps the imports show

- **SPURS, second generation:** `cellSpursCreateTaskset2`, `cellSpursCreateTask2`, `cellSpursJoinTask2`, `cellSpursInitializeWithAttribute2`, workload flags, the lock-free queue (`_cellSpursLFQueuePushBody`), 14 of the 45 SPURS imports.
- **PRX loading:** `sys_prx_load_module` and its variants; the game loads modules of its own at run time.
- **Asynchronous file reads** (`cellFsAio*`) and **memory mapping** (`sys_mmapper_*`).
- About 140 imports are network and online (`sceNp*`, `cellHttp`, `cellSsl`, `sys_net`, `cellVoice`, `cellNetCtl`): multiplayer, answered offline.

ps3recomp: `master` at `a2c20108` (v0.14.0).

## What to expect

Of the ports built on ps3recomp, Twisted Metal (2012) is among the furthest: its menus and in-match HUD draw, its 3D world does not yet, held up by SPURS jobs and the Edge geometry ring. Ascension uses the same kind of SPU work, and more of it. The first goal here is the pipeline end to end: a decrypted ELF, its imports and functions, lifted C++ that compiles, and an executable that starts.
