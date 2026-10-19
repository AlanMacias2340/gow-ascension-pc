# Mac: da tela da Sony ao menu

19/10/2026. No Mac (Apple M4, Vulkan via MoltenVK, `PS3_RSX=rpcs3`) a tela legal da Sony aparecia e o jogo não seguia para o loading. Agora passa do loading e chega nos menus. A mesma correção vale para o Windows, que antes passava por sorte de tempo (cerca de uma execução em três empacava no menu).

## O protocolo do jogo

O job RsxSync (workload 18) lê os reports de quadro do RSX (`0x1101ED10 + 0x10n`, um anel de 27) **um de cada vez, na ordem**, com um GET de 16 bytes, até o RSX escrever o report (a última palavra, armada com um valor diferente de zero, vira 0). Um a cada dois reports começa uma rodada de pós-processamento: o RsxSync escreve o descritor em `0x9BAC30` (`{rodada n, EA da label, ...}`) e sinaliza as cinco tarefas do taskset `0x11027280`. As tarefas trabalham com uma barreira entre elas (`0x9BAC80`) e a última escreve `n` na label (`0x2E200520` nas rodadas ímpares, `0x2E200510` nas pares). Depois dos reports, o FIFO faz `SEMAPHORE_ACQUIRE` nessa label.

No PS3 o RSX leva um quadro desenhando antes do próximo report, então uma rodada sempre termina antes de a próxima ser sinalizada. O jogo depende disso.

## O que quebrava

1. **O RsxSync dormia.** Um workload sem trabalho fica em back-off, e só o walker de FIFO antigo acordava o kernel SPURS quando um report era escrito (`spurs_external_event`). Com o RSX do RPCS3 ninguém acordava; com todas as SPUs ociosas, a rodada nunca começava.
2. **A corrida entre rodadas.** O RSX recompilado escreve os reports quase juntos. O sinal da rodada seguinte caía enquanto as tarefas estavam na barreira (a espera da barreira consumia o sinal, `wobj=0x9BAC80 sig=1`) ou se juntava ao anterior, e o descritor era sobrescrito. A rodada se perdia e o `semaphore_acquire` estourava (`value=0x2 expected=0x4`).

## A correção

- `rpcs3_rsx_guest_write` (`boot_main.cpp`) chama `spurs_external_event()` a cada escrita do RSX, como o walker.
- **`GCM_ROUND_GATE=9BAC30`** (padrão em `host/ascension_defaults.cpp`): o report placeholder `0xFFFFFFFF` que vem depois de cada report de quadro só passa quando
  1. a SPU que estava lendo cada report escrito pelo RSX já o leu de novo depois da escrita (o RsxSync agiu sobre ele e sobre todos os anteriores), e
  2. a rodada do descritor já escreveu a sua label.

  As duas coisas são o próprio progresso do jogo; não há tempo para ajustar. Para saber quem espera um report, o runtime anota todo GET de 16 bytes que encontra o report ainda armado (`spu_read_watch_*` em `spu_channels.c`); o RSX avisa antes de escrever cada report (`g_ps3recomp_rsx_report_hook`, `on_report` em `ps3rsx.h`). Se em 1 s (o timeout do próprio semáforo do RSX) a condição não fecha, o log mostra `GCM_ROUND_GATE: after 1 s ...`, o report passa e as leituras pendentes são descartadas.
- Saíram o intervalo de 16 ms entre flips (`PS3_FLIP_PACE_US`) e a espera por tempo no report (20 ms para começar, até 1 s enquanto houver tarefa rodando).

Medido em execuções de 90 a 120 s: nenhum timeout de semáforo, mais de 120 rodadas seguidas, espera do placeholder com mediana de 0,4 ms e máximo de 9 ms.

## Teclado

A janela do RPCS3 no Mac (`rsx_cocoa_window.m`) não tirava os eventos da fila do AppKit: a thread principal só roda o `CFRunLoop`. `rsx_cocoa_window_pump`, chamada pelo ticker a cada vblank, agora esvazia a fila na thread principal.

## Diagnóstico

- `SPU_TASK_TIMELOG=1`: entrada e saída de cada `WAIT_SIGNAL`, com o objeto de espera (`wobj`: a barreira, ou 0 na espera de rodada) e se o sinal já estava lá.
- `GCM_HOLD_LOG=1`: cada placeholder que esperou, com a rodada e o tempo.
- `SPU_MFCLOG_EA=1101ED00,9BAC00`: os GETs do RsxSync nos reports e no descritor.

## Windows (19/10/2026, depois)

No Windows o RSX do RPCS3 escreve os reports bem mais rápido, e o gate do Mac deixava a rodada 2 passar no meio da rodada 1 (travava em ~15 s, metade das execuções). Duas brechas:

1. Só era vigiado um report que a SPU já tinha consultado antes da escrita. O RSX escrevia o report seguinte enquanto o RsxSync ainda tratava o anterior.
2. O report contava como tratado assim que era lido, mas o RsxSync lê o report **antes** de escrever o descritor da rodada.

Agora (`GCM_ROUND_RING=1101ED00,18`, o anel do RsxSync, 18 reports de `ED00` a `EE10`): todo report armado do anel é vigiado, e ele só deixa de estar pendente quando a SPU consulta **outro** report do anel (o RsxSync já escreveu o descritor e sinalizou as tarefas). Reports fora do anel (outro job consulta `0x1124xxxx`/`0x1126xxxx` sem reler) não seguram mais o RSX. Se o RsxSync parar de ler (1 s), volta a exigir a consulta vista antes, até ele ler de novo.

`GCM_HOLD_LOG=2` mostra cada report que o gate libera.
