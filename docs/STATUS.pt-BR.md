# Situação

Onde o experimento está, em 16/10/2026. Máquinas: Windows 11, AMD Ryzen 7 5700G, Radeon RX 7600, 16 GB; e um Mac, Apple M4, 16 GB, macOS 26. In English: [STATUS.md](STATUS.md) (com o diário técnico completo).

## Onde estamos

**No Windows o jogo inicia, mostra as telas de abertura, carrega e chega aos primeiros menus**: a escolha de idioma, a tela de ajuste da imagem e a de brilho, desenhadas pelos próprios shaders do jogo, na fonte bronze dele. No primeiro uso ele grava o save do sistema (`BCES01741-SYSDATA`). A resposta ao controle ainda não foi testada, e depois dos menus o jogo vai para uma tela preta, que é o próximo ponto a investigar. Está lento: o trabalho das SPUs roda várias vezes mais devagar que num PS3. Não há release; para testar, compile a partir do código.

No macOS as mesmas telas de abertura já eram desenhadas pelo Metal antes da nova tradução do código (abaixo); o build do Mac precisa da mesma retradução (com o lifter da v0.15 do ps3recomp) para chegar ao mesmo ponto.

## Marcos

| Data | Marco |
| --- | --- |
| 15/10/2026 | `EBOOT.BIN` decriptado, imports e funções encontrados, 1,8 milhão de linhas de C++ geradas e compiladas; o executável inicia. |
| 15/10/2026 | Passa pelas verificações do sistema e monta os arquivos do jogo (layout do `sys_lwcond_t`, arquivos acima de 2 GB, Edge Zlib no host). |
| 15/10/2026 | Telas de abertura: o texto legal, "Sony Computer Entertainment presents", Santa Monica Studio, o aviso de jogo online (motor live draw). O mesmo no macOS, pelo Metal. |
| 16/10/2026 | O renderizador principal passa do segundo frame: SPURS2 (32 workloads, tempArea, flags1), o pós-processo nas SPUs, a sincronização GPU/SPU (`GCM_SEMA_ACQUIRE`, `GCM_PARK_SPU_HOLD_MS`, `SPURS_READY_LEVEL`). |
| 16/10/2026 | Código retraduzido com o lifter da v0.15 (um bug de spill/reload corrompia um heap no frame ~12): a tela de carregamento. |
| 16/10/2026 | Passa da tela de carregamento (tasksets SPURS: tasks iniciadas em dobro, tamanho e event flags do Taskset2, tasks criadas pela SPU). |
| 16/10/2026 | Os menus ficam legíveis: atlas de fonte X16, sRGB no framebuffer e gamma de textura, `DDX`/`DDY` nos shaders, no motor live draw. |

## O pipeline

| Etapa | Situação |
| --- | --- |
| Identidade do disco | `BCES-01741`, *God of War: Ascension (EU)*, 1.00, firmware 4.31. A imagem mantém a tabela de regiões do disco, mas os setores já estão decriptados. |
| `EBOOT.BIN` | Extraído: 8.586.688 bytes, SHA-256 `0ecbc9c0cd0bf4a493611148e7d7d4a3ba48d7948ecb7969c6e735fca9bb0b9f`, um SELF (versão 2, revisão de chave `0x001C`). |
| `EBOOT.BIN` → `EBOOT.ELF` | **Feito** (RPCS3): 8.584.256 bytes, SHA-256 `93d94d54ba5dd76ed2d6c86b6558f4f8d2e02355604abca26e0bb71267943be5`. ELF64, big-endian, PowerPC 64, OPD de entrada `0x808360` (código `0x10410`), TOC `0x81EF60`. Sem section headers. |
| Imports / NIDs | **Feito:** 345 imports de 25 bibliotecas; 308 com nome. Cerca de 243 aparecem nas bibliotecas do ps3recomp (um teto para o que está implementado). |
| Limites das funções | **Feito:** 19.199 funções (`find_functions.py`), cada descritor `.opd` o início de uma; 7.556 entradas OPD. O código termina em `0x62C4CC`, logo depois dos stubs de import (`0x627954`-`0x62C494`). |
| Imagens SPU | **Feito:** 4 embutidas (176 KB, `extract_spu_images.py`) mais o policy module `Wws_Job` (`tools/extract_spu_pm.py`), traduzidas e registradas por fingerprint (`build_spu_workloads.py`). |
| Tradução do PPU | **Feita** com o lifter da v0.15: 19.570 funções, 1,8 milhão de linhas de C++ (126 MB) em 12 unidades de 150.000 linhas (cada uma cabe numa máquina de 16 GB), 62 jump tables, 676 entradas no meio de funções, 345 stubs de import como chamadas HLE. `python ps3recomp/tools/ppu_lifter.py work/input/EBOOT.elf --functions meta/functions.json --hle-stubs meta/EBOOT.imports.json --toc 0x81EF60 --code-end 0x62C4CC --chunk-lines 150000 -o src/recomp`; menos de um minuto. |
| Build | **Feito:** `AscensionRecomp.exe`, 75 MB, clang-cl e Ninja com `-j 4`, de 20 a 40 minutos do zero. O projeto é o `templates/project` do ps3recomp, apontado para `../ps3recomp`, `src/recomp` e `src/spu`. |
| Boot | **Até os primeiros menus** (acima). As opções do runtime que este jogo precisa ficam em `host/ascension_defaults.cpp`. |
| macOS | **As telas de abertura, pelo Metal**, na primeira tradução; falta retraduzir. O `tools/run_mac.sh` abre o jogo numa janela. |

## Próximos passos

1. **A tela preta depois dos menus.** Com o save do sistema presente, o jogo pula os avisos e fica preto; descobrir o que ele espera (o `WATCHDOG_UNWIND` do watchdog mostra a pilha exata).
2. **Controle:** confirmar que os menus respondem ao controle (os avisos esperam triângulo ou xis).
3. **A cinemática de abertura:** o `INTROCIN.PSARC` tem `/CINEMATICS/OPENINGINT6.M2V` (MPEG-2, 350 MB) para o `cellVdec`; o ps3recomp decodifica com o FFmpeg carregado em tempo de execução (`-DPS3RECOMP_FFMPEG_RUNTIME=ON`), que o build do Windows ainda não liga.
4. **Desempenho:** medir primeiro. Custos conhecidos: o pós-processo nas SPUs leva ~100 ms por round no Windows (cerca de 13 ms na Mac), e o runtime grava dezenas de milhares de linhas de log por minuto, de forma síncrona.
5. **macOS:** retraduzir com o lifter da v0.15 e levar o build do Mac ao mesmo ponto.
6. Menores: o `GET_REPORT` de tipo 255 não deveria escrever nada; o limite do `[null-read]` às vezes zera no meio da execução (talvez uma escrita fora dos limites no lado do host).

## Mudanças no ps3recomp

Ficam na branch [`ascension-v0.15` do fork `arnaldolima1/ps3recomp`](https://github.com/arnaldolima1/ps3recomp/tree/ascension-v0.15), 21 commits sobre o ps3recomp v0.15.0 (também guardados em `patches/`). Em resumo:

- **SPURS de segunda geração:** os pontos de entrada que o jogo chama (`cellSpursInitializeWithAttribute2`, `cellSpursCreateTask2`, `cellSpursCreateTaskset2` e afins), 32 workloads e flags1, o tempArea do kernel preenchido a cada seleção, `SPURS_READY_LEVEL`, a fila lock-free (`_cellSpursLFQueuePushBody`), os bitsets do taskset atualizados sob o lock da lock-line (sinais perdidos), uma única partida por task criada, `CellSpursTaskset2` com 0x2900 bytes e seus dois event flags, e tasks que uma SPU cria em outro taskset sendo iniciadas.
- **GCM:** as tabelas de offset escritas na memória do jogo, `GET_REPORT` na memória principal, parks do FIFO com tolerância própria (`GCM_PARK_WAIT_MS`), `SEMAPHORE_ACQUIRE` que espera de fato (`GCM_SEMA_ACQUIRE`), um park liberado esperando as tasks SPU (`GCM_PARK_SPU_HOLD_MS`).
- **Renderização (live draw):** texturas X16, sRGB no framebuffer e gamma de textura, `DDX`/`DDY` no decompilador de shaders.
- **Outros:** Edge Zlib no host, `cellGamePatchCheck`, a janela do macOS e dumps de frames do Metal.
- **Diagnósticos:** `WATCHDOG_REGS`, `WATCHDOG_DUMP`, `WATCHDOG_UNWIND`, `[null-read]` por função com registradores, `SPU_MFCLOG_*`, `SPU_ATOM_EA`, `GCM_REPORTLOG`, `GCM_SEMALOG` e outros (a lista completa está no STATUS em inglês).

O upstream corrigiu por conta própria o layout do `sys_lwcond_t`, arquivos acima de 2 GB, `cellGcmMapEaIoAddressWithFlags`, o microstep da SPU e parks do FIFO (#248, #256, #266, #268, #277, #312), então o rebase ficou com as versões dele.

## Diário de depuração (resumo)

O que cada etapa encontrou, do mais recente para o mais antigo. Os endereços são os do jogo (EU 1.00); os detalhes completos estão no [STATUS.md](STATUS.md).

- **Os menus ficam legíveis.** O atlas da fonte é uma textura X16 (256×256) que o live draw não decodificava: cada letra saía como um bloco. O jogo calcula as cores em espaço linear e pede ao RSX a conversão sRGB (`SET_SHADER_PACKER`, 0x1FEC), que o live draw ignorava: tudo saía escuro. E a fonte é de distance field, cuja borda usa derivadas de tela (`DDX`/`DDY`), que o decompilador não implementava: letras inchadas, com os furos preenchidos.
- **Passando da tela de carregamento.** A thread principal espera um job de partículas: o PPU cria cinco tasks SPU, cada uma pega um item com um add atômico, e a que vê a contagem final cria a fase seguinte a partir da própria SPU. Três falhas do runtime: tasks iniciadas em dobro (a contagem passava do total); o `CellSpursTaskset2` criado como um taskset comum (a biblioteca da SPU recusa criar tasks nele, erro `0x80410909`); e o escalonador que só olhava o taskset da task que terminava.
- **A retradução.** O código antigo parava no frame ~12 por um bug do lifter já corrigido no ps3recomp (`a470b79`): um recarregamento de registrador da pilha (`ld r24, 0x78(r1)`) em `func_0037DE70` virava "o valor da entrada da função". O jogo calculava um tamanho 12 bytes menor, escrevia além do bloco e corrompia a lista livre de um heap; a alocação seguinte entrava em laço infinito.
- **O frame 2.** O jogo libera um frame por vblank (o handler de VBlank reescreve o park do FIFO) e conta com o próprio GPU levar o tempo de um frame; no frame 1 ele não espera o pós-processo. O nosso RSX leva tempo zero, então o frame 2 passava na frente do round 1 das SPUs. `GCM_PARK_SPU_HOLD_MS` segura o próximo segmento enquanto há tasks rodando, e `SPURS_READY_LEVEL` mantém o job manager Wws rodando até guardar os seus jobs.
- **O pós-processo nas SPUs** (provavelmente MLAA): cinco tasks percorrem o framebuffer de 1280×720 em blocos, com barreiras entre si, e o GPU espera por elas (`SEMAPHORE_ACQUIRE` nos labels `0x51`/`0x52`). Sinais perdidos numa corrida de leitura-modificação-escrita foram corrigidos.
- **O grafo por frame:** listas de jobs Wws, dependências `{contador, workload, readyCount}`, e a cadeia GPU → RsxSync → tasks → próxima lista EDGE. O SPURS2 tem 32 workloads (o runtime parava em 16), e a barreira precisava do flags1 e do tempArea do kernel.
- **Telas de abertura:** a janela preta era o renderizador D3D12 padrão, que não gravava nenhum draw deste jogo; o motor live draw executa todos.
- **Boot:** o Edge Zlib (descompressão dos arquivos do jogo) roda no host, com o skip de saída do streaming; as tabelas de offset do GCM passaram a ser escritas na memória do jogo; o layout do `sys_lwcond_t` e o acesso a arquivos acima de 2 GB (o `RESOURCES.PSARC` tem 2,1 GB) foram corrigidos.

## Lacunas que os imports mostram

- **PRX:** `sys_prx_load_module` e variantes; o jogo carrega módulos próprios em tempo de execução.
- **Leitura assíncrona de arquivos** (`cellFsAio*`) e **mapeamento de memória** (`sys_mmapper_*`).
- Cerca de 140 imports são de rede e online (`sceNp*`, `cellHttp`, `cellSsl`, `sys_net`, `cellVoice`, `cellNetCtl`): multiplayer, respondidos como offline.

## O que esperar

Entre os ports feitos com o ps3recomp, o Twisted Metal (2012) é um dos mais avançados: os menus e o HUD da partida aparecem, o mundo 3D ainda não, travado pelos jobs SPURS e pelo anel de geometria Edge. O Ascension usa o mesmo tipo de trabalho nas SPUs, e mais dele. Agora ele chega aos menus; o jogo em si (o mundo 3D, o combate, as cinemáticas) ainda está pela frente.
