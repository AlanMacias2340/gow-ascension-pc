<div align="center">

<img src="packaging/icon.png" alt="Ícone do Ascension" width="128">

# Ascension

**God of War: Ascension (PS3), um experimento de recompilação para rodar nativamente no PC.**

[![Status](https://img.shields.io/badge/status-experimento-lightgrey)](docs/STATUS.pt-BR.md)
[![Release](https://img.shields.io/badge/release-ainda%20n%C3%A3o-lightgrey)](#onde-estamos)
[![Windows](https://img.shields.io/badge/Windows-10%2F11%20x64-0078D4)](#compilando-o-código)
[![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-000000)](#compilando-o-código)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)](LICENSE)

[English](README.md) · **Português (Brasil)**

</div>

---

O Ascension é um experimento de recompilação estática: o código PowerPC (PPU) e de SPU do jogo é traduzido antecipadamente para C++ e compilado para a sua máquina, sobre o runtime e as bibliotecas de sistema do [ps3recomp](https://github.com/sp00nznet/ps3recomp). É irmão do [Sparta](https://github.com/arnaldolima1/gow-ghost-of-sparta-pc) e do [Olympus](https://github.com/arnaldolima1/gow-chains-of-olympus-pc), que fazem o mesmo com os jogos de PSP sobre o PortableKit.

> [!WARNING]
> **Um experimento, por curiosidade: ainda não dá para jogar.** O jogo inicia e chega aos primeiros menus, e só. O PS3 é bem mais difícil que o PSP: o jogo depende de seis SPUs (jobs SPURS, geometria Edge, pós-processamento), e nenhum port do ps3recomp desenha o mundo 3D ainda. Windows e macOS (Apple Silicon); Android fica de fora.

> [!IMPORTANT]
> **Nenhum dado do jogo está incluído.** Você precisa da sua própria cópia: a **versão europeia, `BCES-01741`** (1.00), como imagem do seu próprio disco. Ninguém aqui pode te dar uma cópia ou chaves, nem dizer onde conseguir. O Ascension não tem ligação com a Sony Interactive Entertainment ou a Santa Monica Studio.

## Onde estamos

**Ainda não há release**: para testar, compile a partir do código (abaixo). Em outubro de 2026, no Windows:

- **Inicia e mostra as telas de abertura**: o texto legal, "Sony Computer Entertainment presents", o logo da Santa Monica Studio e o aviso de jogo online.
- **Carrega e chega aos primeiros menus**: a escolha de idioma, a tela de ajuste da imagem e a de brilho, desenhadas pelos próprios shaders do jogo, na fonte bronze dele. No primeiro uso ele grava o save do sistema.
- **Depois dos menus vai para uma tela preta**, que é o próximo ponto a investigar. O controle ainda não foi testado, e roda devagar: o trabalho das SPUs é várias vezes mais lento que num PS3.

Chegar até aqui levou 21 commits de correções no runtime e no renderizador do ps3recomp, todos num [fork](https://github.com/arnaldolima1/ps3recomp/tree/ascension-v0.15) e guardadas aqui em `patches/`: o SPURS de segunda geração (32 workloads, tasksets criados pelas SPUs), a sincronização GPU/SPU (o pós-processo nas SPUs, os semáforos do GCM e os parks do FIFO), o renderizador (a textura da fonte, a saída sRGB, as derivadas nos shaders) e um bug do lifter que corrompia um heap. A história completa, com os próximos passos, está em [docs/STATUS.pt-BR.md](docs/STATUS.pt-BR.md).

## Compilando o código

A estrutura que este repositório espera, com o ps3recomp ao lado:

```
ascension-recomp/
  ps3recomp/    https://github.com/arnaldolima1/ps3recomp, branch ascension-v0.15
                (ou https://github.com/sp00nznet/ps3recomp v0.15.0 com os patches/ aplicados)
  ascension/    este repositório
  work/         o seu disco e EBOOT, e o que é feito deles (nunca vai para o git)
```

1. **O executável.** Pegue o `PS3_GAME/USRDIR/EBOOT.BIN` da sua imagem de disco e decripte para `EBOOT.ELF`, com o RPCS3 (*Utilities › Decrypt PS3 Binaries*, com o firmware do console instalado) ou com `python tools/decrypt_self.py EBOOT.BIN -o EBOOT.ELF --keys <seu arquivo de chaves do scetool>`. A revisão de chave dele é `0x001C`.
2. **Análise e tradução** com o pipeline do ps3recomp (`elf_parser.py`, `find_functions.py`, `extract_spu_images.py`, `ppu_loader.py`, `ppu_lifter.py`): os passos estão no [Getting Started](https://github.com/sp00nznet/ps3recomp/blob/master/docs/GETTING_STARTED.md) do ps3recomp, e o comando de tradução que este jogo usa está em [docs/STATUS.pt-BR.md](docs/STATUS.pt-BR.md#o-pipeline). Use o lifter da v0.15: um mais antigo corrompe o heap do jogo.
3. **Build** com CMake e Ninja: no Windows com o Visual Studio 2022 (clang-cl); no macOS com o Apple clang (as ferramentas de linha de comando do Xcode) e `brew install cmake ninja sdl2 glslang spirv-cross ffmpeg`, configurado com `-DPS3RECOMP_FFMPEG_RUNTIME=ON` para o `cellVdec` decodificar a cinemática de abertura (MPEG-2). As ferramentas em Python pedem a versão 3.10 ou mais nova. O código gerado é grande: um build do zero leva de 20 a 40 minutos e pede 16 GB de memória.
4. **Rodando.** Extraia o seu disco em `work/disc` (de modo que exista `work/disc/PS3_GAME/USRDIR`) e coloque o `EBOOT.ELF` ao lado do `EBOOT.BIN` ali. No Windows, a partir desta pasta: `build\win\AscensionRecomp.exe ..\work\disc\PS3_GAME\USRDIR\EBOOT.ELF`. No macOS, o `tools/run_mac.sh` monta a imagem do disco em `work/disc` e abre o jogo numa janela (na primeira vez, `ASCENSION_ISO=<caminho do .iso>`). Os saves ficam em `gamedata/dev_hdd0`.

## Créditos

- [ps3recomp](https://github.com/sp00nznet/ps3recomp), de sp00nznet e colaboradores: o recompilador, o runtime e as bibliotecas de sistema.
- O `tools/decrypt_self.py` veio do port do [Twisted Metal](https://github.com/sp00nznet/twistedmetal) (MIT), adaptado para ler os arquivos de chaves do scetool mais novos.
- God of War é marca registrada da Sony Interactive Entertainment. Este é um projeto não oficial.

## Licença

MIT: veja [LICENSE](LICENSE). Vale só para o código deste repositório, não para o jogo.
