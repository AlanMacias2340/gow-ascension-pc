"""Calls into the system: the macOS Dock, a font for this process only."""

import ctypes
import subprocess
from .config import CONFIG_DIR, HERE, MAC, WINDOWS


def mac_dock(show):
    """Python stays in the Dock after the Tk window is withdrawn, so the game
    looks like a second icon. Accessory policy takes this process out of the
    Dock; regular puts it back when the game closes."""
    if not MAC:
        return
    src = HERE / 'mac_dock.m'
    dylib = CONFIG_DIR / 'mac_dock.dylib'
    try:
        if src.is_file() and (not dylib.is_file() or dylib.stat().st_mtime < src.stat().st_mtime):
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            subprocess.run(['clang', '-dynamiclib', '-framework', 'Cocoa', '-o', str(dylib), str(src)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        lib = ctypes.CDLL(str(dylib))
        lib.ascension_dock.argtypes = [ctypes.c_int]
        lib.ascension_dock(1 if show else 0)
    except (AttributeError, OSError, subprocess.CalledProcessError):
        pass


def register_font(path):
    """The font for this process only (Windows: FR_PRIVATE; macOS: Core Text's
    process scope)."""
    if not path.is_file():
        return False
    try:
        if WINDOWS:
            ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0)  # FR_PRIVATE
            return True
        if MAC:
            cf = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
            ct = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreText.framework/CoreText')
            cf.CFURLCreateFromFileSystemRepresentation.restype = ctypes.c_void_p
            cf.CFURLCreateFromFileSystemRepresentation.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                                                   ctypes.c_long, ctypes.c_bool]
            ct.CTFontManagerRegisterFontsForURL.restype = ctypes.c_bool
            ct.CTFontManagerRegisterFontsForURL.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
            raw = str(path).encode()
            url = cf.CFURLCreateFromFileSystemRepresentation(None, raw, len(raw), False)
            ct.CTFontManagerRegisterFontsForURL(url, 1, None)   # kCTFontManagerScopeProcess
            return True
    except (AttributeError, OSError):
        pass
    return False
