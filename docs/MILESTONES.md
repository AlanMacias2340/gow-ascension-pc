# Milestones

What the game could do, and when. The details behind each one are in [STATUS.md](STATUS.md).

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
| 2026-10-17 | **The cinematic at full speed and in sync** (29.98 fps), the end-of-loading stall gone, every job module lifted (GPU reports wait for the post-process tasks, no lost task wakes, `cellVdec` holds AUs). |
| 2026-10-17 | The main menu renders (about 1 fps). |
| 2026-10-17 | **A launcher:** video, language, subtitles and mods; the game renders inside its window. |
