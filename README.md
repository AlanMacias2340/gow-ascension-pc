<div align="center">

# Ascension

**God of War: Ascension (PS3), an experiment in recompiling it to run natively on a PC.**

[![Status](https://img.shields.io/badge/status-experiment-lightgrey)](docs/STATUS.md)
[![Windows](https://img.shields.io/badge/Windows-10%2F11%20x64-0078D4)](#building-from-source)
[![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-000000)](#building-from-source)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**English** · [Português (Brasil)](README.pt-BR.md)

</div>

---

Ascension is a static recompilation experiment: the game's PowerPC (PPU) and SPU code is translated ahead of time into C++ and compiled for your machine, on top of [ps3recomp](https://github.com/sp00nznet/ps3recomp)'s runtime and system libraries. It is a sibling of [Sparta](https://github.com/arnaldolima1/gow-ghost-of-sparta-pc) and [Olympus](https://github.com/arnaldolima1/gow-chains-of-olympus-pc), which do the same for the PSP games on PortableKit.

> [!WARNING]
> **An experiment, for curiosity.** Nothing runs yet. The PS3 is far harder than the PSP: the game leans on six SPUs (SPURS jobs, Edge geometry, post-processing), and the most advanced ps3recomp ports draw their menus but not yet their 3D worlds. Windows and macOS (Apple Silicon); no Android.

> [!IMPORTANT]
> **No game data is included.** You need your own copy of the game: the **European release, `BCES-01741`** (1.00), as a disc image of your own disc. Nobody here can give you a copy, keys, or tell you where to get them. Ascension is not affiliated with Sony Interactive Entertainment or Santa Monica Studio.

## Status

See [docs/STATUS.md](docs/STATUS.md).

## Building from source

The layout this repository expects, with ps3recomp checked out beside it:

```
ascension-recomp/
  ps3recomp/    https://github.com/arnaldolima1/ps3recomp, branch ascension-v0.15
                (or https://github.com/sp00nznet/ps3recomp v0.15.0 with patches/ applied)
  ascension/    this repository
  work/         your EBOOT.BIN and what is made from it (never committed)
```

1. **The executable.** Take `PS3_GAME/USRDIR/EBOOT.BIN` from your disc image and decrypt it to `EBOOT.ELF`, either with RPCS3 (*Utilities › Decrypt PS3 Binaries*, with the console's firmware installed) or with `python tools/decrypt_self.py EBOOT.BIN -o EBOOT.ELF --keys <your scetool key file>`. Its key revision is `0x001C`.
2. **Analysis and lifting** with ps3recomp's pipeline (`elf_parser.py`, `find_functions.py`, `extract_spu_images.py`, `ppu_loader.py`, `ppu_lifter.py`): the steps are in ps3recomp's [Getting Started](https://github.com/sp00nznet/ps3recomp/blob/master/docs/GETTING_STARTED.md), and this repository's scripts will follow them.
3. **Build** with CMake and Ninja: on Windows with Visual Studio 2022 (clang-cl); on macOS with Apple clang (the Xcode command-line tools) and `brew install cmake ninja sdl2 glslang spirv-cross`. The Python tools need 3.10 or newer.
4. **Run.** On macOS, `tools/run_mac.sh` mounts the disc image at `work/disc` and runs the game in a window (`ASCENSION_ISO=<path to the .iso>` the first time).

## Credits

- [ps3recomp](https://github.com/sp00nznet/ps3recomp) by sp00nznet and contributors: the recompiler, runtime and system libraries.
- `tools/decrypt_self.py` comes from [Twisted Metal](https://github.com/sp00nznet/twistedmetal)'s port (MIT), adapted to read newer scetool key files.
- God of War is a trademark of Sony Interactive Entertainment. This is an unofficial project.

## License

MIT: see [LICENSE](LICENSE). It covers this repository's code only, not the game.
