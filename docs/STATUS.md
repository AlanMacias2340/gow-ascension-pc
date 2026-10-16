# Status

Where the experiment stands. Machine: Windows 11, AMD Ryzen 7 5700G, Radeon RX 7600, 16 GB.

| Step | State |
| --- | --- |
| Disc identity | `BCES-01741`, *God of War: Ascension (EU)*, 1.00, firmware 4.31. The image keeps the disc's region table but its sectors are already decrypted. |
| `EBOOT.BIN` | Extracted: 8,586,688 bytes, SHA-256 `0ecbc9c0cd0bf4a493611148e7d7d4a3ba48d7948ecb7969c6e735fca9bb0b9f`, a SELF (version 2, key revision `0x001C`). |
| `EBOOT.BIN` → `EBOOT.ELF` | **Waiting** for the decryption (RPCS3, or `tools/decrypt_self.py` with the owner's key file). |
| Imports / NIDs | Not started. |
| Function boundaries | Not started. |
| SPU images | Not started. |
| PPU lifting | Not started. |
| Build | Not started. |
| Boot | Not started. |

ps3recomp: `master` at `a2c20108` (v0.14.0).

## What to expect

Of the ports built on ps3recomp, Twisted Metal (2012) is among the furthest: its menus and in-match HUD draw, its 3D world does not yet, held up by SPURS jobs and the Edge geometry ring. Ascension uses the same kind of SPU work, and more of it. The first goal here is the pipeline end to end: a decrypted ELF, its imports and functions, lifted C++ that compiles, and an executable that starts.
