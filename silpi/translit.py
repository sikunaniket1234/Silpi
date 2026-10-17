# -*- coding: utf-8 -*-
"""Silpi transliteration engines.

Two schemes are supported for converting keystrokes to Odia Unicode:

* ``phonetic`` - type Roman text the way it sounds (``namaskaara`` ->
  ନମସ୍କାର).  A pragmatic ITRANS-style scheme for Odia.
* ``akruti``   - the legacy Akruti touch-typing layout, backed by
  :mod:`silpi.akruti_map`.

Both expose ``convert(text) -> str`` and ``describe() -> str``.
"""
from __future__ import annotations

import re

from . import akruti_map

VOWELS = "\u0b05\u0b06\u0b07\u0b08\u0b09\u0b0a\u0b0b\u0b0c\u0b0f\u0b10"
CONSONANT_RANGE = (
    "\u0b15\u0b16\u0b17\u0b18\u0b19\u0b1a\u0b1b\u0b1c\u0b1d\u0b1e"
    "\u0b1f\u0b20\u0b21\u0b22\u0b23\u0b24\u0b25\u0b26\u0b27\u0b28\u0b2a"
    "\u0b2b\u0b2c\u0b2d\u0b2e\u0b2f\u0b30\u0b32\u0b33\u0b35\u0b36\u0b37"
    "\u0b38\u0b39\u0b5c\u0b5d\u0b5f\u0b03"
)
VIRAMA = "\u0b4d"
NUKTA = "\u0b3c"

# --- phonetic token tables -------------------------------------------------
# Independent vowels -> (token list, independent form)
_VOWEL_FORMS = {
    "a": "\u0b05", "aa": "\u0b06", "A": "\u0b06",
    "i": "\u0b07", "ii": "\u0b08", "I": "\u0b08", "ee": "\u0b08",
    "u": "\u0b09", "uu": "\u0b0a", "U": "\u0b0a", "oo": "\u0b0a",
    "R^i": "\u0b0b", "RRi": "\u0b0b", "R": "\u0b0b", "Ru": "\u0b0b",
    "e": "\u0b0f", "ai": "\u0b10",
    "o": "\u0b13", "au": "\u0b14", "Ou": "\u0b14",
}
# Vowel -> dependent sign (matra). 'a' is the inherent vowel (empty sign).
_VOWEL_SIGNS = {
    "a": "", "aa": "\u0b3e", "A": "\u0b3e",
    "i": "\u0b3f", "ii": "\u0b40", "I": "\u0b40", "ee": "\u0b40",
    "u": "\u0b41", "uu": "\u0b42", "U": "\u0b42", "oo": "\u0b42",
    "R^i": "\u0b43", "RRi": "\u0b43", "R": "\u0b43", "Ru": "\u0b43",
    "e": "\u0b47", "ai": "\u0b48",
    "o": "\u0b4b", "au": "\u0b4c", "Ou": "\u0b4c",
}
# consonant -> glyph
_CONSONANTS = {
    "k": "\u0b15", "kh": "\u0b16", "g": "\u0b17", "gh": "\u0b18", "ng": "\u0b19",
    "~N": "\u0b19", "ch": "\u0b1a", "chh": "\u0b1b", "C": "\u0b1b",
    "j": "\u0b1c", "jh": "\u0b1d", "~n": "\u0b1e", "n~": "\u0b1e",
    "T": "\u0b1f", "Th": "\u0b20", "D": "\u0b21", "Dh": "\u0b22", "N": "\u0b23",
    "t": "\u0b24", "th": "\u0b25", "d": "\u0b26", "dh": "\u0b27", "n": "\u0b28",
    "p": "\u0b2a", "ph": "\u0b2b", "f": "\u0b2b", "b": "\u0b2c", "bh": "\u0b2d",
    "m": "\u0b2e", "y": "\u0b5f", "Y": "\u0b2f", "r": "\u0b30", "l": "\u0b32",
    "L": "\u0b33", "v": "\u0b71", "w": "\u0b71", "sh": "\u0b36", "S": "\u0b36",
    "Sh": "\u0b37", "ssh": "\u0b37", "s": "\u0b38", "h": "\u0b39",
    "ksh": "\u0b15\u0b4d\u0b37", "kSh": "\u0b15\u0b4d\u0b37", "x": "\u0b15\u0b4d\u0b37",
    "gy": "\u0b1c\u0b4d\u0b1e", "j~n": "\u0b1c\u0b4d\u0b1e",
    ".D": "\u0b5c", ".d": "\u0b5c", ".Dh": "\u0b5d", ".dh": "\u0b5d", "rri": "\u0b5c",
}
# symbols / signs
_SIGNS = {
    "M": "\u0b02", "nM": "\u0b02", "H": "\u0b03", "z": "\u0b03",
    "~": "\u0b01", ".N": "\u0b01", "^": "\u0b01",
    "'": "\u0b3d", "OM": "\u0b13\u0b02", "Aa": "\u0b06",
}

_ALL_TOKENS = {}
for d in (_CONSONANTS, _VOWEL_FORMS, _SIGNS):
    _ALL_TOKENS.update(d)

# longest tokens first for greedy matching
_MAXLEN = max(len(k) for k in _ALL_TOKENS)


def _match(text: str, i: int):
    for ln in range(min(_MAXLEN, len(text) - i), 0, -1):
        tok = text[i:i + ln]
        node = _ALL_TOKENS.get(tok)
        if node is not None:
            return tok, node
    return None, None


def phonetic(text: str) -> str:
    """Transliterate Roman (ITRANS-ish) text to Odia Unicode.
    
    In Odia orthography, consonants carry an inherent 'a' vowel unless
    followed by another vowel, a conjunct consonant, or an explicit halant/virama.
    Trailing consonants retain their inherent vowel (e.g. 'bharat' -> ଭରତ,
    'namaskar' -> ନମସ୍କାର, 'jagannath' -> ଜଗନ୍ନାଥ).
    Explicit virama can still be produced by typing '_' or 'f' or '.h'.
    """
    out = []
    i = 0
    n = len(text)
    pending_consonant = False  # a consonant is waiting for its vowel or conjunct
    while i < n:
        tok, node = _match(text, i)
        if tok is None:
            # Unknown character: flush pending consonant with inherent vowel (no virama)
            if pending_consonant:
                pending_consonant = False
            out.append(text[i])
            i += 1
            continue
        i += len(tok)
        if tok in _CONSONANTS:
            if tok == "y" and pending_consonant:
                # consonant + ya -> ya-phala (0B4D + 0B5F)
                out.append(VIRAMA + "\u0b5f")
                pending_consonant = True
                continue
            if pending_consonant:
                # Two consecutive consonants without intervening vowel -> form conjunct (yuktakshara)
                out.append(VIRAMA)
            out.append(node)
            pending_consonant = True
        elif tok in _VOWEL_FORMS:
            if pending_consonant:
                out.append(_VOWEL_SIGNS[tok])
                pending_consonant = False
            else:
                out.append(node)
        else:  # sign / symbol
            out.append(node)
            # a trailing sign does not consume or kill the inherent vowel
            if pending_consonant:
                pending_consonant = False
    # If the word ended on a consonant, Odia retains inherent 'a' vowel by default (NO trailing virama)
    return "".join(out)


def akruti(text: str) -> str:
    return akruti_map.to_unicode(text)


_ENGINES = {"phonetic": phonetic, "akruti": akruti}


def convert(text: str, scheme: str) -> str:
    fn = _ENGINES.get(scheme, phonetic)
    return fn(text)


def describe(scheme: str) -> str:
    if scheme == "akruti":
        return ("Akruti phonetic layout: each key types the Odia letter or "
                "sign it represents (k = \u0b15, a = \u0b3e, f = halanta, "
                "\u2026), modelled after the classic Akruti phonetic layout.")
    return ("Phonetic: type Roman as it sounds  (a aa i ii u uu e ai o au, "
            "k kh g gh ... / M = anusvara, H = visarga, ~ = chandrabindu).")
