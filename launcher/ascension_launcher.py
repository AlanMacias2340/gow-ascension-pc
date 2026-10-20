"""God of War: Ascension (PC) launcher.

Settings for the recompiled game (window, video, controls, language, mods,
...), kept in %APPDATA%\\ascension-launcher\\settings.json (macOS:
~/Library/Application Support/ascension-launcher) and handed to the game as the
environment switches ps3recomp reads. PLAY starts build/win/AscensionRecomp.exe
(macOS: build/mac/AscensionRecomp) with the disc's EBOOT.ELF; `--play` does the
same without the window.

Artwork (backgrounds, logo, icon, music) is not part of the repository: it is
read from launcher/assets/ or, failing that, ../work/data/launcher/.

The code is in app/: config (paths, settings, the pages' choices), game
(disc, mods, saves, the game's environment), music, native (macOS Dock, fonts)
and ui (the window).
"""

import ctypes
import sys
from pathlib import Path
from app.config import ROOT, SHOT, WINDOWS, load_settings
from app.game import missing, prepare_game, release_disc, start_game
from app.ui import Launcher


def main():
    if '--play' in sys.argv:
        s = load_settings()
        gone = missing(s)
        if gone:
            print('Falta: ' + '; '.join(gone))
            return 1
        env, mounted = prepare_game(s, status=print)
        try:
            process, log = start_game(s, env, ROOT / 'build' / 'logs' / 'last_run.log')
            code = process.wait()
            log.close()
        finally:
            release_disc(mounted)
        return code
    if WINDOWS:
        try:  # the taskbar shows this window's icon, not Python's; sharp text on scaled displays
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ascensionpc.launcher')
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
    import tkinter as tk
    root = tk.Tk()
    app = Launcher(root)
    if SHOT:
        out = Path(sys.argv[sys.argv.index('--shot') + 1])
        pages = ['home', 'video', 'controls', 'game', 'mods', 'advanced', 'about']

        def grab(i):
            from PIL import ImageGrab
            root.update()
            try:     # the window itself, whatever is on top of it (Windows)
                if not WINDOWS:
                    raise OSError
                img = ImageGrab.grab(window=int(root.wm_frame(), 16))
            except (TypeError, ValueError, OSError):
                x, y = root.winfo_rootx(), root.winfo_rooty()
                img = ImageGrab.grab((x, y, x + root.winfo_width(), y + root.winfo_height()))
            img.save(out / f'{pages[i]}.png')
            if i + 1 < len(pages):
                app.show(pages[i + 1])
                root.after(600, grab, i + 1)
            else:
                root.destroy()
        root.after(2500, grab, 0)
    root.mainloop()
    return 0


if __name__ == '__main__':
    sys.exit(main())
