"""God of War: Ascension (PC) launcher.

Settings for the recompiled game (window, video, controls, language, mods,
...), kept in %APPDATA%\\ascension-launcher\\settings.json (macOS:
~/Library/Application Support/ascension-launcher) and handed to the game as the
environment switches ps3recomp reads. PLAY starts build/win/AscensionRecomp.exe
(macOS: build/mac/AscensionRecomp) with the disc's EBOOT.ELF; `--play` does the
same without the window.

Artwork (backgrounds, logo, icon, music) is not part of the repository: it is
read from launcher/assets/ or, failing that, ../work/data/launcher/.
"""
import ctypes
import json
import os
import shutil
import struct
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

VERSION = '0.1'
APP_NAME = 'God of War: Ascension'
WINDOWS = sys.platform == 'win32'
MAC = sys.platform == 'darwin'
SHOT = '--shot' in sys.argv     # development: screenshot each page, then quit (no music)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # ascension/
WORK = ROOT.parent / 'work'
ASSET_DIRS = [HERE / 'assets', WORK / 'data' / 'launcher']
if WINDOWS:
    CONFIG_DIR = Path(os.environ.get('APPDATA', Path.home())) / 'ascension-launcher'
elif MAC:
    CONFIG_DIR = Path.home() / 'Library' / 'Application Support' / 'ascension-launcher'
else:
    CONFIG_DIR = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'ascension-launcher'
CONFIG_FILE = CONFIG_DIR / 'settings.json'


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
BACKGROUNDS = ['background.jpg', 'background-2.jpg', 'background-3.jpg', 'background-4.png']

# The PS3 console languages the disc has text and voices for (CELL_SYSUTIL_LANG_*).
# Greek is not a console language: the game itself offers it at first start.
LANGUAGES = [
    ('18', 'English (UK)'), ('1', 'English (US)'), ('7', 'Português (Portugal)'),
    ('17', 'Português (Brasil)'), ('2', 'Español'), ('3', 'Français'), ('4', 'Deutsch'),
    ('5', 'Italiano'), ('8', 'Русский'), ('16', 'Polski'), ('19', 'Türkçe'),
]
DISPLAY_MODES = [('window', 'Janela'), ('fullscreen', 'Tela cheia (sem bordas)')]
WINDOW_SIZES = [(s, s.replace('x', ' x ')) for s in
                ('1280x720', '1600x900', '1920x1080', '2560x1440', '3840x2160')]
ENTER_BUTTONS = [('cross', 'X confirma (Ocidente)'), ('circle', 'O confirma (Japão)')]
ON_OFF = [('1', 'Ligado'), ('0', 'Desligado')]

# Video. The renderer: RPCS3's RSX (ps3recomp gpu/, a build with
# -DASCENSION_RPCS3_RSX=ON) or live draw. On macOS, Vulkan is MoltenVK and
# live draw is Metal; the GL backend is WGL, so it is not offered there.
RENDERERS = ([('rpcs3-vulkan', 'RPCS3 · Vulkan (MoltenVK)'),
              ('metal', 'Live draw · Metal')] if MAC else
             [('rpcs3-vulkan', 'RPCS3 · Vulkan'), ('rpcs3-opengl', 'RPCS3 · OpenGL'),
              ('livedraw', 'Live draw · Direct3D 12')] if WINDOWS else
             [('rpcs3-vulkan', 'RPCS3 · Vulkan'), ('rpcs3-opengl', 'RPCS3 · OpenGL')])
RENDER_SCALES = [('100', '100% · 1280 x 720 (original)'), ('150', '150% · 1920 x 1080'),
                 ('200', '200% · 2560 x 1440'), ('300', '300% · 3840 x 2160')]
ASPECTS = [('keep', 'Manter 16:9 (barras pretas)'), ('stretch', 'Esticar para a janela')]
SCALE_FILTERS = [('linear', 'Suave (bilinear)'), ('nearest', 'Nítido (pixel)'),
                 ('fsr', 'AMD FSR 1 (RPCS3)')]
VSYNC_MODES = [('auto', 'Automático (o do renderizador)'), ('1', 'Ligado'), ('0', 'Desligado')]
ANISO_LEVELS = [('0', 'O do jogo'), ('2', '2x'), ('4', '4x'), ('8', '8x'), ('16', '16x')]

# Controls: the PS3 pad's controls, grouped as the Controles page shows them,
# with what they do in the game where that is certain. The ids are
# ps3recomp's (PS3_KEYMAP / PS3_PADMAP, libs/input/pad_keymap.h).
CONTROL_GROUPS = [
    ('Analógico esquerdo · andar', [('ls_up', 'Cima'), ('ls_down', 'Baixo'), ('ls_left', 'Esquerda'),
                                     ('ls_right', 'Direita')]),
    ('Analógico direito · esquiva', [('rs_up', 'Cima'), ('rs_down', 'Baixo'), ('rs_left', 'Esquerda'),
                                      ('rs_right', 'Direita')]),
    ('Botões', [('cross', '✕  Pular'), ('square', '□  Ataque leve'), ('triangle', '△  Ataque forte'),
                ('circle', '○  Agarrar')]),
    ('Ombros e gatilhos', [('l1', 'L1  Defender'), ('r1', 'R1'), ('l2', 'L2'), ('r2', 'R2'),
                           ('l3', 'L3 (clique do analógico)'), ('r3', 'R3 (clique do analógico)')]),
    ('Direcional', [('up', '↑  Cima'), ('down', '↓  Baixo'), ('left', '←  Esquerda'), ('right', '→  Direita')]),
    ('Sistema', [('start', 'START  Pausa'), ('select', 'SELECT')]),
]
PAD_CONTROLS = [c for _, items in CONTROL_GROUPS for c, _ in items if not c.startswith(('ls_', 'rs_'))]

KEY_PRESETS = {
    'pc': {   # WASD to walk, arrows to evade, the face buttons under the right hand and the mouse
        'ls_up': ['W'], 'ls_down': ['S'], 'ls_left': ['A'], 'ls_right': ['D'],
        'rs_up': ['Up'], 'rs_down': ['Down'], 'rs_left': ['Left'], 'rs_right': ['Right'],
        'cross': ['Space', 'K'], 'square': ['J', 'Mouse1'], 'triangle': ['I', 'Mouse2'], 'circle': ['L', 'C'],
        'l1': ['LShift', 'Q'], 'r1': ['E', 'Mouse4'], 'l2': ['Z'], 'r2': ['R', 'Mouse5'],
        'l3': ['LCtrl'], 'r3': ['V'],
        'up': ['T'], 'down': ['G'], 'left': ['F'], 'right': ['H'],
        'start': ['Enter', 'Escape'], 'select': ['Tab', 'Backspace'],
    },
    'classic': {   # the runtime's old fixed map: arrows, Z/X/A/S
        'up': ['Up'], 'down': ['Down'], 'left': ['Left'], 'right': ['Right'],
        'ls_up': ['Up'], 'ls_down': ['Down'], 'ls_left': ['Left'], 'ls_right': ['Right'],
        'cross': ['Z'], 'circle': ['X'], 'square': ['A'], 'triangle': ['S'],
        'l1': ['Q'], 'r1': ['W'], 'l2': ['1'], 'r2': ['2'], 'start': ['Enter'], 'select': ['Tab'],
    },
}
PAD_DEFAULTS = {'up': 'up', 'down': 'down', 'left': 'left', 'right': 'right', 'cross': 'a', 'circle': 'b',
                'square': 'x', 'triangle': 'y', 'l1': 'lb', 'r1': 'rb', 'l2': 'lt', 'r2': 'rt',
                'l3': 'ls', 'r3': 'rs', 'start': 'start', 'select': 'back'}
PAD_BUTTONS = [('a', 'A  ·  ✕'), ('b', 'B  ·  ○'), ('x', 'X  ·  □'), ('y', 'Y  ·  △'),
               ('lb', 'LB  ·  L1'), ('rb', 'RB  ·  R1'), ('lt', 'LT  ·  L2'), ('rt', 'RT  ·  R2'),
               ('ls', 'Clique esquerdo  ·  L3'), ('rs', 'Clique direito  ·  R3'),
               ('back', 'View / Back  ·  Share'), ('start', 'Menu / Start  ·  Options'),
               ('guide', 'Xbox / PS'), ('up', 'Direcional ↑'), ('down', 'Direcional ↓'),
               ('left', 'Direcional ←'), ('right', 'Direcional →'), ('none', '(nenhum)')]
DEADZONES = [(str(v), f'{v}%' + (' (padrão)' if v == 24 else '')) for v in (0, 5, 10, 15, 20, 24, 30, 40, 50)]

# Key names as ps3recomp reads them, from Tk's keysyms.
TK_KEYS = {
    'space': 'Space', 'Return': 'Enter', 'KP_Enter': 'Enter', 'Tab': 'Tab', 'ISO_Left_Tab': 'Tab',
    'BackSpace': 'Backspace', 'Escape': 'Escape', 'Up': 'Up', 'Down': 'Down', 'Left': 'Left', 'Right': 'Right',
    'Shift_L': 'LShift', 'Shift_R': 'RShift', 'Control_L': 'LCtrl', 'Control_R': 'RCtrl',
    'Alt_L': 'LAlt', 'Alt_R': 'RAlt', 'Option_L': 'LAlt', 'Option_R': 'RAlt',
    'comma': 'Comma', 'period': 'Period', 'slash': 'Slash', 'semicolon': 'Semicolon',
    'apostrophe': 'Quote', 'quoteright': 'Quote', 'bracketleft': 'LBracket', 'bracketright': 'RBracket',
    'minus': 'Minus', 'equal': 'Equals', 'grave': 'Grave', 'quoteleft': 'Grave', 'backslash': 'Backslash',
    'Insert': 'Insert', 'Delete': 'Delete', 'Home': 'Home', 'End': 'End', 'Prior': 'PageUp',
    'Next': 'PageDown', 'Caps_Lock': 'CapsLock',
    **{f'KP_{i}': f'Num{i}' for i in range(10)}, **{f'F{i}': f'F{i}' for i in range(1, 13)},
}
KEY_LABELS = {
    'Space': 'Espaço', 'Escape': 'Esc', 'Up': '↑', 'Down': '↓', 'Left': '←', 'Right': '→',
    'LShift': 'Shift esq.', 'RShift': 'Shift dir.', 'LCtrl': 'Control esq.', 'RCtrl': 'Control dir.',
    'LAlt': 'Option esq.' if MAC else 'Alt esq.', 'RAlt': 'Option dir.' if MAC else 'Alt dir.',
    'Comma': ',', 'Period': '.', 'Slash': '/', 'Semicolon': ';', 'Quote': "'", 'LBracket': '[',
    'RBracket': ']', 'Minus': '-', 'Equals': '=', 'Grave': '`', 'Backslash': '\\',
    'PageUp': 'Page Up', 'PageDown': 'Page Down', 'CapsLock': 'Caps Lock',
    'Mouse1': '🖱 Esquerdo', 'Mouse2': '🖱 Direito', 'Mouse3': '🖱 Meio', 'Mouse4': '🖱 Botão 4',
    'Mouse5': '🖱 Botão 5', **{f'Num{i}': f'Num {i}' for i in range(10)},
}


def key_label(name):
    return KEY_LABELS.get(name, name) if name else '—'


GAME_EXE = ROOT / 'build' / 'win' / 'AscensionRecomp.exe' if WINDOWS else ROOT / 'build' / 'mac' / 'AscensionRecomp'
# On macOS the disc stays an .iso, mounted read-only at work/disc when the game
# starts; the decrypted EBOOT.ELF sits in ascension/input/.
EBOOT = (WORK / 'disc' / 'PS3_GAME' / 'USRDIR' / 'EBOOT.ELF') if WINDOWS else ROOT / 'input' / 'EBOOT.ELF'

DEFAULTS = {
    'display_mode': 'window', 'window_size': '1280x720', 'perf_overlay': '1',
    'renderer': RENDERERS[0][0], 'render_scale': '100', 'aspect': 'keep', 'scale_filter': 'linear',
    'vsync': 'auto', 'aniso': '0',
    'esc_quits': '0', 'language': '18', 'enter_button': 'cross', 'subtitles': '1',
    'keymap': KEY_PRESETS['pc'], 'padmap': PAD_DEFAULTS, 'pad_deadzone': '24',
    'mods_dir': str(ROOT / 'mods'), 'mods_enabled': [], 'mods_order': [],
    'game_exe': str(GAME_EXE), 'eboot': str(EBOOT),
    'disc_dir': '' if WINDOWS else str(WORK / 'disc'), 'disc_iso': '',
    'backup_saves': '1', 'music': '1', 'extra_env': '',
}

# Colours: the bronze and fire of Ascension's logo over near black, with
# Kratos' red for what can be pressed.
BG, PANEL, CARD, LINE = '#0b0908', '#14100e', '#1e1814', '#2e2620'
TEXT, MUTED, GOLD = '#ece2d4', '#91857a', '#e2b86a'
ACCENT, ACCENT_HI = '#9e1b16', '#c9271f'


def asset(name):
    for folder in ASSET_DIRS:
        if (folder / name).is_file():
            return folder / name
    return None


def load_settings():
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        data = {}
    s = {**DEFAULTS, **data}
    keymap = s['keymap'] if isinstance(s['keymap'], dict) else {}
    s['keymap'] = {c: [k for k in keymap.get(c, [])][:2] for _, items in CONTROL_GROUPS for c, _ in items}
    padmap = s['padmap'] if isinstance(s['padmap'], dict) else {}
    s['padmap'] = {c: padmap.get(c, PAD_DEFAULTS[c]) for c in PAD_CONTROLS}
    if s['renderer'] not in dict(RENDERERS):
        s['renderer'] = RENDERERS[0][0]
    return s


def save_settings(values):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(values, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(CONFIG_FILE)


def save_dir():
    return ROOT / 'gamedata' / 'dev_hdd0' / 'home' / '00000001' / 'savedata'


def icon_file():
    """icon-2.png as an .ico (window, taskbar and the game's window); on
    macOS the .png itself (the game's Dock icon)."""
    src = asset('icon-2.png')
    if not src or not WINDOWS:
        return src
    ico = CONFIG_DIR / 'icon.ico'
    try:
        if not ico.is_file() or ico.stat().st_mtime < src.stat().st_mtime:
            from PIL import Image
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with Image.open(src) as im:
                im.convert('RGBA').save(ico, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        return ico
    except OSError:
        return None


BUILTIN_MODS = ROOT / 'mods-builtin'
GENERATED_DIR = CONFIG_DIR / 'generated'


def read_mod_json(folder):
    try:
        data = json.loads((Path(folder) / 'mod.json').read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def all_mods(s):
    """Every mod the launcher knows, in priority order (first wins): the ones
    that come with Ascension (mods-builtin, ids '@<folder>') and the user's
    (the mods folder, ids = folder names). Each is a dict: id, path, name,
    description, builtin, meta (its mod.json)."""
    found = {}
    if BUILTIN_MODS.is_dir():
        for d in sorted(BUILTIN_MODS.iterdir()):
            if d.is_dir():
                found['@' + d.name] = (d, True)
    user = Path(s['mods_dir'])
    if user.is_dir():
        for d in sorted(user.iterdir()):
            if d.is_dir() and d.name not in found:
                found[d.name] = (d, False)
    order = [m for m in s.get('mods_order', []) if m in found]
    order += [m for m in found if m not in order]
    mods = []
    for mid in order:
        path, builtin = found[mid]
        meta = read_mod_json(path)
        mods.append({'id': mid, 'path': path, 'builtin': builtin, 'meta': meta,
                     'name': meta.get('name') or path.name,
                     'description': meta.get('description', '')})
    return mods


def enabled_mod_list(s):
    on = set(s.get('mods_enabled', []))
    return [m for m in all_mods(s) if m['id'] in on]


def ptbr_mod(s):
    """An enabled mod that brings Brazilian Portuguese (tools/make_ptbr_mod.py
    builds one from the US disc): BR_PORTUGUESE.PSARC, the US voices, and the
    language-table entry "17 pt-br BR_PORTUGUESE" (the text, R_LANG_PT-BR, is
    already on the European disc)."""
    for m in enabled_mod_list(s):
        if (m['path'] / 'BR_PORTUGUESE.PSARC').is_file() or str(m['meta'].get('language', '')).lower() == 'pt-br':
            return m
    return None


def language_options(s):
    """Brazilian Portuguese is offered only with a mod that brings it."""
    if ptbr_mod(s):
        return LANGUAGES
    return [o for o in LANGUAGES if o[0] != '17']


def effective_language(s):
    lang = s['language']
    if lang == '17' and not ptbr_mod(s):
        return '7'
    return lang


def apply_text_ops(data, ops):
    """One archive file changed by a mod: {"text": "..."} replaces it,
    {"insert_after": "<line>", "line": "<new line>"} adds a line (once)."""
    for op in ops:
        if 'text' in op:
            data = op['text'].encode('utf-8')
        elif 'insert_after' in op and 'line' in op:
            eol = b'\r\n' if b'\r\n' in data else b'\n'
            anchor, line = op['insert_after'].encode('utf-8'), op['line'].encode('utf-8')
            lines = data.split(eol)
            if line not in lines and anchor in lines:
                i = lines.index(anchor)
                lines.insert(i + 1, line)
                data = eol.join(lines)
    return data


def disc_root(s):
    """The disc's folder (the one holding PS3_GAME) when one is set, else None:
    on Windows the EBOOT.ELF's own disc decides."""
    d = s.get('disc_dir', '')
    return Path(d) if d else None


def disc_usrdir(s):
    root = disc_root(s)
    return root / 'PS3_GAME' / 'USRDIR' if root else Path(s['eboot']).parent


GAME_ID = 'BCES01741'


def read_sfo(path):
    """A PARAM.SFO's entries: {key: text or number}."""
    data = Path(path).read_bytes()
    if data[:4] != b'\0PSF':
        raise ValueError('not a PARAM.SFO')
    keys, values, count = struct.unpack_from('<III', data, 8)
    out = {}
    for i in range(count):
        koff, fmt, length, _cap, voff = struct.unpack_from('<HHIII', data, 20 + 16 * i)
        key = data[keys + koff:data.index(b'\0', keys + koff)].decode('ascii', 'replace')
        raw = data[values + voff:values + voff + length]
        out[key] = int.from_bytes(raw[:4], 'little') if fmt == 0x0404 else raw.rstrip(b'\0').decode('utf-8', 'replace')
    return out


def disc_problem(s):
    """Why the disc found is not the one the game was built from, or None
    (also when there is no disc to look at yet)."""
    root = disc_root(s)
    sfo = (root / 'PS3_GAME' if root else Path(s['eboot']).parent.parent) / 'PARAM.SFO'
    if not sfo.is_file():
        return None
    try:
        info = read_sfo(sfo)
    except (OSError, ValueError, struct.error):
        return f'o PARAM.SFO do disco não pôde ser lido ({sfo})'
    title = str(info.get('TITLE_ID', ''))
    if title != GAME_ID:
        name = str(info.get('TITLE', '')).replace('\n', ' ')
        return f'o disco é {title or "?"}{" (" + name + ")" if name else ""}, não a versão europeia {GAME_ID}'
    return None


def ensure_disc(s):
    """macOS: mount the .iso read-only at the disc folder if it is not there yet.
    Returns the folder when this call mounted it (release_disc undoes that)."""
    root = disc_root(s)
    if not root or (root / 'PS3_GAME').is_dir():
        return None
    iso = s.get('disc_iso', '')
    if MAC and iso and Path(iso).is_file():
        root.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(['hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', str(root), iso],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise OSError('hdiutil: ' + (r.stderr or r.stdout).strip())
        return root
    return None


def release_disc(root):
    """Unmount a disc ensure_disc mounted; a busy one stays (nothing is lost)."""
    if root and MAC:
        subprocess.run(['hdiutil', 'detach', str(root)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


MODS_LOCK = threading.Lock()     # PLAY and the build after Salvar write the same archives


def compose_mods(s, log=lambda m: None):
    with MODS_LOCK:
        return _compose_mods(s, log)


def prebuild_mods(s):
    """The mods' archives built ahead of PLAY, when the disc is there."""
    try:
        if disc_usrdir(s).is_dir():
            compose_mods(s)
    except Exception:       # PLAY builds them again and reports what fails
        pass


def _compose_mods(s, log):
    """The folders for PS3_MODS: first the archives the launcher builds from
    the enabled mods' recipes ("psarc_patches" in mod.json, applied to the
    copy of that archive the highest-priority mod ships, or to the disc's),
    then every enabled mod's own files. Rebuilt only when an input changes."""
    mods = enabled_mod_list(s)
    usrdir = disc_usrdir(s)
    wanted = {}
    for m in mods:
        for archive, files in (m['meta'].get('psarc_patches') or {}).items():
            wanted.setdefault(archive, [])
    dirs = []
    if wanted:
        GENERATED_DIR.mkdir(parents=True, exist_ok=True)
        import importlib.util
        spec = importlib.util.spec_from_file_location('psarc_replace', ROOT / 'tools' / 'psarc_replace.py')
        pr = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pr)
        for archive in wanted:
            base = next((m['path'] / archive for m in mods if (m['path'] / archive).is_file()), usrdir / archive)
            # lowest priority first, so the first mod in the list has the last word
            ops = {}
            for m in reversed(mods):
                for inner, op in ((m['meta'].get('psarc_patches') or {}).get(archive) or {}).items():
                    ops.setdefault(inner, []).append(op if isinstance(op, dict) else {'text': str(op)})
            st = base.stat()
            key = json.dumps([str(base), st.st_size, int(st.st_mtime), ops], sort_keys=True)
            out = GENERATED_DIR / archive
            keyf = GENERATED_DIR / (archive + '.key')
            if not (out.is_file() and keyf.is_file() and keyf.read_text(encoding='utf-8') == key):
                log(f'montando {archive}')
                src = pr.Psarc(str(base))
                replace = {inner: apply_text_ops(src.read(src.index_of(inner)), oplist)
                           for inner, oplist in ops.items() if inner in src.names}
                pr.write(src, str(out), replace)
                keyf.write_text(key, encoding='utf-8')
        dirs.append(str(GENERATED_DIR))
    dirs += [str(m['path']) for m in mods]
    return dirs


def keymap_env(keymap):
    """PS3_KEYMAP: "cross=Space,K;square=J,Mouse1;..." (libs/input/pad_keymap.h)."""
    return ';'.join(f'{c}=' + ','.join(keys) for c, keys in keymap.items() if keys)


def padmap_env(padmap):
    return ';'.join(f'{c}={b}' for c, b in padmap.items())


def game_environment(s):
    env = dict(os.environ)
    env['PS3_SYS_LANG'] = effective_language(s)
    env['PS3_ENTER_BUTTON'] = s['enter_button']
    env['PS3_WINDOW_SIZE'] = s['window_size']
    env['PS3_FULLSCREEN'] = '1' if s['display_mode'] == 'fullscreen' else '0'
    env['PS3_ESC_QUITS'] = s['esc_quits']
    env['LD_PERF_OVERLAY'] = s['perf_overlay']
    env['PS3_OVERLAY_FONT'] = str(HERE / 'Cinzel-Black.ttf')   # RPCS3's overlay in the launcher's font
    if MAC:
        env['PS3RECOMP_METAL_FPS'] = s['perf_overlay']    # in the window's title
    # Video
    env.pop('PS3_RSX', None)
    env.pop('PS3_RSX_RENDERER', None)
    if s['renderer'].startswith('rpcs3'):
        env['PS3_RSX'] = 'rpcs3'
        env['PS3_RSX_RENDERER'] = 'opengl' if s['renderer'] == 'rpcs3-opengl' else 'vulkan'
        if MAC and s['renderer'] == 'rpcs3-vulkan':
            icd = next((p for p in (
                '/opt/homebrew/opt/molten-vk/etc/vulkan/icd.d/MoltenVK_icd.json',
                '/usr/local/opt/molten-vk/etc/vulkan/icd.d/MoltenVK_icd.json') if Path(p).is_file()), None)
            if icd and not env.get('VK_ICD_FILENAMES'):
                env['VK_ICD_FILENAMES'] = icd
            lib = '/opt/homebrew/lib' if Path('/opt/homebrew/lib').is_dir() else '/usr/local/lib'
            env['DYLD_FALLBACK_LIBRARY_PATH'] = lib + os.pathsep + env.get('DYLD_FALLBACK_LIBRARY_PATH', '')
    env['PS3_RENDER_SCALE'] = s['render_scale']
    env['PS3_ASPECT'] = s['aspect']
    env['PS3_SCALE_FILTER'] = s['scale_filter']
    env['PS3_ANISO'] = s['aniso']
    if s['vsync'] in ('0', '1'):
        env['PS3_VSYNC'] = s['vsync']
    else:
        env.pop('PS3_VSYNC', None)
    # Controls
    env['PS3_KEYMAP'] = keymap_env(s['keymap']) or 'start=Enter'
    env['PS3_PADMAP'] = padmap_env(s['padmap'])
    env['PS3_PAD_DEADZONE'] = s['pad_deadzone']
    root = disc_root(s)
    if root:
        env['PS3_VFS_ROOT'] = str(root)
    # The disc image is mounted read-only, so it reports no free space and the
    # game exits with NOSPACE. Saves and the cache live beside the disc.
    for key, folder in (('PS3_HDD0_ROOT', ROOT / 'gamedata' / 'dev_hdd0'),
                        ('PS3_HDD1_ROOT', ROOT / 'gamedata' / 'dev_hdd1')):
        folder.mkdir(parents=True, exist_ok=True)
        env[key] = str(folder)
    mods = compose_mods(s)
    if mods:
        env['PS3_MODS'] = ';'.join(mods)
    else:
        env.pop('PS3_MODS', None)
    ico = icon_file()
    if ico:
        env['PS3_WINDOW_ICON'] = str(ico)
    for item in s.get('extra_env', '').replace('\n', ';').split(';'):
        if '=' in item:
            k, v = item.split('=', 1)
            if k.strip():
                env[k.strip()] = v.strip()
    return env


def apply_save_settings(s):
    """Language and subtitles into the game's system save (BCES01741-SYSDATA).

    The game asks the console language only when it makes that save, at the
    first start; after that it reads its own copy. SAVEDATA (4 KB, no checksum)
    is a 16-byte header and the options block the boot hands out
    (func_0001A680): +0x0C text language (to func_003963A8), +0x0D voice
    language (to the audio side, func_00396348), +0x18 subtitles (to
    func_00032C74, which -subtitlesOn also drives). With English the game writes
    18 (English UK, the European text) and 1. Returns what it changed."""
    path = save_dir() / 'BCES01741-SYSDATA' / 'SAVEDATA'
    try:
        data = bytearray(path.read_bytes())
    except OSError:
        return None                                  # no save yet: the console language decides
    if len(data) < 0x29 or data[0:4] != bytes((0, 0, 0, 1)):
        return None
    lang = int(effective_language(s))                # 17 only with the PT-BR mod
    if lang in (1, 18):
        text, voice = 18, 1
    else:
        text = voice = lang
    new = bytearray(data)
    new[0x1C], new[0x1D] = text, voice
    new[0x28] = 1 if s.get('subtitles') == '1' else 0
    if new != data:
        path.write_bytes(bytes(new))
        return True
    return False


def tree_signature(folder):
    """Relative path, size and mtime of every file (copytree keeps mtimes)."""
    out = []
    for dirpath, _dirs, files in os.walk(folder):
        for name in files:
            st = (Path(dirpath) / name).stat()
            out.append((os.path.relpath(Path(dirpath) / name, folder), st.st_size, int(st.st_mtime)))
    return sorted(out)


def backup_saves():
    """A copy of the saves, unless the newest backup already has them as they
    are: starting the game ten times without playing keeps the older ones."""
    src = save_dir()
    if not src.is_dir() or not any(src.iterdir()):
        return None
    folder = ROOT / 'gamedata' / 'save-backups'
    backups = sorted(folder.iterdir()) if folder.is_dir() else []
    if backups and tree_signature(backups[-1]) == tree_signature(src):
        return backups[-1]
    dst = folder / time.strftime('%Y%m%d-%H%M%S')
    shutil.copytree(src, dst)
    backups = sorted(folder.iterdir())
    for old in backups[:-10]:                       # keep the last ten
        shutil.rmtree(old, ignore_errors=True)
    return dst


def backup_list():
    """The save backups, newest first."""
    folder = ROOT / 'gamedata' / 'save-backups'
    return sorted((d for d in folder.iterdir() if d.is_dir()), reverse=True) if folder.is_dir() else []


def restore_saves(backup):
    """The saves as they were in `backup`. The current ones are backed up
    first; the copy is taken before that, since it can drop the oldest."""
    dst = save_dir()
    tmp = dst.with_name('savedata.restoring')
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.copytree(backup, tmp)
    backup_saves()
    shutil.rmtree(dst, ignore_errors=True)
    tmp.rename(dst)


def missing(s):
    out = []
    if not Path(s['game_exe']).is_file():
        out.append('o executável do jogo (' + s['game_exe'] + ')')
    if not Path(s['eboot']).is_file():
        out.append('o EBOOT.ELF do disco (' + s['eboot'] + ')')
    root = disc_root(s)
    if root and not (root / 'PS3_GAME').is_dir() and not (MAC and Path(s.get('disc_iso') or '-').is_file()):
        out.append('o disco (' + str(root) + ('; ou a imagem .iso' if MAC else '') + ')')
    return out


def prepare_game(s, status=lambda m: None):
    """Everything before the game starts (it can take a while: the disc,
    the saves, the mods' archives). Returns the environment and the disc
    folder it mounted, if any."""
    status('Preparando o jogo…')
    mounted = ensure_disc(s)
    problem = disc_problem(s)
    if problem:
        release_disc(mounted)
        raise OSError(problem[0].upper() + problem[1:] + '.')
    if s.get('backup_saves') == '1':
        status('Copiando os saves…')
        backup_saves()
    apply_save_settings(s)
    status('Preparando os mods…')
    return game_environment(s), mounted


def start_game(s, env, log_path, parent=None):
    """Start the game; with `parent` (a window handle) it renders inside that
    window. The previous run's log is kept as last_run.prev.log."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if log_path.is_file():
        log_path.replace(log_path.with_suffix('.prev.log'))
    log = open(log_path, 'w', encoding='utf-8', errors='replace')
    flags = subprocess.CREATE_NO_WINDOW if WINDOWS else 0
    if parent:
        env = {**env, 'PS3_PARENT_HWND': str(parent)}
    try:
        return subprocess.Popen([s['game_exe'], s['eboot']], cwd=str(ROOT), env=env,
                                stdout=log, stderr=subprocess.STDOUT, creationflags=flags), log
    except BaseException:
        log.close()
        raise


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
                self.error = 'não abriu music.mp3'
        elif MAC and path and self.player:
            self.ok = True
            if self._cached_aac().is_file() and self._cached_aac().stat().st_mtime >= path.stat().st_mtime:
                self.path, self._converted = self._cached_aac(), True   # afplay rejected this MP3 before
        elif MAC and not path:
            self.error = 'sem music.mp3'
        elif MAC:
            self.error = 'afplay não encontrado'

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
                self.error = (text or f'afplay saiu com código {code}')[:80]
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


class Launcher:
    FADE_STEPS, FADE_MS, HOLD_MS = 30, 40, 7000

    def __init__(self, root):
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
        self.tk, self.ttk, self.filedialog, self.messagebox = tk, ttk, filedialog, messagebox
        self.root = root
        self.s = load_settings()
        self.vars = {}
        self.dynamic = {}
        self.mod_vars = {}
        self.mod_order = list(self.s['mods_order'])
        self.keymap = {c: list(k) for c, k in self.s['keymap'].items()}
        self.padmap = dict(self.s['padmap'])
        self.capturing = None
        self.process = None
        self.preparing = False
        self.mounted = None        # the disc folder the launcher mounted (macOS)
        if MAC:   # Tk on macOS counts 72 points to the inch: the sizes below assume Windows' 96
            root.tk.call('tk', 'scaling', 1.33)
        self.heading = 'Georgia'
        if register_font(HERE / 'Cinzel-Black.ttf'):
            from tkinter import font as tkfont
            families = set(tkfont.families(root))
            self.heading = next((f for f in ('Cinzel Black', 'Cinzel') if f in families), 'Georgia')
        self.ui = 'Segoe UI' if WINDOWS else 'Helvetica Neue' if MAC else 'DejaVu Sans'
        root.title(f'{APP_NAME} (PC)')
        root.configure(bg=BG)
        w, h = 1180, 740
        root.geometry(f'{w}x{h}+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 3}')
        root.minsize(1000, 660)
        ico = icon_file()
        if ico:
            try:
                if WINDOWS:
                    root.iconbitmap(default=str(ico))
                else:
                    self.icon_photo = tk.PhotoImage(file=str(ico))
                    root.iconphoto(True, self.icon_photo)
            except tk.TclError:
                pass
        self.style()
        self.bg_sources = [p for p in (asset(n) for n in BACKGROUNDS) if p]
        self.bg_index, self.bg_cache, self.bg_size = 0, {}, None
        self.logo_src = asset('logo.png')
        self.music = Music() if not SHOT else Music.__new__(Music)
        if SHOT:
            self.music.ok = False
            self.music.error = ''
        self.build()
        self.show('home')
        self.saved = self.gather()
        if self.s.get('music') == '1':
            self.music.play()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(400, self.watch_changes)
        root.after(self.HOLD_MS, self.next_background)

    # ---- look -------------------------------------------------------------------------------
    def style(self):
        ttk = self.ttk
        s = ttk.Style(self.root)
        s.theme_use('clam')
        base = (self.ui, 10)
        self.root.option_add('*TCombobox*Listbox.background', CARD)
        self.root.option_add('*TCombobox*Listbox.foreground', TEXT)
        self.root.option_add('*TCombobox*Listbox.selectBackground', ACCENT)
        self.root.option_add('*TCombobox*Listbox.font', base)
        s.configure('.', background=PANEL, foreground=TEXT, fieldbackground=CARD, bordercolor=LINE,
                    lightcolor=LINE, darkcolor=LINE, troughcolor=CARD, focuscolor=ACCENT, font=base)
        s.configure('TFrame', background=PANEL)
        s.configure('TLabel', background=PANEL, foreground=TEXT)
        s.configure('Muted.TLabel', background=PANEL, foreground=MUTED, font=(self.ui, 9))
        s.configure('Section.TLabel', background=PANEL, foreground=GOLD, font=(self.heading, 12))
        s.configure('Page.TLabel', background=PANEL, foreground=TEXT, font=(self.heading, 20))
        s.configure('TCheckbutton', background=PANEL, foreground=TEXT, indicatorcolor=CARD,
                    indicatorbackground=CARD, padding=(0, 3))
        s.map('TCheckbutton', background=[('active', PANEL)],
              indicatorbackground=[('selected', ACCENT_HI), ('active', LINE)],
              indicatorforeground=[('selected', '#fbf1e2')])
        s.configure('TCombobox', arrowcolor=GOLD, foreground=TEXT, padding=5, arrowsize=14)
        s.map('TCombobox', fieldbackground=[('readonly', CARD)], foreground=[('readonly', TEXT)],
              selectbackground=[('readonly', CARD)], selectforeground=[('readonly', TEXT)])
        s.configure('TEntry', foreground=TEXT, insertcolor=TEXT, padding=5)
        s.configure('TButton', background=CARD, foreground=TEXT, padding=(14, 6), borderwidth=1)
        s.map('TButton', background=[('active', LINE), ('disabled', PANEL)], foreground=[('disabled', MUTED)])
        s.configure('Play.TButton', background=ACCENT, foreground='#fbf1e2', font=(self.heading, 16),
                    padding=(44, 10), borderwidth=0)
        s.map('Play.TButton', background=[('active', ACCENT_HI), ('disabled', '#2e1c1c')],
              foreground=[('disabled', '#8a7a78')])
        s.configure('Vertical.TScrollbar', background=CARD, arrowcolor=MUTED, troughcolor=PANEL, bordercolor=PANEL)

    # ---- settings widgets -------------------------------------------------------------------
    def var(self, key):
        if key not in self.vars:
            self.vars[key] = self.tk.StringVar(value=str(self.s.get(key, DEFAULTS.get(key, ''))))
        return self.vars[key]

    def choice(self, parent, key, options, width=28):
        """A read-only combobox showing labels for stored values. `options` may
        be a function, re-read by refresh_choices when what it depends on changes."""
        source = options
        options = source() if callable(source) else source
        shown = self.tk.StringVar()
        box = self.ttk.Combobox(parent, textvariable=shown, state='readonly', width=width)
        box.maps = (dict(options), {label: value for value, label in options})
        box.configure(values=[label for _, label in options])
        shown.set(box.maps[0].get(self.var(key).get(), options[0][1]))
        shown.trace_add('write', lambda *_: box.maps[1].get(shown.get()) and self.var(key).set(box.maps[1][shown.get()]))
        box.bind('<MouseWheel>', lambda e: 'break')
        if callable(source):
            self.dynamic.setdefault(key, []).append((box, shown, source))
        return box

    def refresh_choices(self, key, fallback):
        for box, shown, source in self.dynamic.get(key, []):
            options = source()
            box.maps = (dict(options), {label: value for value, label in options})
            box.configure(values=[label for _, label in options])
            if self.var(key).get() not in box.maps[0]:
                self.var(key).set(fallback)
            shown.set(box.maps[0].get(self.var(key).get(), options[0][1]))

    def page(self, name, title, subtitle):
        tk, ttk = self.tk, self.ttk
        outer = tk.Frame(self.content, bg=PANEL)
        canvas = tk.Canvas(outer, bg=PANEL, highlightthickness=0, bd=0)
        inner = ttk.Frame(canvas, padding=(34, 26, 34, 26))
        inner.bind('<Configure>', lambda _e: canvas.configure(scrollregion=canvas.bbox('all')))
        win = canvas.create_window(0, 0, window=inner, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(win, width=e.width))
        canvas.pack(side='left', fill='both', expand=True)
        outer.scroll = lambda n: canvas.yview_scroll(n, 'units')
        ttk.Label(inner, text=title, style='Page.TLabel').grid(row=0, column=0, columnspan=3, sticky='w')
        ttk.Label(inner, text=subtitle, style='Muted.TLabel').grid(row=1, column=0, columnspan=3, sticky='w', pady=(2, 8))
        inner.columnconfigure(2, weight=1)
        inner.next_row = 2
        self.pages[name] = outer
        return inner

    def section(self, f, title):
        r = f.next_row
        self.ttk.Label(f, text=title.upper(), style='Section.TLabel').grid(row=r, column=0, columnspan=3, sticky='w', pady=(18, 0))
        self.tk.Frame(f, bg=LINE, height=1).grid(row=r + 1, column=0, columnspan=3, sticky='we', pady=(3, 8))
        f.next_row += 2

    def row(self, f, title, widget, hint=None):
        r = f.next_row
        self.ttk.Label(f, text=title).grid(row=r, column=0, sticky='w', pady=6, padx=(0, 24))
        widget.grid(row=r, column=1, sticky='w')
        if hint:
            self.ttk.Label(f, text=hint, style='Muted.TLabel', wraplength=360, justify='left').grid(
                row=r, column=2, sticky='w', padx=(18, 0))
        f.next_row += 1

    def note(self, f, text):
        self.ttk.Label(f, text=text, style='Muted.TLabel', wraplength=760, justify='left').grid(
            row=f.next_row, column=0, columnspan=3, sticky='w', pady=(6, 0))
        f.next_row += 1

    def path_row(self, f, key, title, folder=False, hint=None):
        holder = self.ttk.Frame(f)
        self.ttk.Entry(holder, textvariable=self.var(key), width=58).pack(side='left')

        def browse():
            current = self.var(key).get()
            if folder:
                p = self.filedialog.askdirectory(initialdir=current or str(ROOT))
            else:
                p = self.filedialog.askopenfilename(initialdir=str(Path(current).parent) if current else str(ROOT))
            if p:
                self.var(key).set(str(Path(p)))
        self.ttk.Button(holder, text='Procurar…', command=browse).pack(side='left', padx=(8, 0))
        self.row(f, title, holder, hint)

    # ---- layout -----------------------------------------------------------------------------
    def build(self):
        tk = self.tk
        side = self.side = tk.Frame(self.root, bg=BG, width=230)
        side.pack(side='left', fill='y')
        side.pack_propagate(False)
        self.side_logo = tk.Label(side, bg=BG, bd=0)
        self.side_logo.pack(anchor='w', padx=18, pady=(22, 18))
        self.side_logo_image = self.scaled_logo(196)
        if self.side_logo_image:
            self.side_logo.configure(image=self.side_logo_image)
        else:
            self.side_logo.configure(text='GOD OF WAR\nASCENSION', fg=GOLD, font=(self.heading, 15), justify='left')
        self.nav, self.current = {}, None
        for name, title in (('home', 'Início'), ('video', 'Vídeo'), ('controls', 'Controles'), ('game', 'Jogo'),
                            ('mods', 'Mods'), ('advanced', 'Avançado'), ('about', 'Sobre')):
            item = tk.Label(side, text='    ' + title, bg=BG, fg=TEXT, anchor='w', font=(self.heading, 12),
                            pady=11, cursor='hand2')
            item.pack(fill='x')
            item.bind('<Button-1>', lambda _e, n=name: self.show(n))
            item.bind('<Enter>', lambda _e, n=name: n != self.current and self.nav[n].configure(bg='#1a1411'))
            item.bind('<Leave>', lambda _e, n=name: n != self.current and self.nav[n].configure(bg=BG))
            self.nav[name] = item
        tk.Frame(side, bg=BG).pack(fill='both', expand=True)
        self.music_label = tk.Label(side, text='', bg=BG, fg=MUTED, font=(self.ui, 9), cursor='hand2')
        self.music_label.pack(anchor='w', padx=22, pady=(0, 6))
        self.music_label.bind('<Button-1>', lambda _e: self.toggle_music())
        self.refresh_music_label()
        tk.Label(side, text=('F11 ou Ctrl+Cmd+F' if MAC else 'F11 ou Alt+Enter') + ' no jogo:\ntela cheia', bg=BG, fg=MUTED, font=(self.ui, 9),
                 justify='left').pack(anchor='w', padx=22, pady=(0, 4))
        tk.Label(side, text=f'v{VERSION} · recompilação PS3 → PC', bg=BG, fg=MUTED, font=(self.ui, 9)).pack(
            anchor='w', padx=22, pady=(0, 18))

        right = self.right = tk.Frame(self.root, bg=PANEL)
        right.pack(side='left', fill='both', expand=True)
        bar = tk.Frame(right, bg=BG, height=76)
        bar.pack(fill='x', side='bottom')
        bar.pack_propagate(False)
        self.status = tk.Label(bar, text='', bg=BG, fg=MUTED, font=(self.ui, 10), anchor='w', justify='left')
        self.status.pack(side='left', padx=24)
        self.play_button = self.ttk.Button(bar, text='JOGAR', style='Play.TButton', command=self.play)
        self.play_button.pack(side='right', padx=(10, 24), pady=12)
        self.save_button = self.ttk.Button(bar, text='Salvar', command=self.save, state='disabled')
        self.save_button.pack(side='right', pady=12)
        self.content = tk.Frame(right, bg=PANEL)
        self.content.pack(fill='both', expand=True)

        self.pages = {}
        self.build_home()
        self.build_video()
        self.build_controls()
        self.build_game()
        self.build_mods()
        self.build_advanced()
        self.build_about()
        self.refresh_choices('language', '7')   # PT-BR only while its mod is on
        self.root.bind_all('<MouseWheel>', self.wheel)
        if not (WINDOWS or MAC) and self.tk.TkVersion < 8.7:   # X11 before Tk 8.7: the wheel is buttons 4 and 5
            self.root.bind_all('<Button-4>', lambda e: self.wheel(e, -1))
            self.root.bind_all('<Button-5>', lambda e: self.wheel(e, 1))
        self.refresh_status()

    def wheel(self, event, units=None):
        page = self.pages.get(self.current)
        if hasattr(page, 'scroll') and 'combobox' not in str(event.widget).lower():
            page.scroll(units if units is not None else -event.delta if MAC else int(-event.delta / 120))

    def show(self, name):
        self.cancel_capture()
        for p in self.pages.values():
            p.pack_forget()
        self.pages[name].pack(fill='both', expand=True)
        self.current = name
        for n, item in self.nav.items():
            item.configure(bg=PANEL if n == name else BG, fg=GOLD if n == name else TEXT)
        if name == 'mods':
            self.refresh_mods()
        elif name == 'game':
            self.refresh_backups()

    # ---- home: backgrounds that cross-fade, the logo, quick settings --------------------------
    def build_home(self):
        tk, ttk = self.tk, self.ttk
        page = tk.Frame(self.content, bg=PANEL)
        self.pages['home'] = page
        self.banner = tk.Canvas(page, bg=BG, highlightthickness=0, bd=0)
        self.banner.pack(fill='both', expand=True)
        self.banner_item = self.banner.create_image(0, 0, anchor='nw')
        self.banner.bind('<Configure>', lambda _e: self.root.after_idle(self.draw_banner))
        quick = ttk.Frame(page, padding=(30, 12, 30, 14))
        quick.pack(fill='x')
        ttk.Label(quick, text='CONFIGURAÇÕES RÁPIDAS', style='Section.TLabel').grid(row=0, column=0, columnspan=4, sticky='w')
        tk.Frame(quick, bg=LINE, height=1).grid(row=1, column=0, columnspan=4, sticky='we', pady=(3, 8))
        items = (('Modo de exibição', 'display_mode', DISPLAY_MODES), ('Tamanho da janela', 'window_size', WINDOW_SIZES),
                 ('Idioma', 'language', self.languages), ('Contador de FPS', 'perf_overlay', ON_OFF))
        for i, (title, key, options) in enumerate(items):
            r, c = 2 + i // 2, (i % 2) * 2
            ttk.Label(quick, text=title).grid(row=r, column=c, sticky='w', pady=5, padx=(0, 14))
            self.choice(quick, key, options, width=24).grid(row=r, column=c + 1, sticky='w', padx=(0, 46))

    def cover(self, path, w, h):
        """The image scaled to cover w x h, darkened toward the left and bottom."""
        from PIL import Image
        key = (path, w, h)
        if key in self.bg_cache:
            return self.bg_cache[key]
        with Image.open(path) as im:
            im = im.convert('RGB')
            scale = max(w / im.width, h / im.height)
            im = im.resize((max(w, round(im.width * scale)), max(h, round(im.height * scale))), Image.LANCZOS)
            left, top = (im.width - w) // 2, max(0, (im.height - h) // 3)
            im = im.crop((left, top, left + w, top + h))
        from PIL import ImageChops
        # Left: dark behind the logo. Bottom: into the panel below.
        left = Image.new('L', (256, 1))
        left.putdata([max(40, 200 - int(320 * x / 256)) for x in range(256)])
        bottom = Image.new('L', (1, 256))
        bottom.putdata([int(255 * max(0.0, (y - 141) / 115) ** 1.6) for y in range(256)])
        shade = ImageChops.lighter(left.resize((w, h), Image.BILINEAR), bottom.resize((w, h), Image.BILINEAR))
        dark = Image.new('RGB', (w, h), PANEL)
        im = Image.composite(dark, im, shade)
        if len(self.bg_cache) > 12:
            self.bg_cache.clear()
        self.bg_cache[key] = im
        return im

    def scaled_logo(self, width):
        if not self.logo_src:
            return None
        try:
            from PIL import Image, ImageTk
            with Image.open(self.logo_src) as im:
                im = im.convert('RGBA')
                return ImageTk.PhotoImage(im.resize((width, round(im.height * width / im.width)), Image.LANCZOS))
        except OSError:
            return None

    def banner_frame(self, index, w, h):
        from PIL import Image
        im = self.cover(self.bg_sources[index], w, h).copy()
        if self.logo_src:
            if self.bg_size != (w, h):
                with Image.open(self.logo_src) as lg:
                    lg = lg.convert('RGBA')
                    lw = min(560, int(w * 0.48))
                    self.logo_banner = lg.resize((lw, round(lg.height * lw / lg.width)), Image.LANCZOS)
            im.paste(self.logo_banner, (int(w * 0.04), int(h * 0.08)), self.logo_banner)
        return im

    def draw_banner(self, blend=None):
        if not self.bg_sources:
            return
        from PIL import Image, ImageTk
        w, h = self.banner.winfo_width(), self.banner.winfo_height()
        if w < 50 or h < 50:
            return
        if self.bg_size != (w, h):
            self.frames = {}
        if self.bg_index not in self.frames:
            self.frames[self.bg_index] = self.banner_frame(self.bg_index, w, h)
        self.bg_size = (w, h)
        im = self.frames[self.bg_index]
        if blend:
            nxt, t = blend
            if nxt not in self.frames:
                self.frames[nxt] = self.banner_frame(nxt, w, h)
            im = Image.blend(im, self.frames[nxt], t)
        self.banner_photo = ImageTk.PhotoImage(im)
        self.banner.itemconfigure(self.banner_item, image=self.banner_photo)

    def next_background(self):
        if len(self.bg_sources) < 2 or self.current != 'home' or self.process:
            self.root.after(self.HOLD_MS, self.next_background)
            return
        nxt = (self.bg_index + 1) % len(self.bg_sources)

        def step(i):
            if i > self.FADE_STEPS:
                self.bg_index = nxt
                self.draw_banner()
                self.root.after(self.HOLD_MS, self.next_background)
                return
            t = i / self.FADE_STEPS
            self.draw_banner((nxt, t * t * (3 - 2 * t)))    # smoothstep
            self.root.after(self.FADE_MS, step, i + 1)
        step(1)

    # ---- pages ------------------------------------------------------------------------------
    def build_video(self):
        f = self.page('video', 'Vídeo', 'Renderizador, janela e imagem do jogo.')
        rpcs3 = 'Só com o renderizador RPCS3.'
        self.section(f, 'Renderizador')
        if MAC:
            hint = ('RPCS3 · Vulkan usa o MoltenVK (o jogo precisa de RPCS3=1 scripts/mac/build.sh, '
                    'depois de scripts/mac/build-gpu.sh). Live draw desenha com Metal.')
        elif WINDOWS:
            hint = ('RPCS3: o renderizador do RPCS3 (pede o jogo compilado com -DASCENSION_RPCS3_RSX=ON). '
                    'Live draw: o desenho próprio do ps3recomp.')
        else:
            hint = 'RPCS3: Vulkan ou OpenGL (o jogo compilado com -DASCENSION_RPCS3_RSX=ON).'
        self.row(f, 'Renderizador', self.choice(f, 'renderer', RENDERERS), hint)
        self.row(f, 'Resolução interna', self.choice(f, 'render_scale', RENDER_SCALES),
                 'O jogo desenha em 1280 x 720; acima disso fica mais nítido e pesa mais na GPU. ' + rpcs3)
        self.row(f, 'Filtro anisotrópico', self.choice(f, 'aniso', ANISO_LEVELS),
                 'Texturas vistas de lado mais nítidas. ' + rpcs3)
        self.section(f, 'Exibição')
        self.row(f, 'Modo de exibição', self.choice(f, 'display_mode', DISPLAY_MODES),
                 'No jogo, ' + ('F11 ou Ctrl+Cmd+F' if MAC else 'F11 ou Alt+Enter') + ' alterna entre janela e tela cheia.')
        self.row(f, 'Tamanho da janela', self.choice(f, 'window_size', WINDOW_SIZES),
                 'O tamanho da janela do jogo' + (' (em pixels; numa tela Retina ocupa metade em pontos).' if MAC else '.'))
        self.row(f, 'Proporção', self.choice(f, 'aspect', ASPECTS),
                 'Esticar deforma a imagem numa janela que não é 16:9.' + ('' if MAC else ' ' + rpcs3))
        self.row(f, 'Escala da imagem', self.choice(f, 'scale_filter', SCALE_FILTERS),
                 'Como a imagem é ampliada até a janela.' + ('' if MAC else ' ' + rpcs3))
        self.row(f, 'Sincronização vertical', self.choice(f, 'vsync', VSYNC_MODES),
                 'Ligada: sem cortes na imagem, mas com um pouco mais de atraso. Automático: Metal e live draw '
                 'ligam, RPCS3 desliga.')
        self.section(f, 'Informações na tela')
        self.row(f, 'Contador de FPS', self.choice(f, 'perf_overlay', ON_OFF),
                 'No macOS, FPS e tempo de quadro no título da janela.' if MAC else
                 'FPS, tempo de quadro, velocidade, CPU e GPU no canto superior direito.')

    # ---- controls: keyboard and mouse, controller ---------------------------------------------
    def build_controls(self):
        tk, ttk = self.tk, self.ttk
        f = self.page('controls', 'Controles',
                      'Teclado, mouse e controle funcionam juntos; o que estiver ligado responde.')
        self.section(f, 'Geral')
        self.row(f, 'Botão de confirmar', self.choice(f, 'enter_button', ENTER_BUTTONS),
                 'Qual botão aceita nos menus do sistema.')
        self.row(f, 'Esc fecha o jogo', self.choice(f, 'esc_quits', ON_OFF),
                 'Ligado, Esc fecha o jogo em vez de chegar a ele (por padrão Esc é START).')

        bar = tk.Frame(f, bg=PANEL)
        bar.grid(row=f.next_row, column=0, columnspan=3, sticky='we', pady=(22, 0))
        tk.Frame(f, bg=LINE, height=1).grid(row=f.next_row + 1, column=0, columnspan=3, sticky='we')
        f.next_row += 2
        self.control_tabs, self.control_tab_frames = {}, {}
        for name, title in (('keyboard', 'TECLADO E MOUSE'), ('pad', 'CONTROLE')):
            holder = tk.Frame(bar, bg=PANEL)
            holder.pack(side='left', padx=(0, 6))
            label = tk.Label(holder, text=title, bg=PANEL, fg=TEXT, font=(self.heading, 11), padx=16, pady=8,
                             cursor='hand2')
            label.pack()
            mark = tk.Frame(holder, bg=PANEL, height=3)
            mark.pack(fill='x')
            label.bind('<Button-1>', lambda _e, n=name: self.show_control_tab(n))
            self.control_tabs[name] = (label, mark)
        for name in ('keyboard', 'pad'):
            frame = tk.Frame(f, bg=PANEL)
            frame.grid(row=f.next_row, column=0, columnspan=3, sticky='we', pady=(10, 0))
            frame.columnconfigure(3, weight=1)
            self.control_tab_frames[name] = frame
        f.next_row += 1
        self.build_keyboard_tab(self.control_tab_frames['keyboard'])
        self.build_pad_tab(self.control_tab_frames['pad'])
        self.show_control_tab('keyboard')

    def show_control_tab(self, name):
        self.cancel_capture()
        for n, (label, mark) in self.control_tabs.items():
            label.configure(fg=GOLD if n == name else MUTED)
            mark.configure(bg=ACCENT_HI if n == name else PANEL)
            if n == name:
                self.control_tab_frames[n].grid()
            else:
                self.control_tab_frames[n].grid_remove()

    def build_keyboard_tab(self, f):
        tk, ttk = self.tk, self.ttk
        top = tk.Frame(f, bg=PANEL)
        top.grid(row=0, column=0, columnspan=4, sticky='we', pady=(0, 6))
        tk.Label(top, text='Clique numa tecla e aperte a nova tecla ou botão do mouse. Esc cancela; × apaga.',
                 bg=PANEL, fg=MUTED, font=(self.ui, 9)).pack(side='left')
        ttk.Button(top, text='Clássico (setas)', command=lambda: self.key_preset('classic')).pack(side='right')
        ttk.Button(top, text='Padrão (WASD)', command=lambda: self.key_preset('pc')).pack(side='right', padx=(0, 8))
        self.key_cells = {}
        r = 1
        for group, items in CONTROL_GROUPS:
            tk.Label(f, text=group.upper(), bg=PANEL, fg=GOLD, font=(self.heading, 10)).grid(
                row=r, column=0, columnspan=4, sticky='w', pady=(14, 4))
            if r == 1:
                for col, head in ((1, 'PRINCIPAL'), (2, 'ALTERNATIVA')):
                    tk.Label(f, text=head, bg=PANEL, fg=MUTED, font=(self.ui, 8)).grid(row=r, column=col, sticky='sw',
                                                                                    pady=(14, 4))
            r += 1
            for control, title in items:
                tk.Label(f, text=title, bg=PANEL, fg=TEXT, font=(self.ui, 10), anchor='w', width=26).grid(
                    row=r, column=0, sticky='w', pady=2)
                for slot in (0, 1):
                    self.key_cells[(control, slot)] = self.key_cell(f, control, slot, r, 1 + slot)
                r += 1
        self.refresh_keys()

    def key_cell(self, parent, control, slot, row, column):
        tk = self.tk
        cell = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=LINE)
        cell.grid(row=row, column=column, sticky='w', padx=(0, 10), pady=2)
        label = tk.Label(cell, text='', bg=CARD, fg=TEXT, font=(self.ui, 10), width=16, pady=4, cursor='hand2')
        label.pack(side='left')
        clear = tk.Label(cell, text='×', bg=CARD, fg=MUTED, font=(self.ui, 11), padx=6, cursor='hand2')
        clear.pack(side='left')
        label.bind('<Button-1>', lambda _e: self.start_capture(control, slot))
        clear.bind('<Button-1>', lambda _e: self.set_key(control, slot, None))
        for w in (label, clear):
            w.bind('<Enter>', lambda _e: cell.configure(highlightbackground=MUTED)
                   if self.capturing != (control, slot) else None)
            w.bind('<Leave>', lambda _e: cell.configure(highlightbackground=LINE)
                   if self.capturing != (control, slot) else None)
        return cell, label

    def refresh_keys(self):
        for (control, slot), (cell, label) in self.key_cells.items():
            keys = self.keymap.get(control, [])
            name = keys[slot] if slot < len(keys) else None
            capturing = self.capturing == (control, slot)
            label.configure(text='Aperte…' if capturing else key_label(name),
                            fg=GOLD if capturing else (TEXT if name else MUTED))
            cell.configure(highlightbackground=GOLD if capturing else LINE)

    def set_key(self, control, slot, name):
        """Put `name` in a control's slot; a key used elsewhere leaves that place."""
        self.cancel_capture(refresh=False)
        note = None
        if name:
            for other, keys in self.keymap.items():
                if name in keys and (other, keys.index(name)) != (control, slot):
                    keys.remove(name)
                    note = f'{key_label(name)} saiu de {self.control_title(other)}.'
        keys = [k for k in self.keymap.get(control, []) if k]
        while len(keys) <= slot:
            keys.append(None)
        keys[slot] = name
        self.keymap[control] = [k for k in keys if k]
        self.refresh_keys()
        self.refresh_status(note or ' ')

    def control_title(self, control):
        for group, items in CONTROL_GROUPS:
            for c, title in items:
                if c == control:
                    return (group.split(' · ')[0] + ' ' + title.lower()) if c.startswith(('ls_', 'rs_')) else title.split('  ')[0]
        return control

    def key_preset(self, name):
        self.cancel_capture(refresh=False)
        self.keymap = {c: list(KEY_PRESETS[name].get(c, [])) for _, items in CONTROL_GROUPS for c, _ in items}
        self.refresh_keys()

    def start_capture(self, control, slot):
        self.cancel_capture(refresh=False)
        self.capturing = (control, slot)
        self.refresh_keys()
        self.refresh_status('Aperte uma tecla ou um botão do mouse para ' + self.control_title(control) + ' (Esc cancela).')
        # Armed a moment later, so the click that started it is not taken as Mouse1.
        self.root.after(250, self.arm_capture, (control, slot))

    def arm_capture(self, which):
        if self.capturing != which:
            return
        self.root.bind_all('<KeyPress>', self.capture_key)
        self.root.bind_all('<ButtonPress>', self.capture_mouse)

    def cancel_capture(self, refresh=True):
        if not getattr(self, 'capturing', None):
            return
        self.capturing = None
        self.root.unbind_all('<KeyPress>')
        self.root.unbind_all('<ButtonPress>')
        if refresh:
            self.refresh_keys()
            self.refresh_status()

    def capture_key(self, event):
        if not self.capturing:
            return None
        if event.keysym == 'Escape':
            self.cancel_capture()
            return 'break'
        sym = event.keysym
        name = TK_KEYS.get(sym)
        if not name and len(sym) == 1 and sym.isascii() and sym.isalnum():
            name = sym.upper()
        if name:
            self.set_key(*self.capturing, name)
        else:
            self.refresh_status(f'A tecla "{sym}" não pode ser usada; escolha outra (Esc cancela).')
        return 'break'

    def capture_mouse(self, event):
        if not self.capturing:
            return None
        old_aqua = MAC and self.tk.TkVersion < 8.7          # Tk 8.6 on macOS: 2 is the right button
        names = {1: 'Mouse1', 2: 'Mouse2' if old_aqua else 'Mouse3', 3: 'Mouse3' if old_aqua else 'Mouse2',
                 8: 'Mouse4', 9: 'Mouse5'}
        if WINDOWS and self.tk.TkVersion < 8.7:
            names.update({4: 'Mouse4', 5: 'Mouse5'})
        name = names.get(event.num)
        if name:
            self.set_key(*self.capturing, name)
        return 'break'

    def build_pad_tab(self, f):
        tk, ttk = self.tk, self.ttk
        top = tk.Frame(f, bg=PANEL)
        top.grid(row=0, column=0, columnspan=4, sticky='we', pady=(0, 6))
        tk.Label(top, text='Controles de Xbox, PlayStation e outros que o sistema reconhece. '
                           'Qual botão do controle faz cada botão do PS3:',
                 bg=PANEL, fg=MUTED, font=(self.ui, 9)).pack(side='left')
        ttk.Button(top, text='Restaurar padrão', command=self.pad_defaults).pack(side='right')
        self.pad_vars = {}
        r = 1
        for group, items in CONTROL_GROUPS:
            items = [(c, t) for c, t in items if c in PAD_CONTROLS]
            if not items:
                continue
            tk.Label(f, text=group.upper(), bg=PANEL, fg=GOLD, font=(self.heading, 10)).grid(
                row=r, column=0, columnspan=4, sticky='w', pady=(14, 4))
            r += 1
            for control, title in items:
                tk.Label(f, text=title, bg=PANEL, fg=TEXT, font=(self.ui, 10), anchor='w', width=26).grid(
                    row=r, column=0, sticky='w', pady=2)
                v = self.tk.StringVar(value=self.padmap.get(control, PAD_DEFAULTS[control]))
                v.trace_add('write', lambda *_a, c=control, var=v: self.padmap.__setitem__(c, var.get()))
                self.pad_vars[control] = v
                self.choice_var(f, v, PAD_BUTTONS, width=26).grid(row=r, column=1, sticky='w', pady=2)
                r += 1
        tk.Label(f, text='ANALÓGICOS', bg=PANEL, fg=GOLD, font=(self.heading, 10)).grid(
            row=r, column=0, columnspan=4, sticky='w', pady=(14, 4))
        r += 1
        tk.Label(f, text='Zona morta', bg=PANEL, fg=TEXT, font=(self.ui, 10), anchor='w', width=26).grid(
            row=r, column=0, sticky='w', pady=2)
        self.choice(f, 'pad_deadzone', DEADZONES, width=26).grid(row=r, column=1, sticky='w', pady=2)
        tk.Label(f, text='Quanto do centro dos analógicos é ignorado; aumente se o personagem anda sozinho.',
                 bg=PANEL, fg=MUTED, font=(self.ui, 9), wraplength=320, justify='left').grid(
            row=r, column=2, columnspan=2, sticky='w', padx=(18, 0))

    def pad_defaults(self):
        for control, v in self.pad_vars.items():
            v.set(PAD_DEFAULTS[control])
        self.var('pad_deadzone').set('24')

    def choice_var(self, parent, var, options, width=28):
        """A read-only combobox over a StringVar of its own (not a setting key)."""
        shown = self.tk.StringVar()
        box = self.ttk.Combobox(parent, textvariable=shown, state='readonly', width=width,
                                values=[label for _, label in options])
        to_label, to_value = dict(options), {label: value for value, label in options}
        shown.set(to_label.get(var.get(), options[0][1]))
        shown.trace_add('write', lambda *_: shown.get() in to_value and var.set(to_value[shown.get()]))
        var.trace_add('write', lambda *_: shown.get() != to_label.get(var.get()) and shown.set(to_label.get(var.get(), '')))
        box.bind('<MouseWheel>', lambda e: 'break')
        return box

    def build_game(self):
        f = self.page('game', 'Jogo', 'Idioma, legendas e saves.')
        self.section(f, 'Idioma')
        self.row(f, 'Idioma do jogo', self.choice(f, 'language', self.languages),
                 'Textos, legendas e vozes seguem o idioma do sistema do PS3. Vozes em grego: o próprio jogo oferece no primeiro início.')
        sub = self.choice(f, 'subtitles', ON_OFF)
        self.row(f, 'Legendas', sub, 'Legendas nas falas e cinemáticas.')
        self.note(f, 'O jogo guarda o idioma e as legendas no save do sistema; o launcher os ajusta ali antes de '
                     'cada início, então valem mesmo depois do primeiro uso.')
        self.section(f, 'Saves')
        self.row(f, 'Backup antes de jogar', self.choice(f, 'backup_saves', ON_OFF),
                 'Copia os saves para gamedata/save-backups (os últimos 10 ficam).')
        holder = self.ttk.Frame(f)
        self.ttk.Button(holder, text='Abrir pasta de saves', command=lambda: self.open_path(save_dir())).pack(side='left')
        self.ttk.Button(holder, text='Abrir backups', command=lambda: self.open_path(ROOT / 'gamedata' / 'save-backups')).pack(
            side='left', padx=(8, 0))
        self.row(f, '', holder)
        holder = self.ttk.Frame(f)
        self.backup_box = self.ttk.Combobox(holder, state='readonly', width=30)
        self.backup_box.bind('<MouseWheel>', lambda e: 'break')
        self.backup_box.pack(side='left')
        self.restore_button = self.ttk.Button(holder, text='Restaurar', command=self.restore_backup)
        self.restore_button.pack(side='left', padx=(8, 0))
        self.row(f, 'Restaurar um backup', holder, 'Os saves atuais viram um backup antes, então nada se perde.')
        self.refresh_backups()

    def refresh_backups(self):
        self.backups = backup_list()
        labels = []
        for d in self.backups:
            try:
                labels.append(time.strftime('%d/%m/%Y  %H:%M:%S', time.strptime(d.name, '%Y%m%d-%H%M%S')))
            except ValueError:
                labels.append(d.name)
        self.backup_box.configure(values=labels)
        self.backup_box.set(labels[0] if labels else 'Nenhum backup')
        busy = self.process or self.preparing or not labels
        self.restore_button.configure(state='disabled' if busy else 'normal')

    def restore_backup(self):
        i = self.backup_box.current()
        if i < 0 or self.process or self.preparing:
            return
        label = self.backup_box.get()
        if not self.messagebox.askyesno(APP_NAME, f'Voltar os saves para {label}?'):
            return
        try:
            restore_saves(self.backups[i])
        except OSError as e:
            self.messagebox.showerror(APP_NAME, f'Não consegui restaurar:\n{e}')
            return
        self.refresh_backups()
        self.refresh_status(f'Saves restaurados de {label}.')

    def build_mods(self):
        f = self.page('mods', 'Mods', 'Ligue, desligue e ordene. O primeiro da lista vence quando dois mexem no mesmo arquivo.')
        self.section(f, 'Mods')
        self.mods_frame = self.tk.Frame(f, bg=PANEL)
        self.mods_frame.grid(row=f.next_row, column=0, columnspan=3, sticky='we')
        self.mods_frame.columnconfigure(0, weight=1)
        f.next_row += 1
        self.section(f, 'Português do Brasil')
        self.note(f, 'O disco europeu já traz os textos em português do Brasil; as vozes vêm do disco americano. '
                     'Escolha a imagem (.iso) do seu disco americano, ou a pasta extraída dele, e o launcher monta o '
                     'mod PT-BR na sua pasta de mods. Com ele ligado, Português (Brasil) aparece em Idioma.')
        holder = self.ttk.Frame(f)
        self.ttk.Button(holder, text='Criar mod PT-BR do disco americano (.iso)…',
                        command=lambda: self.make_ptbr(folder=False)).pack(side='left')
        self.ttk.Button(holder, text='…ou da pasta extraída', command=lambda: self.make_ptbr(folder=True)).pack(
            side='left', padx=(8, 0))
        holder.grid(row=f.next_row, column=0, columnspan=3, sticky='w', pady=(8, 0))
        f.next_row += 1
        self.section(f, 'Pasta de mods')
        self.path_row(f, 'mods_dir', 'Pasta', folder=True)
        self.note(f, 'Cada mod é uma subpasta que espelha o USRDIR do jogo (um mod que troca GAME.PSARC traz '
                     '<mod>/GAME.PSARC), ou um mod.json com uma receita que o launcher aplica aos arquivos do seu '
                     'disco ao jogar. Os mods incluídos vêm com o Ascension e não trazem nada do jogo.')
        holder = self.ttk.Frame(f)
        self.ttk.Button(holder, text='Atualizar lista', command=self.refresh_mods).pack(side='left')
        self.ttk.Button(holder, text='Abrir pasta',
                        command=lambda: self.open_path(Path(self.var('mods_dir').get()), make=True)).pack(side='left', padx=(8, 0))
        holder.grid(row=f.next_row, column=0, columnspan=3, sticky='w', pady=(10, 0))
        f.next_row += 1
        self.var('mods_dir').trace_add('write', lambda *_: self.refresh_mods())
        self.mod_order = list(self.s['mods_order'])
        self.mod_vars = {}
        self.refresh_mods()

    def current_mod_settings(self):
        enabled = [m for m, v in self.mod_vars.items() if v.get()] if self.mod_vars else list(self.s['mods_enabled'])
        return {**self.s, 'mods_dir': self.var('mods_dir').get(), 'mods_enabled': enabled,
                'mods_order': list(getattr(self, 'mod_order', self.s['mods_order']))}

    def switch(self, parent, var, command):
        """An on/off switch: a pill that is red-gold when on."""
        tk = self.tk
        c = tk.Canvas(parent, width=46, height=24, bg=CARD, highlightthickness=0, bd=0, cursor='hand2')

        def draw(*_):
            c.delete('all')
            on = var.get()
            fill = ACCENT_HI if on else '#3a302a'
            c.create_oval(2, 2, 22, 22, fill=fill, outline=fill)
            c.create_oval(24, 2, 44, 22, fill=fill, outline=fill)
            c.create_rectangle(12, 2, 34, 22, fill=fill, outline=fill)
            x = 26 if on else 4
            c.create_oval(x, 4, x + 16, 20, fill='#fbf1e2' if on else '#8a7f76', outline='')

        def toggle(_e=None):
            var.set(not var.get())
            draw()
            command()
        c.bind('<Button-1>', toggle)
        var.trace_add('write', draw)
        draw()
        return c

    def refresh_mods(self):
        tk, ttk = self.tk, self.ttk
        for w in self.mods_frame.winfo_children():
            w.destroy()
        s = self.current_mod_settings()
        mods = all_mods({**s, 'mods_order': self.mod_order})
        self.mod_order = [m['id'] for m in mods]
        enabled = set(s['mods_enabled'])
        if not mods:
            ttk.Label(self.mods_frame, text='Nenhum mod.', style='Muted.TLabel').grid(row=0, column=0, sticky='w')
        for i, m in enumerate(mods):
            v = self.mod_vars.get(m['id']) or tk.BooleanVar(value=m['id'] in enabled)
            self.mod_vars[m['id']] = v
            card = tk.Frame(self.mods_frame, bg=CARD, highlightthickness=1, highlightbackground=LINE)
            card.grid(row=i, column=0, sticky='we', pady=4)
            card.columnconfigure(1, weight=1)
            self.switch(card, v, self.mods_changed).grid(row=0, column=0, rowspan=2, padx=(14, 14), pady=12)
            head = tk.Frame(card, bg=CARD)
            head.grid(row=0, column=1, sticky='w', pady=(10, 0))
            tk.Label(head, text=m['name'], bg=CARD, fg=TEXT, font=(self.heading, 11)).pack(side='left')
            if m['builtin']:
                tk.Label(head, text=' INCLUÍDO ', bg='#3a2a14', fg=GOLD, font=(self.ui, 7, 'bold')).pack(side='left', padx=(10, 0))
            tk.Label(card, text=m['description'] or str(m['path']), bg=CARD, fg=MUTED, font=(self.ui, 9),
                     wraplength=620, justify='left').grid(row=1, column=1, sticky='w', pady=(2, 10))
            arrows = tk.Frame(card, bg=CARD)
            arrows.grid(row=0, column=2, rowspan=2, padx=12)
            for txt, step in (('▲', -1), ('▼', 1)):
                b = tk.Label(arrows, text=txt, bg=CARD, fg=MUTED if (step < 0 and i == 0) or (step > 0 and i == len(mods) - 1) else TEXT,
                             font=(self.ui, 10), cursor='hand2', padx=6)
                b.pack(side='top')
                b.bind('<Button-1>', lambda _e, mid=m['id'], st=step: self.move_mod(mid, st))
        self.mods_changed()

    def languages(self):
        return language_options(self.current_mod_settings())

    def mods_changed(self):
        self.refresh_choices('language', '7')

    def make_ptbr(self, folder):
        if folder:
            src = self.filedialog.askdirectory(title='Pasta do disco americano (com PS3_GAME)')
        else:
            src = self.filedialog.askopenfilename(title='Imagem do disco americano',
                                                  filetypes=[('Imagem de disco', '*.iso'), ('Todos', '*.*')])
        if not src:
            return
        out = Path(self.var('mods_dir').get()) / 'PT-BR'
        eu = Path(self.var('eboot').get()).parent
        self.refresh_status('Criando o mod PT-BR… (copia ~140 MB)')

        def work():
            import importlib.util
            try:
                spec = importlib.util.spec_from_file_location('make_ptbr_mod', ROOT / 'tools' / 'make_ptbr_mod.py')
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                us, unmount = Path(src), None
                if us.suffix.lower() == '.iso':
                    us, unmount = mod.mount_iso(us)
                elif (us / 'PS3_GAME' / 'USRDIR').is_dir():
                    us = us / 'PS3_GAME' / 'USRDIR'
                try:
                    mod.build(us, eu, out, log=lambda m: None)
                finally:
                    if unmount:
                        unmount()
                self.root.after(0, self.ptbr_done, None)
            except BaseException as e:   # SystemExit carries the reason
                self.root.after(0, self.ptbr_done, str(e) or type(e).__name__)
        threading.Thread(target=work, daemon=True).start()

    def ptbr_done(self, error):
        if error:
            self.refresh_status('O mod PT-BR não foi criado.')
            self.messagebox.showerror(APP_NAME, 'Não consegui criar o mod PT-BR:\n' + error)
            return
        if 'PT-BR' not in self.mod_order:
            self.mod_order.insert(0, 'PT-BR')
        self.mod_vars['PT-BR'] = self.tk.BooleanVar(value=True)
        self.refresh_mods()
        self.var('language').set('17')
        self.refresh_choices('language', '7')
        self.refresh_status('Mod PT-BR criado e ligado; idioma: Português (Brasil). Clique em Salvar.')

    def move_mod(self, name, step):
        i = self.mod_order.index(name)
        j = i + step
        if 0 <= j < len(self.mod_order):
            self.mod_order[i], self.mod_order[j] = self.mod_order[j], self.mod_order[i]
            self.refresh_mods()

    def build_advanced(self):
        f = self.page('advanced', 'Avançado', 'Caminhos, música do launcher e variáveis do runtime.')
        self.section(f, 'Arquivos do jogo')
        self.path_row(f, 'game_exe', 'Executável')
        self.path_row(f, 'eboot', 'EBOOT.ELF')
        self.path_row(f, 'disc_dir', 'Pasta do disco', folder=True,
                      hint='A pasta com PS3_GAME.' + (' Com a imagem abaixo, o launcher a monta aqui.' if MAC else
                                                       ' Vazio: a do EBOOT.ELF.'))
        if MAC:
            self.path_row(f, 'disc_iso', 'Imagem do disco (.iso)',
                          hint='Montada só para leitura na pasta do disco ao jogar.')
        self.section(f, 'Launcher')
        self.row(f, 'Música de fundo', self.choice(f, 'music', ON_OFF))
        self.section(f, 'Runtime')
        entry = self.ttk.Entry(f, textvariable=self.var('extra_env'), width=70)
        self.row(f, 'Variáveis extras', entry)
        self.note(f, 'Separadas por ";", por exemplo  PS3_VERBOSE=1;VDEC_TIMELOG=1.  Para quem está depurando.')
        self.section(f, 'Registro')
        holder = self.ttk.Frame(f)
        self.ttk.Button(holder, text='Abrir último log', command=lambda: self.open_path(self.log_path())).pack(side='left')
        self.ttk.Button(holder, text='Pasta do jogo', command=lambda: self.open_path(ROOT)).pack(side='left', padx=(8, 0))
        self.row(f, '', holder)

    def build_about(self):
        f = self.page('about', 'Sobre', f'{APP_NAME} (PC) · launcher v{VERSION}')
        self.section(f, 'O projeto')
        self.note(f, 'God of War: Ascension (PS3) recompilado para rodar nativamente no PC. O código PowerPC do '
                     'jogo é traduzido para C e compilado para x86-64; o código dos SPUs também é recompilado, e '
                     'o que o PS3 fazia no sistema (vídeo RSX, áudio, arquivos, SPURS) é reimplementado pelo '
                     'runtime do ps3recomp. Não é um emulador e não traz nada do jogo: você precisa do seu '
                     'próprio disco.')
        self.note(f, 'Estado: experimento. O jogo vai do boot ao primeiro nível, mas ainda lento (menu a ~28 fps, '
                     'primeiro nível a ~9 fps). Veja o andamento no repositório.')
        self.section(f, 'Links')
        for title, url in (('Este projeto', 'https://github.com/arnaldolima1/gow-ascension-pc'),
                           ('Marcos', 'https://github.com/arnaldolima1/gow-ascension-pc/blob/main/docs/MILESTONES.md'),
                           ('ps3recomp (sp00nznet)', 'https://github.com/sp00nznet/ps3recomp')):
            link = self.tk.Label(f, text=url, bg=PANEL, fg=GOLD, cursor='hand2', font=(self.ui, 10, 'underline'))
            link.bind('<Button-1>', lambda _e, u=url: webbrowser.open(u))
            self.row(f, title, link)
        self.section(f, 'Créditos')
        self.note(f, 'Por Arnaldo Lima, com o runtime ps3recomp de sp00nznet e colaboradores. Launcher no estilo '
                     'do de gow3_pc (FelipePrado0). Fonte Cinzel (SIL Open Font License).')
        self.note(f, 'God of War é marca da Sony Interactive Entertainment. Projeto de fãs, sem fins lucrativos e '
                     'sem ligação com a Sony ou a Santa Monica Studio.')

    # ---- state ------------------------------------------------------------------------------
    def gather(self):
        values = {k: v.get() for k, v in self.vars.items()}
        values['keymap'] = {c: list(k) for c, k in self.keymap.items()}
        values['padmap'] = dict(self.padmap)
        values['mods_order'] = list(getattr(self, 'mod_order', self.s['mods_order']))
        if getattr(self, 'mod_vars', None):
            values['mods_enabled'] = [m for m, v in self.mod_vars.items() if v.get()]
        else:
            values['mods_enabled'] = list(self.s['mods_enabled'])
        return values

    def watch_changes(self):
        dirty = self.gather() != self.saved
        self.save_button.configure(state='normal' if dirty else 'disabled')
        if self.var('music').get() != ('1' if self.music_on() else '0'):
            self.set_music(self.var('music').get() == '1')
        self.refresh_music_label()
        paths = tuple(self.vars[k].get() for k in ('game_exe', 'eboot', 'disc_dir', 'disc_iso') if k in self.vars)
        if paths != getattr(self, 'watched_paths', paths) and not (self.process or self.preparing):
            self.refresh_status()
        self.watched_paths = paths
        self.root.after(400, self.watch_changes)

    def save(self):
        self.s.update(self.gather())
        save_settings(self.s)
        self.saved = self.gather()
        self.save_button.configure(state='disabled')
        self.refresh_status('Configurações salvas.')
        threading.Thread(target=prebuild_mods, args=(dict(self.s),), daemon=True).start()

    def refresh_status(self, text=None):
        if text is None:
            s = {**self.s, **self.gather()}
            gone, problem = missing(s), disc_problem(s)
            text = ('Falta ' + ' e '.join(gone)) if gone else ('Atenção: ' + problem + '.') if problem else 'Pronto para jogar.'
        self.status.configure(text=text)

    # ---- music ------------------------------------------------------------------------------
    def music_on(self):
        return getattr(self, '_music_on', self.s.get('music') == '1')

    def set_music(self, on):
        self._music_on = on
        if on and not self.process:
            self.music.play()
        else:
            self.music.pause()
        self.var('music').set('1' if on else '0')
        self.refresh_music_label()

    def toggle_music(self):
        self.set_music(not self.music_on())

    def refresh_music_label(self):
        if not hasattr(self, 'music_label'):
            return
        err = getattr(getattr(self, 'music', None), 'error', '')
        if err and self.music_on():
            text = '♪ Música: ' + err
        else:
            text = '♪ Música: ligada' if self.music_on() else '♪ Música: desligada'
        self.music_label.configure(text=text)

    # ---- actions ----------------------------------------------------------------------------
    def log_path(self):
        return ROOT / 'build' / 'logs' / 'last_run.log'

    def open_path(self, path, make=False):
        path = Path(path)
        if make:
            path.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            self.messagebox.showinfo(APP_NAME, f'Ainda não existe:\n{path}')
            return
        if WINDOWS:
            os.startfile(str(path))
        else:
            subprocess.Popen(['open' if MAC else 'xdg-open', str(path)])

    def play(self):
        """The slow part (disc, saves, mods) runs in a thread with its steps in
        the status bar; the window gives way to the game only once it starts."""
        if self.process or self.preparing:
            return
        if self.gather() != self.saved:
            self.save()
        gone = missing(self.s)
        if gone:
            self.messagebox.showerror(APP_NAME, 'Não encontrei ' + ' e '.join(gone) + '.\nAjuste em Avançado.')
            return
        problem = disc_problem(self.s)
        if problem:
            self.messagebox.showerror(APP_NAME, 'Este jogo foi compilado da versão europeia, mas ' + problem + '.')
            return
        self.preparing = True
        self.play_button.configure(state='disabled')
        s = dict(self.s)

        def work():
            try:
                env, mounted = prepare_game(s, status=lambda m: self.root.after(0, self.refresh_status, m))
                self.root.after(0, self.launch, env, mounted)
            except Exception as e:
                self.root.after(0, self.launch_failed, str(e) or type(e).__name__)
        threading.Thread(target=work, daemon=True).start()

    def launch(self, env, mounted):
        self.mounted = self.mounted or mounted
        host = self.enter_game_view()
        try:
            self.process, self.log = start_game(self.s, env, self.log_path(),
                                                parent=host.winfo_id() if host else None)
        except Exception as e:
            self.leave_game_view()
            self.launch_failed(str(e) or type(e).__name__)
            return
        self.preparing = False
        self.music.pause()
        self.refresh_backups()
        self.refresh_status('Jogo em execução…')
        threading.Thread(target=self.wait_game, daemon=True).start()

    def launch_failed(self, error):
        self.preparing = False
        self.play_button.configure(state='normal')
        self.refresh_status()
        self.messagebox.showerror(APP_NAME, f'O jogo não abriu:\n{error}')

    def enter_game_view(self):
        """The launcher's window becomes the game's: the pages give way to a
        black area the game renders into, at the chosen size or full screen.
        Elsewhere the game opens a window of its own and the launcher hides."""
        root = self.root
        if not WINDOWS:
            root.withdraw()
            root.update_idletasks()
            root.update()
            mac_dock(False)
            return None
        self.prev_geometry, self.prev_minsize = root.geometry(), root.minsize()
        self.side.pack_forget()
        self.right.pack_forget()
        self.game_host = self.tk.Frame(root, bg='black', highlightthickness=0, bd=0)
        self.game_host.pack(fill='both', expand=True)
        root.minsize(320, 180)
        if self.s['display_mode'] == 'fullscreen':
            root.attributes('-fullscreen', True)
        else:
            w, h = self.s['window_size'].split('x')
            root.geometry(f'{w}x{h}+{max(0, root.winfo_x())}+{max(0, root.winfo_y())}')
        root.update_idletasks()
        root.update()
        return self.game_host

    def leave_game_view(self):
        root = self.root
        if not WINDOWS:
            mac_dock(True)
            root.deiconify()
            root.lift()
            return
        root.attributes('-fullscreen', False)
        if WINDOWS:   # the game's F11 may have left the frame borderless
            try:
                frame = int(root.wm_frame(), 16)
                u = ctypes.windll.user32
                u.SetWindowLongW(frame, -16, 0x00CF0000 | 0x10000000)   # GWL_STYLE: WS_OVERLAPPEDWINDOW | WS_VISIBLE
                u.SetWindowPos(frame, 0, 0, 0, 0, 0, 0x0027)           # NOSIZE|NOMOVE|NOZORDER|FRAMECHANGED
            except (AttributeError, OSError, ValueError):
                pass
        if getattr(self, 'game_host', None):
            self.game_host.destroy()
            self.game_host = None
        root.minsize(*self.prev_minsize)
        root.geometry(self.prev_geometry)
        self.side.pack(side='left', fill='y')
        self.right.pack(side='left', fill='both', expand=True)

    def wait_game(self):
        code = self.process.wait()
        try:
            self.root.after(0, self.game_ended, code)
        except RuntimeError:     # the launcher closed first
            pass

    def game_ended(self, code):
        self.log.close()
        self.process = None
        self.play_button.configure(state='normal')
        self.leave_game_view()
        self.refresh_backups()
        if self.music_on():
            self.music.play()
        if code == 0:
            self.refresh_status('Jogo fechado.')
            return
        self.refresh_status(f'O jogo terminou com código {code}.')
        if self.messagebox.askyesno(APP_NAME, f'O jogo terminou com código {code}.\nAbrir o log desta execução?'):
            self.open_path(self.log_path())

    def close(self):
        if self.process:
            if not self.messagebox.askyesno(APP_NAME, 'Fechar o jogo?'):
                return
            self.process.terminate()
            try:
                self.process.wait(5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.log.close()
        if self.gather() != self.saved and self.messagebox.askyesno(APP_NAME, 'Salvar as alterações antes de sair?'):
            self.save()
        self.music.close()
        release_disc(self.mounted)
        self.root.destroy()


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
