# RSX do RPCS3 no Windows: estabilidade, overlay e desempenho

19/10/2026, à tarde, no Windows (Ryzen 7 5700G, RX 7600), depois do trabalho da manhã no Mac ([mac-loading.md](mac-loading.md)). Commits: ps3recomp `ascension-v2`, ascension `v2`.

## Atualização (19/10/2026, noite): 12,5 → 28,5 fps

**Causa real da lentidão:** o cache de texturas do RPCS3 protege com `PAGE_NOACCESS` as superfícies que a GPU desenhou (para copiá-las de volta quando alguém lê). A checagem de DMA da SPU (`mfc_ea_range_committed`, `ps3kit/runtime/spu/spu_dma.h`) tomava essas páginas por memória não alocada. Resultado: **todo DMA das tarefas de pós-processamento para os render targets era descartado**, ~50 mil por segundo, cada um com um `VirtualQuery`. As tarefas trabalhavam sobre dados velhos e cada rodada levava ~60 ms.

**Correção** (ps3kit `34a100d`): `g_vm_protected_page_hook` (o `ps3rsx_handle_fault`, ligado pelo `boot_main` com `PS3_RSX=rpcs3`) libera cada página de 4 KB do intervalo, como o handler de exceções faz para um acesso da CPU, e o DMA é feito.

**Resultado no menu:** 28,5 fps (era 12,5), Speed 95%, frame de 35 ms, rodada de ~17 ms (era ~60), nenhum DMA recusado. O brilho âmbar das lajes ficou mais forte, porque o pós-processamento agora recebe a imagem certa.

A otimização do FMA (abaixo) foi medida: **sem ganho visível** (12,3 → 12,5 fps). Fica, porque está correta.

**Próximo:** o Hold ainda está em ~500 ms/s (o RSX ainda espera metade do tempo pela rodada), e falta medir o primeiro nível com o RSX do RPCS3. Se um DMA voltar a ser recusado, o log mostra `[spu-dma] SKIP`.

## Onde parou (antes da atualização)

- O menu roda com o RSX do RPCS3 (Vulkan) **sem travar**: 10 execuções de 25 a 60 s, nenhum timeout de semáforo.
- O **overlay de desempenho** é o do RPCS3, no estilo do launcher (Cinzel, nomes dourados, painel translúcido, valores em verde/amarelo/vermelho).
- O desempenho ainda está **ruim**: ~12 fps no menu (antes, com o RSX do RPCS3, eram 5-8; com live draw, ~30).
- Há uma otimização **commitada mas não testada no jogo** (FMA da SPU, abaixo). O build dela foi interrompido. **Primeira coisa a fazer:** compilar e medir.

## O que foi feito

### Build no Windows depois do pull do Mac

O commit do Mac moveu os hooks de serialização do shim para os namespaces `vm`/`rsx` (o clang exige). O MSVC procura os símbolos no namespace global, então `gpu/shim/emu.cpp` define as duas versões.

### Travamento na rodada 2 (o gate do Mac tinha duas brechas)

O RSX do RPCS3 no Windows escreve os reports bem mais rápido que no Mac, e o `GCM_ROUND_GATE` deixava a rodada 2 de pós-processamento começar no meio da rodada 1. As tarefas perdiam o sinal na barreira e o jogo travava em ~15 s (metade das execuções).

1. Só era vigiado um report que a SPU já tinha consultado antes da escrita.
2. O report contava como tratado assim que era lido, mas o RsxSync lê o report **antes** de escrever o descritor da rodada.

Correção (`spu_channels.c`, `boot_main.cpp`):

- `GCM_ROUND_RING=1101ED00,18` (padrão em `host/ascension_defaults.cpp`): o anel real do RsxSync tem 18 reports, de `ED00` a `EE10` (a doc do Mac dizia 27 a partir de `ED10`; com isso havia uma espera de 1 s a cada 9 rodadas).
- Todo report armado do anel é vigiado. Ele só deixa de estar pendente quando a SPU consulta **outro** report do anel.
- Reports fora do anel (outro job consulta `0x1124xxxx`/`0x1126xxxx` sem reler) não seguram mais o RSX.
- `GCM_HOLD_LOG=2` mostra cada report que o gate libera e o estado dele.

### Overlay

- `PS3_PERF_OVERLAY=0..5` (ou `LD_PERF_OVERLAY=1`, que vale 4): 1 FPS; 2 + CPU; 3 + utilização; 4 a lista completa; 5 + os gráficos do RPCS3.
- A lista: FPS, Frame (ms), CPU (processo), RSX (carga do thread RSX), SPU (slots SPURS ocupados), **Hold** (ms por segundo que o gate segurou o RSX), Speed (contra 30 fps).
- Cores: verde bom, amarelo médio, vermelho ruim (limites em `overlay_perf_metrics.cpp` e `rpcs3_perf_guest_text` em `boot_main.cpp`).
- `PS3_OVERLAY_FONT` (um `.ttf`; o launcher passa a Cinzel dele; um build acha `launcher/Cinzel-Black.ttf` ao lado de `build/<plataforma>`) e `PS3_OVERLAY_COLORS` (`corpo,fundo,título,fundo do título` em `#RRGGBBAA`).

### Ferramenta

`scripts\windows\snap.ps1 -Out x.png` salva a janela do jogo mesmo atrás de outras janelas, para conferir a tela sem precisar de você.

## Diagnóstico do desempenho

O overlay mostra **Hold ≈ 650-780 ms/s**: o RSX passa 2/3 do tempo parado esperando a rodada de pós-processamento das SPUs. Cada rodada (uma a cada 2 quadros) leva **~55-60 ms**.

Linha do tempo de uma rodada (`SPU_TASK_TIMELOG=1`, `GCM_HOLD_LOG=2`):

| Fase | Tempo |
|---|---|
| 1ª barreira | ~3 ms |
| **entre a 1ª e a 2ª barreira** | **~32 ms** (as 5 tarefas em paralelo) |
| resto até a label | ~20 ms |

O profiler (`run.ps1 -Profile`) mostra as threads de SPU dentro da imagem `spu_0001_at_0067F580` (as tarefas de pós-processamento), código de ponto flutuante pesado, com tempo nos helpers lentos: `spu__xs_fma_fix` (2,6%), `spu_csflt`, `spu_cuflt`, `spu_fi`, `spu__xs_fm_fix`, `spu__xs_fm_std`.

Descartado: `write_color_buffers` (cópia dos render targets de volta à memória a cada draw). Com `PS3_RSX_WCB=0` nada mudou (12,3 fps, rodada ainda ~60 ms). A opção ficou, desligável, com padrão ligado.

## Pendente: FMA vetorial com desnormais e underflow (commitado, sem teste no jogo)

`runtime/spu/spu_helpers.h`, `spu__xs_fma_exact2`: no modo de float da SPU (truncamento, que é o modo do código recompilado), operandos desnormais viram zero e resultados abaixo de 2⁻¹²⁶ viram `+0` no próprio caminho vetorial, em vez de cair no laço escalar por pista (`spu__xs_fma_fix`). É bit a bit igual à referência:

- um desnormal zerado antes da conta dá o mesmo que a referência, que o lê como zero;
- truncado em double, o valor fica abaixo de 2⁻¹²⁶ exatamente quando o valor exato fica.

`tests/test_spu_float_neon.c` dá o mesmo resultado com o helper antigo e com o novo. Os dois falham no mesmo caso, `fma(1, 1, -2^-60)` no modo SPU, que é antigo: o caso usa constantes literais, que o compilador resolve em tempo de compilação no arredondamento padrão.

**Não se sabe ainda quanto ganha.** Se o caminho lento vem de expoente 255 (faixa estendida) e não de desnormais, o ganho é pequeno.

## Próximos passos

1. **Compilar e medir a mudança do FMA.** O build recompila o código SPU recompilado (alguns minutos):

   ```powershell
   cd C:\Users\ArnaldoLima\Documents\Project\psp-recomp\ascension-recomp\ascension
   .\scripts\windows\build.ps1 -Name fmafix
   .\scripts\windows\run.ps1 -Menu -Seconds 40 -Name fmafix -Env @{ PS3_RSX = "rpcs3"; GCM_HOLD_LOG = "1" }
   ```

   Olhar no overlay ou no log o FPS e o Hold, e quanto dura a rodada (`[rsx-report-hold] ... held`). Antes: ~12 fps, rodada ~59 ms.
2. **Descobrir qual condição manda as pistas para o caminho lento** (desnormal, underflow ou expoente 255) com um contador nos `_fix`, e vetorizar o que for comum. Se for expoente 255, `spu_fm`/`spu_fa` precisam de um caminho vetorial para a faixa estendida.
3. **`spu_csflt`/`spu_cuflt`/`spu_fi`**: ver se são chamadas fora de linha e se dá para gerar SSE direto no lifter.
4. Depois do pós-processamento, o resto do quadro: o thread principal do PPU ainda passa >50% esperando as SPUs (`func_00416328`, `func_00466E28`), como no live draw.
5. Planejado antes: cache de shaders em disco com a **nossa** tela de carregamento e a escolha de renderer no menu de vídeo do launcher.

## Comandos úteis

```powershell
# teste sem você: vai direto ao menu
.\scripts\windows\run.ps1 -Menu -Seconds 40 -Name x -Env @{ PS3_RSX = "rpcs3" }
# linha do tempo das rodadas
... -Env @{ PS3_RSX = "rpcs3"; GCM_HOLD_LOG = "2"; SPU_TASK_TIMELOG = "1" }
# perfil das threads aos 28 s
.\scripts\windows\run.ps1 -Menu -Seconds 45 -Name prof -Profile -ProfileAt 28 -ProfileThreads 6 -Env @{ PS3_RSX = "rpcs3" }
# print da janela
.\scripts\windows\snap.ps1 -Out C:\caminho\shot.png
```

A lib do RSX (MSVC) é recompilada assim, a partir de um PowerShell:

```powershell
cmd /c '"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul && ninja -C C:\Users\ArnaldoLima\Documents\Project\psp-recomp\ascension-recomp\work\gpu-build ps3rsx_flip_smoke'
```
