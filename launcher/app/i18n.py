"""The launcher's own language. The code is written in English; each other
language is launcher/lang/<code>.json, a map from the English text to its
translation ("_name" is the language's own name). Text with no translation
stays in English."""
import json
import os
import subprocess
import sys

from .config import HERE

BASE = 'en'
LANG_DIR = HERE / 'lang'
_table = {}
_code = BASE


def available():
    """[(code, name)]: English, then every lang/*.json, by name."""
    out = []
    for path in sorted(LANG_DIR.glob('*.json')) if LANG_DIR.is_dir() else []:
        try:
            name = json.loads(path.read_text(encoding='utf-8')).get('_name', path.stem)
        except (OSError, ValueError):
            continue
        out.append((path.stem, name))
    return [(BASE, 'English')] + sorted(out, key=lambda o: o[1])


def system_language():
    """The system's first language as a code ('pt-BR', 'en', ...)."""
    names = []
    try:
        if sys.platform == 'win32':
            import ctypes
            import locale
            names.append(locale.windows_locale.get(ctypes.windll.kernel32.GetUserDefaultUILanguage(), ''))
        elif sys.platform == 'darwin':
            r = subprocess.run(['defaults', 'read', '-g', 'AppleLanguages'], capture_output=True, text=True, timeout=2)
            names += [p.strip(' \t"(),') for p in r.stdout.split('\n')]
    except (AttributeError, OSError, subprocess.SubprocessError):
        pass
    names += [os.environ.get(k, '') for k in ('LC_ALL', 'LC_MESSAGES', 'LANG')]
    for name in names:
        name = name.split('.')[0].replace('_', '-')
        if name and name != 'C':
            return name
    return 'en'


def resolve(code):
    """A setting ('auto' or a code) as a language the launcher has."""
    codes = [c for c, _ in available()]
    want = system_language() if code in ('', 'auto') else code
    if want in codes:
        return want
    primary = want.split('-')[0].lower()
    return next((c for c in codes if c.split('-')[0].lower() == primary), BASE)


def set_language(code):
    """Load the language a setting names; returns the code in use."""
    global _table, _code
    code = _code = resolve(code)
    _table = {}
    if code != BASE:
        try:
            _table = json.loads((LANG_DIR / f'{code}.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            _table = {}
    return code


def current():
    return _code


def tr(text, **values):
    """`text` in the launcher's language; {name} fields filled from `values`."""
    text = _table.get(text, text)
    return text.format(**values) if values else text
