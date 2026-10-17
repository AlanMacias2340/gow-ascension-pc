# Situação

Onde o experimento está, em 17/10/2026. Máquinas: Windows 11, AMD Ryzen 7 5700G, Radeon RX 7600, 16 GB; e um Mac, Apple M4, 16 GB, macOS 26. In English: [STATUS.md](STATUS.md) (com o diário técnico completo).

## Onde estamos

**No Windows o jogo inicia, mostra as telas de abertura, carrega, passa pelos primeiros menus e toca a cinemática de abertura com imagem e som**: a escolha de idioma, a tela de ajuste da imagem e a de brilho, desenhadas pelos próprios shaders do jogo, na fonte bronze dele; depois `OPENINGINT6.M2V` decodificado pelo FFmpeg. No primeiro uso ele grava o save do sistema (`BCES01741-SYSDATA`). A resposta ao controle ainda não foi testada, e o menu principal depois da cinemática ainda não foi visto (ela dura uns 4 minutos). Ainda está lento: 26-55 fps nos menus sem save e 45-60 na cinemática (eram ~10 e ~33-38 na manhã de 17/10/2026), e o vídeo da cinemática anda a 75-85% da velocidade do áudio (veja os próximos passos); um painel no canto superior direito mostra FPS, tempo de quadro, velocidade, CPU e GPU. Não há release; para testar, compile a partir do código.

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
| 17/10/2026 | A "tela preta" depois dos menus era o cartão de fade do jogo esperando a cinemática: `cellVdecQueryAttrEx`/`cellVdecOpenEx` implementados, timestamps gerados para o MPEG-2 sem PTS, `frame_rate_code` no `CellVdecMpeg2Info`, FFmpeg em tempo de execução no Windows. A cinemática toca com imagem e som. |
| 17/10/2026 | Desempenho: os 15 módulos de job Wws (que rodavam no interpretador de SPU) traduzidos e registrados por assinatura, menos log por quadro (`PS3_VERBOSE=0`), painel de desempenho (`LD_PERF_OVERLAY`). Menus sem save: 5-6 → ~10 fps. |
| 17/10/2026 | Desempenho, parte dois: os fragmentos de código do módulo 209 traduzidos independentes de posição, mais 27 entradas nos módulos de job, SSE4.1 no código SPU traduzido e nas operações de ponto flutuante do SPU (patches 0023-0025). Menus sem save ~10 → 26-55 fps, cinemática ~35 → 45-60 fps. |

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
| Módulos de job SPU | **Feito:** os 15 módulos Wws que o gerenciador carrega do EBOOT (`0x6B2480`-`0x82B780`), despejados com `SPU_DUMP_OVL=<dir>,0x4000` e traduzidos com `python ps3recomp/tools/lift_jobmods.py --jobmods work/jobmods --out ascension/src/spu --register ascension/src/spu/jobmods_register.c --symbol-prefix ascension --extra-funcs-json ascension/tools/jobmods_extra_funcs.json` (imagens 200-214). O policy module foi retraduzido com entradas extras: `build_spu_workloads.py ... --relift --extra-funcs spu_wws_pm_at_0077CA80=0xA2C,0xA68,0x3368,0x3378`. |
| Build | **Feito:** `AscensionRecomp.exe`, ~89 MB, clang-cl e Ninja com `-j 4`, de 20 a 40 minutos do zero. O projeto é o `templates/project` do ps3recomp, apontado para `../ps3recomp`, `src/recomp` e `src/spu`. Com `-DPS3RECOMP_FFMPEG_RUNTIME=ON -DPS3RECOMP_FFMPEG_INCLUDE_DIR=<work/deps/ffmpeg-9.0.2-include>` (headers do FFmpeg 9.0.2) e, ao lado do executável, `avcodec-63.dll`, `avutil-61.dll` e `swresample-7.dll` (cópia em `work/deps/ffmpeg-9.0.2-bin`). O link gera `AscensionRecomp.map`, para dar nome aos endereços do amostrador (`PS3_DEBUG=<arquivo>`, comando `prof <tid> <s>`). |
| Boot | **Até a cinemática de abertura** (acima). As opções do runtime que este jogo precisa ficam em `host/ascension_defaults.cpp`. |
| macOS | **As telas de abertura, pelo Metal**, na primeira tradução; falta retraduzir. O `tools/run_mac.sh` abre o jogo numa janela. |

## Próximos passos

1. **Um frame mais curto.** O loop principal roda a ~24-33 Hz esperando a cadeia de cada frame (`tools/frame_timeline.py`: o último relatório da GPU sai ~13 ms depois do início do frame, as listas EDGE terminam ~25 ms depois); as threads SPU ficam quase ociosas. Candidatos: o trabalho de textura na CPU da thread do RSX (`decode_texel`, `nv3089_blit`) e a latência das listas EDGE.
2. ~~**A cinemática atrasa em relação ao áudio**~~ resolvido (2026-10-17): vídeo decodificado a 29,98 fps no filme inteiro, sincronizado. Resta uma oscilação leve: o loop a ~35 Hz contra o filme a 30 fps.
2b. **A entrada `0x4418` do módulo de job 214** trava o jogo no fim do carregamento quando é traduzida: fica entre um `bihz` que liga interrupções (`0x4414`) e um que desliga (`0x447C`), e o `biz`/`bihz` do interpretador ignora os bits E/D que o código traduzido aplica. Fica fora do `tools/jobmods_extra_funcs.json`; provavelmente a mesma raiz do item 5.
3. **O menu principal depois da cinemática:** agora renderiza, a ~1 fps. Próximo passo.
4. **Controle:** confirmar que os menus respondem ao controle (os avisos esperam triângulo ou xis).
5. ~~**Travamento intermitente**~~ resolvido (2026-10-17): o relatório seguinte da GPU passava à frente da rodada do RsxSync (`GCM_REPORT_SPU_HOLD_MS`, patch 0029); o job module 214 roda compilado.
6. **Profundidade lida como ARGB8:** o jogo amostra o zeta como textura ARGB8 (o truque comum do PS3) e o live draw só associa o snapshot de profundidade a texturas `DEPTH24_D8`; o pós-processo (SSAO etc.) recebe zeros.
7. **macOS:** retraduzir com o lifter da v0.15 e levar o build do Mac ao mesmo ponto.
8. Menores: o `GET_REPORT` de tipo 255 não deveria escrever nada; o limite do `[null-read]` às vezes zera no meio da execução.

## Mudanças no ps3recomp

Ficam na branch [`ascension-v0.15` do fork `arnaldolima1/ps3recomp`](https://github.com/arnaldolima1/ps3recomp/tree/ascension-v0.15), 25 commits sobre o ps3recomp v0.15.0 (também guardados em `patches/`). Em resumo:

- **SPURS de segunda geração:** os pontos de entrada que o jogo chama (`cellSpursInitializeWithAttribute2`, `cellSpursCreateTask2`, `cellSpursCreateTaskset2` e afins), 32 workloads e flags1, o tempArea do kernel preenchido a cada seleção, `SPURS_READY_LEVEL`, a fila lock-free (`_cellSpursLFQueuePushBody`), os bitsets do taskset atualizados sob o lock da lock-line (sinais perdidos), uma única partida por task criada, `CellSpursTaskset2` com 0x2900 bytes e seus dois event flags, e tasks que uma SPU cria em outro taskset sendo iniciadas.
- **GCM:** as tabelas de offset escritas na memória do jogo, `GET_REPORT` na memória principal, parks do FIFO com tolerância própria (`GCM_PARK_WAIT_MS`), `SEMAPHORE_ACQUIRE` que espera de fato (`GCM_SEMA_ACQUIRE`), um park liberado esperando as tasks SPU (`GCM_PARK_SPU_HOLD_MS`).
- **Renderização (live draw):** texturas X16, sRGB no framebuffer e gamma de textura, `DDX`/`DDY` no decompilador de shaders; painel de desempenho (`LD_PERF_OVERLAY`).
- **Vídeo (cellVdec):** `cellVdecQueryAttrEx`/`cellVdecOpenEx`, timestamps numerados para AUs sem PTS, `CellVdecMpeg2Info` com `frame_rate_code`, proporção e estrutura de quadro.
- **SPU:** `cellSpursJoinTask2`; `lift_jobmods.py --extra-funcs-json` (entradas extras por módulo).
- **Outros:** Edge Zlib no host, `cellGamePatchCheck`, a janela do macOS e dumps de frames do Metal.
- **Diagnósticos:** `WATCHDOG_REGS`, `WATCHDOG_DUMP`, `WATCHDOG_UNWIND`, `[null-read]` por função com registradores, `SPU_MFCLOG_*`, `SPU_ATOM_EA`, `GCM_REPORTLOG`, `GCM_SEMALOG`, `LD_ZPROBE`, `HLE_BT_NID`, entradas no interpretador de SPU com o PC inicial, e outros (a lista completa está no STATUS em inglês).

O upstream corrigiu por conta própria o layout do `sys_lwcond_t`, arquivos acima de 2 GB, `cellGcmMapEaIoAddressWithFlags`, o microstep da SPU e parks do FIFO (#248, #256, #266, #268, #277, #312), então o rebase ficou com as versões dele.

## Diário de depuração (resumo)

O que cada etapa encontrou, do mais recente para o mais antigo. Os endereços são os do jogo (EU 1.00); os detalhes completos estão no [STATUS.md](STATUS.md).

- **Cinemática em velocidade total, sincronizada; travamento do fim do loading resolvido** (2026-10-17, Windows). Um GET_REPORT espera enquanto as tarefas de pós-processamento ainda estão numa rodada (`GCM_REPORT_SPU_HOLD_MS=50`): o RsxSync transforma cada relatório num sinal, e com o job module 214 compilado o relatório seguinte chegava antes de as tarefas começarem, o sinal era perdido e o jogo parava sempre. Depois, três causas de engasgos: a trava medida com GetTickCount (passos de 15,6 ms); esperas de tarefa que perdiam o aviso e dormiam até o timeout de 1 s (agora conferidas a cada 2 ms, `[missed-wake]`); `cellVdecDecodeAu` devolvendo BUSY com a fila cheia, onde o decodificador segura o AU. Resultado: vídeo a 29,98 fps, loop ~35 Hz, quadro mais longo 44 ms. ps3recomp `7744141`, patch 0029.
- **Menus de ~10 para 26-55 fps; por que a cinemática atrasa em relação ao áudio.** O módulo 209 não copia código: a lista de DMA de cada job traz até três fragmentos de código do EBOOT para o buffer de entrada, em endereços que variam; agora traduzidos uma vez cada, independentes de posição. O interpretador só voltava ao código traduzido da própria imagem, então um job que caía nele uma vez rodava o resto interpretado; com o histograma (`SPU_INTERP_HIST`) entraram 27 entradas nos módulos de job (a 28ª, 214:`0x4418`, trava o jogo e foi achada por bisseção com `SPU_NOLIFT`). O código SPU traduzido era compilado sem SSE4.1: o `shufb` virava um laço byte a byte e cada operação de ponto flutuante quatro lanes escalares; as versões SSE4.1 são idênticas bit a bit às de referência e 4,8x mais rápidas. Na cinemática, o áudio roda em tempo real e o vídeo a 58-99%: o demultiplexador carrega um bloco de 64 KB por iteração do loop principal, e o stream precisa de ~2 MB/s.

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
