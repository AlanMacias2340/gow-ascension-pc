# Milestones

What the game could do, and when.

| Date | Milestone |
| --- | --- |
| 2026-10-15 | `EBOOT.BIN` decrypted, imports and functions found, 1.8 million lines of C++ lifted and compiled; the executable starts. |
| 2026-10-15 | Boots through the system checks and mounts the game's archives (`sys_lwcond_t` layout, files past 2 GB, Edge Zlib on the host). |
| 2026-10-15 | The intro screens render: the legal text, "Sony Computer Entertainment presents", Santa Monica Studio, the online-play notice (live draw engine). The same on macOS through Metal. |
| 2026-10-16 | The main renderer runs past its second frame: SPURS2 (32 workloads, tempArea, flags1), the frame's SPU post-process, GPU/SPU synchronization. |
| 2026-10-16 | Re-lifted with the v0.15 lifter (a spill-reload bug corrupted a heap at frame ~12): the loading screen. |
| 2026-10-16 | Past the loading screen (SPURS tasksets: duplicate starts, Taskset2 size and event flags, SPU-created tasks). |
| 2026-10-16 | The menus read: X16 font atlas, framebuffer sRGB and texture gamma, fragment `DDX`/`DDY` in the live draw engine. |
| 2026-10-17 | The opening cinematic plays with picture and sound (`cellVdec` with FFmpeg at run time; the "black screen" was the game's fade card waiting for it). |
| 2026-10-17 | Performance: the 15 Wws job modules lifted, a performance panel. First-use menus 5-6 → ~10 fps. |
| 2026-10-17 | Performance, part two: position-independent lifts of streamed job code, SSE4.1 for lifted SPU code. Menus ~10 → 26-55 fps, cinematic ~35 → 45-60 fps. |
| 2026-10-17 | RsxSync woken by GPU reports, SSE4.1 SPU ops, 381 job-module entries, the interpreter honouring interrupt enables. Cinematic video at 72-90% speed. |
| 2026-10-17 | **The cinematic at full speed and in sync** (29.98 fps), the end-of-loading stall gone, module 214 lifted whole (GPU reports wait for the post-process tasks, no lost task wakes, `cellVdec` holds AUs). |
| 2026-10-17 | The main menu renders (about 1 fps). |
| 2026-10-17 | **A launcher:** video, language, subtitles and mods; the game renders inside its window. |
| 2026-10-17 | **Main menu 1 -> 12 fps:** the 18 job modules the loading never streams lifted too (33 in all), streamed code found inside bigger GETs and by content. |
| 2026-10-17 | Brazilian Portuguese (voices from the US disc, text already on the EU disc); mods as recipes, Skip intro included. |
| 2026-10-18 | **The first level** (Kratos in chains): a lost-task race in the SPURS taskset scheduler fixed; the level loads and runs (~16 fps on live draw). |
| 2026-10-19 | **RPCS3's RSX as the renderer** (Windows and macOS): the game's GPU/SPU post-process rounds paced on the game's own progress. |
| 2026-10-19 | Main menu 12 → 28 fps on RPCS3's RSX: SPU transfers into surfaces the GPU protected were being dropped. |
| 2026-10-19 | **Level textures correct:** IO space handed back on unmap, so the scenery's vertex streams no longer read the command buffer. |
| 2026-10-20 | Level ~10 → ~15 fps: lifted SPU floats without the extended-range check (RPCS3's "approximate" rules), no local-store diagnostics in lifted code, contiguous job-module code lifted as one function, streamed code found by an index. |
| 2026-10-21 | Level ~15 → ~16.7 fps: each SPU on its own core, the main PPU thread on core 0. |
| 2026-10-21 | **SPU job replay:** recorded game jobs rerun outside the game and checked byte for byte by what they write, with timing and profiling. Module 218 (per-draw geometry) decoded: index decompression and position transform written natively, identical on the recorded jobs; the rest of the job goes native next. |
