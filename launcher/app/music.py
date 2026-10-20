"""The launcher's background music."""

import ctypes
import shutil
import subprocess
import threading
import time
from pathlib import Path
from .config import CONFIG_DIR, MAC, WINDOWS, asset
from .i18n import tr


class Music:
    """music.mp3 on a loop, with no extra packages: Windows' MCI, or on macOS
    /usr/bin/afplay. Pausing stops the player; playing starts the track again.
    SIGSTOP does not resume afplay's audio queue, so it is not used."""
    def __init__(self):
        self.ok = False
        self.error = ''
        self.path = path = asset('music.mp3')
        self.proc = self.thread = None
        self.closed = False
        self.want = False
        self._converted = False
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self.player = '/usr/bin/afplay' if Path('/usr/bin/afplay').is_file() else shutil.which('afplay')
        if WINDOWS and path:
            self.mci = ctypes.windll.winmm.mciSendStringW
            self.ok = self.send(f'open "{path}" type mpegvideo alias bgm') == 0
            if self.ok:
                self.send('setaudio bgm volume to 350')
            elif not self.ok:
                self.error = tr('could not open music.mp3')
        elif MAC and path and self.player:
            self.ok = True
            if self._cached_aac().is_file() and self._cached_aac().stat().st_mtime >= path.stat().st_mtime:
                self.path, self._converted = self._cached_aac(), True   # afplay rejected this MP3 before
        elif MAC and not path:
            self.error = tr('no music.mp3')
        elif MAC:
            self.error = tr('afplay not found')

    def send(self, cmd):
        return self.mci(cmd, None, 0, None)

    def _stop_proc(self):
        with self._lock:
            proc = self.proc
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass

    @staticmethod
    def _cached_aac():
        return CONFIG_DIR / 'music.m4a'

    def _convert_once(self):
        """afplay rejects some MP3s ('fmt?'). One conversion to AAC, kept for
        the next start, then retry."""
        if self._converted:
            return False
        self._converted = True
        afconvert = '/usr/bin/afconvert'
        if not Path(afconvert).is_file():
            return False
        out = self._cached_aac()
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            r = subprocess.run([afconvert, '-f', 'm4af', '-d', 'aac', str(self.path), str(out)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except OSError:
            return False
        if r.returncode == 0 and out.is_file():
            self.path = out
            return True
        return False

    def loop(self):
        fails = 0
        while not self.closed:
            if not self.want:
                self._wake.wait()
                self._wake.clear()
                continue
            started = time.monotonic()
            try:
                proc = subprocess.Popen([self.player, '-v', '0.35', str(self.path)],
                                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE, start_new_session=True)
            except OSError as e:
                self.error = str(e)[:80]
                self.want = False
                return
            with self._lock:
                self.proc = proc
            err = proc.stderr.read() if proc.stderr else b''
            code = proc.wait()
            if self.closed or not self.want or code in (0, -15, 143, -9, 137):
                if code == 0:
                    fails = 0
                continue
            if time.monotonic() - started < 0.4:
                fails += 1
                if fails == 1 and self._convert_once():
                    continue
                text = err.decode('utf-8', 'replace').strip()
                self.error = (text or tr('afplay exited with code {code}', code=code))[:80]
                self.want = False
                return
            time.sleep(0.2)

    def play(self):
        if not self.ok:
            return
        self.error = ''
        if WINDOWS:
            self.send('play bgm repeat')
            return
        self.want = True
        self._wake.set()
        if not self.thread:
            self.thread = threading.Thread(target=self.loop, daemon=True)
            self.thread.start()

    def pause(self):
        if not self.ok:
            return
        if WINDOWS:
            self.send('pause bgm')
        else:
            self.want = False
            self._stop_proc()

    def close(self):
        if not self.ok:
            return
        if WINDOWS:
            self.send('close bgm')
        else:
            self.closed = True
            self.want = False
            self._wake.set()
            self._stop_proc()
