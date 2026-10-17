// Runtime defaults for God of War: Ascension, set before main() runs.
//
// Each is an environment switch ps3recomp reads on first use. A value already
// set in the environment wins, so any of them can still be turned off for a
// run (set it to 0).
//
//   PS3_EDGE_ZLIB_HLE  the Edge Zlib inflate queue is serviced on the host:
//                      the SPU path cannot serve it yet, and without it the
//                      archives never load.
//   RSX_LIVE_DRAW      the live NV4097 draw engine. The default D3D12 path
//                      records none of this title's draws (every present
//                      had draws=0: a black window); the live engine draws
//                      the intro screens correctly.
//   GCM_PARK_WAIT_MS   how long a parked FIFO waits to be patched before the
//                      runtime follows `put` (ps3recomp's default is 50 ms).
//                      This title's SPU jobs fill a frame and patch the park
//                      after `put` has moved; following it early skips the
//                      frame.
//   GCM_SEMA_ACQUIRE   a FIFO SEMAPHORE_ACQUIRE really waits. After each
//                      frame's reports the GPU waits for the label the SPU
//                      post-process tasks write when they finish the frame;
//                      without the wait it runs ahead, RsxSync overwrites the
//                      tasks' descriptor before the slow ones read it, and a
//                      round loses its decrements.
//   GCM_PARK_SPU_HOLD_MS  a park the vblank handler has patched (the next
//                      frame's segment) is held while SPURS tasks are still
//                      running, up to this long. The first frame has no
//                      post-process ACQUIRE: the game relies on the RSX taking
//                      a frame's time, and without the hold frame 2's reports
//                      landed while round 1 still ran, so round 2 never began.
//   SPURS_READY_LEVEL  readyCount is a level, as the real kernel treats it.
//                      The Wws job managers zero their own count once their
//                      jobs are stored; consuming it per admission left
//                      RsxSync's round-2 job unrun until a later kick, which
//                      never came (the render thread waits on frame slot
//                      0x99AAC8 for it).
//   LD_PERF_OVERLAY    frame rate, frame time, speed, CPU and GPU use in the
//                      top-right corner of the window.
//   PS3_VERBOSE=0      the per-frame log lines (task creation and joins, SPU
//                      dispatch, viewport changes, events) stay quiet: every
//                      guest thread writes them through one FILE lock, and
//                      they cost the main thread several percent of its time.
//                      Set PS3_VERBOSE=1 to get them back when investigating.
//
// The OS environment is used directly, not getenv(): the boot harness routes
// getenv through a cache that also remembers a miss, so asking first would pin
// the variable as unset before it is set.
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <stdlib.h>
#endif

namespace {

void set_default(const char* name, const char* value)
{
#ifdef _WIN32
    if (GetEnvironmentVariableA(name, nullptr, 0)) return;
    SetEnvironmentVariableA(name, value);
#else
    setenv(name, value, 0);
#endif
}

struct AscensionDefaults {
    AscensionDefaults()
    {
        set_default("PS3_EDGE_ZLIB_HLE", "1");
        set_default("RSX_LIVE_DRAW", "1");
        set_default("GCM_PARK_WAIT_MS", "2000");
        set_default("GCM_SEMA_ACQUIRE", "1");
        set_default("GCM_PARK_SPU_HOLD_MS", "1000");
        set_default("SPURS_READY_LEVEL", "1");
        set_default("LD_PERF_OVERLAY", "1");
        set_default("PS3_VERBOSE", "0");    }
} s_defaults;

}  // namespace
