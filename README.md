<div align="center">

<img src="packaging/icon.png" alt="Ícone do Ascension" width="128">

# Ascension

**God of War: Ascension (PS3), recompilado para rodar nativamente no PC.**

[![Status](https://img.shields.io/badge/status-experimento-lightgrey)](docs/MILESTONES.md)
[![Release](https://img.shields.io/badge/release-ainda%20n%C3%A3o-lightgrey)](#onde-estamos)
[![Windows](https://img.shields.io/badge/Windows-10%2F11%20x64-0078D4)](#compilando)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)](LICENSE)

**Português (Brasil)** · [English](docs/README.en.md)

</div>

---

O Ascension traduz o código do jogo, do processador principal (PPU) e dos SPUs do PS3, para C++ e o compila para o seu PC, sobre o runtime do [ps3recomp](https://github.com/sp00nznet/ps3recomp). Não é um emulador: é o próprio jogo, recompilado. É irmão do [Sparta](https://github.com/arnaldolima1/gow-ghost-of-sparta-pc) e do [Olympus](https://github.com/arnaldolima1/gow-chains-of-olympus-pc), que fazem o mesmo com os God of War de PSP.

> [!WARNING]
> **Um experimento: ainda não dá para jogar do começo ao fim.** O jogo chega ao primeiro nível, mas ainda lento (~16-17 fps). Só Windows por enquanto (o suporte ao macOS está pausado).

> [!IMPORTANT]
> **Nenhum dado do jogo está incluído.** Você precisa da sua própria cópia, a **versão europeia `BCES-01741`** (1.00), tirada do seu disco. Ninguém aqui pode te dar o jogo ou chaves. Projeto de fãs, sem ligação com a Sony Interactive Entertainment ou a Santa Monica Studio.

## Onde estamos

Outubro de 2026, no Windows:

- **Do boot ao primeiro nível:** telas de abertura, carregamento, menus de primeiro uso, cinemática de abertura (imagem e som sincronizados), menu principal e o primeiro nível, com o Kratos acorrentado.
- **Dois renderizadores:** o RSX do [RPCS3](https://github.com/RPCS3/rpcs3) (Vulkan ou OpenGL), que desenha o jogo corretamente, e o *live draw* próprio do projeto (D3D12).
- **Desempenho:** menu principal a ~30 fps; o primeiro nível a ~16-17 fps (era ~9). O limite é o código das SPUs recompilado, não a placa de vídeo: o job de geometria por draw (módulo 218) é o maior custo, e está sendo reescrito como código nativo, validado contra jobs gravados do jogo, sem precisar rodá-lo.
- **Launcher** em português, inglês e espanhol, com vídeo, controles, idioma, legendas e mods; **português do Brasil** com vozes e textos, montado a partir do seu disco americano.

Ainda não há release. Os marcos estão em [docs/MILESTONES.md](docs/MILESTONES.md).

## Jogando

Com o jogo compilado (abaixo), abra o launcher:

```powershell
.\scripts\windows\launcher.ps1
```

<p align="center"><img src="docs/images/launcher-home.jpg" alt="O launcher do Ascension" width="760"></p>

JOGAR abre o jogo dentro da própria janela do launcher.

- **Vídeo:** renderizador (RPCS3 Vulkan ou OpenGL, live draw), resolução interna e filtro anisotrópico (RPCS3), janela ou tela cheia (F11 ou Alt+Enter também alternam durante o jogo), tamanho da janela, proporção, escala da imagem, sincronização vertical, contador de FPS.
- **Controles:** abas para teclado e mouse (duas teclas por comando, clique e aperte a nova) e para o controle (qual botão faz cada um, zona morta). Padrão: WASD anda, setas esquivam, Espaço/J/I/L ou o mouse nos botões, Shift defende, Esc ou Enter pausa. Teclado, mouse e controle funcionam juntos.
- **Jogo:** idioma (inglês, português, espanhol, francês, alemão, italiano, russo, polonês, turco) e legendas, que valem mesmo depois do primeiro uso; backup automático dos saves.
- **Mods:** liga, desliga e ordena. Vem com **Pular intro** (direto ao carregamento, sem as telas de abertura); o botão **Criar mod PT-BR** monta o português do Brasil a partir da imagem do seu disco americano. Os mods incluídos são receitas: o launcher as aplica aos arquivos do seu disco, sem trazer nada do jogo.

<p align="center"><img src="docs/images/launcher-mods.jpg" alt="A página de mods" width="760"></p>

## Compilando

```
ascension-recomp/
  ps3kit/       o runtime e o recompilador (fork do ps3recomp, com as mudanças deste projeto)
  ascension/    este repositório
  work/         o seu disco e o que sai dele (nunca vai para o git)
```

1. **Disco:** extraia a sua imagem em `work/disc` e decripte `PS3_GAME/USRDIR/EBOOT.BIN` para `EBOOT.ELF` (com o RPCS3, ou `tools/decrypt_self.py` e o seu arquivo de chaves).
2. **Tradução:** gere o código C++ com o recompilador; os scripts de `scripts/` cobrem cada etapa (veja [scripts/README.md](scripts/README.md)).
3. **Build:** Visual Studio 2022 (clang-cl), CMake e Ninja, com `.\scripts\windows\build.ps1`; o renderizador do RPCS3 se compila antes com `.\scripts\windows\build-gpu.ps1` (MSVC e Vulkan SDK). As configurações da máquina ficam num `.env` local. Um build do zero leva de 20 a 40 minutos e pede 16 GB de memória.

Os saves ficam em `gamedata/dev_hdd0`.

## Créditos

- [ps3recomp](https://github.com/sp00nznet/ps3recomp), de sp00nznet e colaboradores: o recompilador, o runtime e as bibliotecas de sistema.
- [RPCS3](https://github.com/RPCS3/rpcs3): o código do RSX usado como renderizador (GPL-2.0; um build com ele fica sob a GPL-2.0).
- `tools/decrypt_self.py`, do port do [Twisted Metal](https://github.com/sp00nznet/twistedmetal) (MIT).
- O launcher segue o estilo do de [gow3_pc](https://github.com/FelipePrado0/gow3_pc); fonte Cinzel (SIL Open Font License).
- God of War é marca registrada da Sony Interactive Entertainment.

## Licença

MIT: veja [LICENSE](LICENSE). Vale só para o código deste repositório, não para o jogo.
