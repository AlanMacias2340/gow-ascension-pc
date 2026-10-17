"""Lay the per-frame dependency chain out in time, from a run log.

usage: python tools/frame_timeline.py build/logs/<run>.log [--frames 200] [--show 3]

Run the game with (scripts/run.ps1 -Env @{...}):
    SPU_ATOM_EA=99AA80 SPU_ATOM_EA_MAX=1 PPU_WWATCH=99AA80 PPU_WWATCH_LEN=0x80
    PPU_WWATCH_MAX=300000 GCM_REPORTLOG=1000000   [VDEC_TIMELOG=1]
The 128-byte line at 0x99AA80 holds the frame's dependency counters
(0x99AA84 + 4f), MeshProc's (0x99AAA4), the EDGE lists' (0x99AAB0 + 4i) and the
frame slots the render thread waits on (0x99AAC0 + 4i); the PPU starts frame f
by writing f to 0x99AAA0. For the last --frames frames, prints the median time
from the frame's start to each link: the GPU's last report of the frame, the
RsxSync workload (wid 18), MeshProc (wid 14), the EDGE lists (wid 15-17), and the
video picture taken (VDEC_TIMELOG). --show prints the raw events of that many
frames too.
"""
import argparse
import re
import statistics


def parse(path):
    ev = []
    for l in open(path, encoding="utf-8", errors="ignore"):
        m = re.search(r"\[atom-ea\] t=(\d+)us PUTLLC OK lr=0x(\w+) ea=0x\w+ wid=(\d+) RAM=(.*)", l)
        if m:
            ev.append((int(m.group(1)), "S", (int(m.group(3)), m.group(2), m.group(4).split()))); continue
        m = re.search(r"\[ww\] t=(\d+)us 0x(\w+) <- 0x(\w+) .*guest-fn=0x(\w+)", l)
        if m:
            ev.append((int(m.group(1)), "P", (int(m.group(2), 16), int(m.group(3), 16), m.group(4)))); continue
        m = re.search(r"\[GET_REPORT\] t=(\d+)us type=(\d+) off=0x(\w+)", l)
        if m:
            ev.append((int(m.group(1)), "R", (int(m.group(2)), int(m.group(3), 16)))); continue
        m = re.search(r"\[vdec-time\] t=(\d+)us", l)
        if m:
            ev.append((int(m.group(1)), "V", ()))
    ev.sort()
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--frames", type=int, default=200)
    ap.add_argument("--show", type=int, default=0)
    a = ap.parse_args()
    ev = parse(a.log)
    starts = [e[0] for e in ev if e[1] == "P" and e[2][0] == 0x99AAA0]
    if len(starts) < 3:
        raise SystemExit("no frame starts (PPU writes to 0x99AAA0) in the log: see the usage for the variables")
    starts = starts[-(a.frames + 1):]
    rows = []
    for fi, (s, e) in enumerate(zip(starts, starts[1:])):
        seg = [x for x in ev if s <= x[0] < e]
        rel = lambda x: (x[0] - s) / 1000

        def first(pred):
            return next((rel(x) for x in seg if pred(x)), None)

        def last(pred):
            v = [rel(x) for x in seg if pred(x)]
            return v[-1] if v else None
        rows.append({
            "frame": (e - s) / 1000,
            "gpu last report": first(lambda x: x[1] == "R" and x[2][0] == 255),
            "RsxSync (wid 18)": first(lambda x: x[1] == "S" and x[2][0] == 18),
            "MeshProc done (wid 14)": last(lambda x: x[1] == "S" and x[2][0] == 14),
            "EDGE done (wid 15-17)": last(lambda x: x[1] == "S" and x[2][0] in (15, 16, 17)),
            "video picture": first(lambda x: x[1] == "V"),
        })
        if fi >= len(starts) - 1 - a.show:
            print(f"--- frame of {(e - s) / 1000:.1f} ms")
            for x in seg:
                kind = {"R": "GPU", "S": "SPU", "P": "PPU", "V": "VID"}[x[1]]
                print(f"  {rel(x):7.2f} {kind} {x[2] if x[1] != 'S' else ('wid', x[2][0], 'lr', x[2][1])}")
    print(f"{len(rows)} frames; ms from the frame's start (median, and in how many frames it happened):")
    for k in rows[0]:
        v = [r[k] for r in rows if r[k] is not None]
        if v:
            print(f"  {k:24} {statistics.median(v):7.1f}   ({len(v)}/{len(rows)})")
    fr = sorted(r["frame"] for r in rows)
    print("frame time p10/p50/p90:", f"{fr[len(fr)//10]:.1f} / {fr[len(fr)//2]:.1f} / {fr[len(fr)*9//10]:.1f} ms")


if __name__ == "__main__":
    main()
