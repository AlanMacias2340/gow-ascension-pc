<div align="center">

# Ascension

**God of War: Ascension (PS3), um experimento de recompilação para rodar nativamente no PC.**

[![Status](https://img.shields.io/badge/status-experimento-lightgrey)](docs/STATUS.md)
[![Windows](https://img.shields.io/badge/Windows-10%2F11%20x64-0078D4)](#compilando-o-código)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)](LICENSE)

[English](README.md) · **Português (Brasil)**

</div>

---

O Ascension é um experimento de recompilação estática: o código PowerPC (PPU) e de SPU do jogo é traduzido antecipadamente para C++ e compilado para a sua máquina, sobre o runtime e as bibliotecas de sistema do [ps3recomp](https://github.com/sp00nznet/ps3recomp). É irmão do [Sparta](https://github.com/arnaldolima1/gow-ghost-of-sparta-pc) e do [Olympus](https://github.com/arnaldolima1/gow-chains-of-olympus-pc), que fazem o mesmo com os jogos de PSP sobre o PortableKit.

> [!WARNING]
> **Um experimento, por curiosidade.** Nada roda ainda. O PS3 é bem mais difícil que o PSP: o jogo depende de seis SPUs (jobs SPURS, geometria Edge, pós-processamento), e os ports mais avançados do ps3recomp desenham os menus, mas ainda não o mundo 3D. Só Windows; Android fica de fora.

> [!IMPORTANT]
> **Nenhum dado do jogo está incluído.** Você precisa da sua própria cópia: a **versão europeia, `BCES-01741`** (1.00), como imagem do seu próprio disco. Ninguém aqui pode te dar uma cópia ou chaves, nem dizer onde conseguir. O Ascension não tem ligação com a Sony Interactive Entertainment ou a Santa Monica Studio.

## Situação

Veja [docs/STATUS.md](docs/STATUS.md) (em inglês).

## Compilando o código

A estrutura que este repositório espera, com o ps3recomp ao lado:

```
ascension-recomp/
  ps3recomp/    https://github.com/sp00nznet/ps3recomp
  ascension/    este repositório
  work/         o seu EBOOT.BIN e o que é feito dele (nunca vai para o git)
```

1. **O executável.** Pegue o `PS3_GAME/USRDIR/EBOOT.BIN` da sua imagem de disco e decripte para `EBOOT.ELF`, com o RPCS3 (*Utilities › Decrypt PS3 Binaries*, com o firmware do console instalado) ou com `python tools/decrypt_self.py EBOOT.BIN -o EBOOT.ELF --keys <seu arquivo de chaves do scetool>`. A revisão de chave dele é `0x001C`.
2. **Análise e tradução** com o pipeline do ps3recomp (`elf_parser.py`, `find_functions.py`, `extract_spu_images.py`, `ppu_loader.py`, `ppu_lifter.py`): os passos estão no [Getting Started](https://github.com/sp00nznet/ps3recomp/blob/master/docs/GETTING_STARTED.md) do ps3recomp, e os scripts deste repositório vão segui-los.
3. **Build** com Visual Studio 2022 (clang-cl), CMake e Ninja.

## Créditos

- [ps3recomp](https://github.com/sp00nznet/ps3recomp), de sp00nznet e colaboradores: o recompilador, o runtime e as bibliotecas de sistema.
- O `tools/decrypt_self.py` veio do port do [Twisted Metal](https://github.com/sp00nznet/twistedmetal) (MIT), adaptado para ler os arquivos de chaves do scetool mais novos.
- God of War é marca registrada da Sony Interactive Entertainment. Este é um projeto não oficial.

## Licença

MIT: veja [LICENSE](LICENSE). Vale só para o código deste repositório, não para o jogo.
