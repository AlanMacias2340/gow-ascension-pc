"""God of War: Ascension (PC) launcher.

Settings for the recompiled game (window, language, mods, ...), kept in
%APPDATA%\\ascension-launcher\\settings.json and handed to the game as the
environment switches ps3recomp reads. PLAY starts build/win/AscensionRecomp.exe
with the disc's EBOOT.ELF; `--play` does the same without the window.

Artwork (backgrounds, logo, icon, music) is not part of the repository: it is
read from launcher/assets/ or, failing that, ../work/data/launcher/.
"""
import ctypes
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

VERSION = '0.1'
APP_NAME = 'God of War: Ascension'
WINDOWS = sys.platform == 'win32'
SHOT = '--shot' in sys.argv     # development: screenshot each page, then quit (no music)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                                   # ascension/
WORK = ROOT.parent / 'work'
ASSET_DIRS = [HERE / 'assets', WORK / 'data' / 'launcher']
CONFIG_DIR = Path(os.environ.get('APPDATA', Path.home())) / 'ascension-launcher'
CONFIG_FILE = CONFIG_DIR / 'settings.json'
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

DEFAULTS = {
    'display_mode': 'window', 'window_size': '1280x720', 'perf_overlay': '1',
    'esc_quits': '0', 'language': '18', 'enter_button': 'cross', 'subtitles': '1',
    'mods_dir': str(ROOT / 'mods'), 'mods_enabled': [], 'mods_order': [],
    'game_exe': str(ROOT / 'build' / 'win' / 'AscensionRecomp.exe'),
    'eboot': str(WORK / 'disc' / 'PS3_GAME' / 'USRDIR' / 'EBOOT.ELF'),
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
    return {**DEFAULTS, **data}


def save_settings(values):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(values, indent=2, ensure_ascii=False), encoding='utf-8')
    tmp.replace(CONFIG_FILE)


def save_dir():
    return ROOT / 'gamedata' / 'dev_hdd0' / 'home' / '00000001' / 'savedata'


def icon_file():
    """icon-2.png as an .ico (window, taskbar and the game's window)."""
    src = asset('icon-2.png')
    if not src:
        return None
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


def compose_mods(s, log=lambda m: None):
    """The folders for PS3_MODS: first the archives the launcher builds from
    the enabled mods' recipes ("psarc_patches" in mod.json, applied to the
    copy of that archive the highest-priority mod ships, or to the disc's),
    then every enabled mod's own files. Rebuilt only when an input changes."""
    mods = enabled_mod_list(s)
    usrdir = Path(s['eboot']).parent
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


def game_environment(s):
    env = dict(os.environ)
    env['PS3_SYS_LANG'] = effective_language(s)
    env['PS3_ENTER_BUTTON'] = s['enter_button']
    env['PS3_WINDOW_SIZE'] = s['window_size']
    env['PS3_FULLSCREEN'] = '1' if s['display_mode'] == 'fullscreen' else '0'
    env['PS3_ESC_QUITS'] = s['esc_quits']
    env['LD_PERF_OVERLAY'] = s['perf_overlay']
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


def backup_saves():
    src = save_dir()
    if not src.is_dir() or not any(src.iterdir()):
        return None
    dst = ROOT / 'gamedata' / 'save-backups' / time.strftime('%Y%m%d-%H%M%S')
    shutil.copytree(src, dst)
    backups = sorted((ROOT / 'gamedata' / 'save-backups').iterdir())
    for old in backups[:-10]:                       # keep the last ten
        shutil.rmtree(old, ignore_errors=True)
    return dst


def missing(s):
    out = []
    if not Path(s['game_exe']).is_file():
        out.append('o executável do jogo (' + s['game_exe'] + ')')
    if not Path(s['eboot']).is_file():
        out.append('o EBOOT.ELF do disco (' + s['eboot'] + ')')
    return out


def start_game(s, log_path, parent=None):
    """Start the game; with `parent` (a window handle) it renders inside that window."""
    if s.get('backup_saves') == '1':
        backup_saves()
    apply_save_settings(s)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = open(log_path, 'w', encoding='utf-8', errors='replace')
    flags = subprocess.CREATE_NO_WINDOW if WINDOWS else 0
    env = game_environment(s)
    if parent:
        env['PS3_PARENT_HWND'] = str(parent)
    return subprocess.Popen([s['game_exe'], s['eboot']], cwd=str(ROOT), env=env,
                            stdout=log, stderr=subprocess.STDOUT, creationflags=flags), log


class Music:
    """music.mp3 on a loop through Windows' MCI (no extra packages)."""
    def __init__(self):
        self.ok = False
        path = asset('music.mp3')
        if not (WINDOWS and path):
            return
        self.mci = ctypes.windll.winmm.mciSendStringW
        self.ok = self.send(f'open "{path}" type mpegvideo alias bgm') == 0
        if self.ok:
            self.send('setaudio bgm volume to 350')

    def send(self, cmd):
        return self.mci(cmd, None, 0, None)

    def play(self):
        if self.ok:
            self.send('play bgm repeat')

    def pause(self):
        if self.ok:
            self.send('pause bgm')

    def close(self):
        if self.ok:
            self.send('close bgm')


def register_font(path):
    if WINDOWS and path.is_file():
        try:
            ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0)  # FR_PRIVATE
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
        self.process = None
        self.heading = 'Cinzel Black' if register_font(HERE / 'Cinzel-Black.ttf') else 'Georgia'
        self.ui = 'Segoe UI' if WINDOWS else 'DejaVu Sans'
        root.title(f'{APP_NAME} (PC)')
        root.configure(bg=BG)
        w, h = 1180, 740
        root.geometry(f'{w}x{h}+{(root.winfo_screenwidth() - w) // 2}+{(root.winfo_screenheight() - h) // 3}')
        root.minsize(1000, 660)
        ico = icon_file()
        if ico:
            try:
                root.iconbitmap(default=str(ico))
            except tk.TclError:
                pass
        self.style()
        self.bg_sources = [p for p in (asset(n) for n in BACKGROUNDS) if p]
        self.bg_index, self.bg_cache, self.bg_size = 0, {}, None
        self.logo_src = asset('logo.png')
        self.build()
        self.show('home')
        self.saved = self.gather()
        self.music = Music() if not SHOT else Music.__new__(Music)
        if SHOT:
            self.music.ok = False
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
        for name, title in (('home', 'Início'), ('video', 'Vídeo'), ('game', 'Jogo'),
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
        tk.Label(side, text='F11 ou Alt+Enter no jogo:\ntela cheia', bg=BG, fg=MUTED, font=(self.ui, 9),
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
        self.build_game()
        self.build_mods()
        self.build_advanced()
        self.build_about()
        self.refresh_choices('language', '7')   # PT-BR only while its mod is on
        self.root.bind_all('<MouseWheel>', self.wheel)
        self.refresh_status()

    def wheel(self, event):
        page = self.pages.get(self.current)
        if hasattr(page, 'scroll') and 'combobox' not in str(event.widget).lower():
            page.scroll(int(-event.delta / 120))

    def show(self, name):
        for p in self.pages.values():
            p.pack_forget()
        self.pages[name].pack(fill='both', expand=True)
        self.current = name
        for n, item in self.nav.items():
            item.configure(bg=PANEL if n == name else BG, fg=GOLD if n == name else TEXT)
        if name == 'mods':
            self.refresh_mods()

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
        f = self.page('video', 'Vídeo', 'Janela e imagem do jogo.')
        self.section(f, 'Exibição')
        self.row(f, 'Modo de exibição', self.choice(f, 'display_mode', DISPLAY_MODES),
                 'No jogo, F11 ou Alt+Enter alterna entre janela e tela cheia.')
        self.row(f, 'Tamanho da janela', self.choice(f, 'window_size', WINDOW_SIZES),
                 'O jogo desenha em 1280 x 720 e a imagem é esticada para a janela.')
        self.section(f, 'Informações na tela')
        self.row(f, 'Contador de FPS', self.choice(f, 'perf_overlay', ON_OFF),
                 'FPS, tempo de quadro, velocidade, CPU e GPU no canto superior direito.')
        self.note(f, 'Resolução interna maior, filtros e limitador de FPS virão quando o renderizador tiver suporte.')

    def build_game(self):
        f = self.page('game', 'Jogo', 'Idioma e controles, como o PS3 os informa ao jogo.')
        self.section(f, 'Idioma')
        self.row(f, 'Idioma do jogo', self.choice(f, 'language', self.languages),
                 'Textos, legendas e vozes seguem o idioma do sistema do PS3. Vozes em grego: o próprio jogo oferece no primeiro início.')
        sub = self.choice(f, 'subtitles', ON_OFF)
        self.row(f, 'Legendas', sub, 'Legendas nas falas e cinemáticas.')
        self.note(f, 'O jogo guarda o idioma e as legendas no save do sistema; o launcher os ajusta ali antes de '
                     'cada início, então valem mesmo depois do primeiro uso.')
        self.section(f, 'Controles')
        self.row(f, 'Botão de confirmar', self.choice(f, 'enter_button', ENTER_BUTTONS),
                 'Qual botão aceita nos menus do sistema.')
        self.row(f, 'Esc fecha o jogo', self.choice(f, 'esc_quits', ON_OFF))
        self.section(f, 'Saves')
        self.row(f, 'Backup antes de jogar', self.choice(f, 'backup_saves', ON_OFF),
                 'Copia os saves para gamedata/save-backups (os últimos 10 ficam).')
        holder = self.ttk.Frame(f)
        self.ttk.Button(holder, text='Abrir pasta de saves', command=lambda: self.open_path(save_dir())).pack(side='left')
        self.ttk.Button(holder, text='Abrir backups', command=lambda: self.open_path(ROOT / 'gamedata' / 'save-backups')).pack(
            side='left', padx=(8, 0))
        self.row(f, '', holder)

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
        self.note(f, 'Estado: experimento. A abertura, os menus de primeiro uso e a cinemática de abertura '
                     'funcionam; o menu principal ainda está lento. Veja o andamento no repositório.')
        self.section(f, 'Links')
        for title, url in (('Este projeto', 'https://github.com/arnaldolima1/gow-ascension-pc'),
                           ('Andamento (STATUS)', 'https://github.com/arnaldolima1/gow-ascension-pc/blob/main/docs/STATUS.md'),
                           ('Marcos', 'https://github.com/arnaldolima1/gow-ascension-pc/blob/main/docs/MILESTONES.md'),
                           ('ps3recomp (fork usado)', 'https://github.com/arnaldolima1/ps3recomp'),
                           ('ps3recomp (original, sp00nznet)', 'https://github.com/sp00nznet/ps3recomp')):
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
        self.root.after(400, self.watch_changes)

    def save(self):
        self.s.update(self.gather())
        save_settings(self.s)
        self.saved = self.gather()
        self.save_button.configure(state='disabled')
        self.refresh_status('Configurações salvas.')

    def refresh_status(self, text=None):
        if text is None:
            gone = missing({**self.s, **self.gather()})
            text = ('Falta ' + ' e '.join(gone)) if gone else 'Pronto para jogar.'
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
        if hasattr(self, 'music_label'):
            self.music_label.configure(text=('♪ Música: ligada' if self.music_on() else '♪ Música: desligada'))

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
        os.startfile(str(path)) if WINDOWS else subprocess.Popen(['xdg-open', str(path)])

    def play(self):
        if self.process:
            return
        if self.gather() != self.saved:
            self.save()
        gone = missing(self.s)
        if gone:
            self.messagebox.showerror(APP_NAME, 'Não encontrei ' + ' e '.join(gone) + '.\nAjuste em Avançado.')
            return
        host = self.enter_game_view()
        try:
            self.process, self.log = start_game(self.s, self.log_path(), parent=host.winfo_id())
        except OSError as e:
            self.leave_game_view()
            self.messagebox.showerror(APP_NAME, f'O jogo não abriu:\n{e}')
            return
        self.music.pause()
        self.play_button.configure(state='disabled')
        self.refresh_status('Jogo em execução…')
        threading.Thread(target=self.wait_game, daemon=True).start()

    def enter_game_view(self):
        """The launcher's window becomes the game's: the pages give way to a
        black area the game renders into, at the chosen size or full screen."""
        root = self.root
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
        self.root.after(0, self.game_ended, code)

    def game_ended(self, code):
        self.log.close()
        self.process = None
        self.play_button.configure(state='normal')
        self.leave_game_view()
        self.refresh_status('Jogo fechado.' if code == 0 else f'O jogo terminou com código {code}: veja o último log em Avançado.')
        if self.music_on():
            self.music.play()

    def close(self):
        if self.process:
            if not self.messagebox.askyesno(APP_NAME, 'Fechar o jogo?'):
                return
            self.process.terminate()
        if self.gather() != self.saved and self.messagebox.askyesno(APP_NAME, 'Salvar as alterações antes de sair?'):
            self.save()
        self.music.close()
        self.root.destroy()


def main():
    if '--play' in sys.argv:
        s = load_settings()
        gone = missing(s)
        if gone:
            print('Falta: ' + '; '.join(gone))
            return 1
        process, log = start_game(s, ROOT / 'build' / 'logs' / 'last_run.log')
        code = process.wait()
        log.close()
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
        pages = ['home', 'video', 'game', 'mods', 'advanced', 'about']

        def grab(i):
            from PIL import ImageGrab
            root.update()
            try:     # the window itself, whatever is on top of it
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
