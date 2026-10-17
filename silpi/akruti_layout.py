# -*- coding: utf-8 -*-
"""Akruti phonetic keyboard layout for Silpi.

This is a direct key -> Odia glyph map ("type it as it sounds"), modelled
after the classic Akruti phonetic layout.  It is derived from the
open-source "Akruti Phonetic" KeyMagic layout published by the Odia
Wikimedia community (github.com/OdiaWikimedia/Kunji-Binyasa).

Keys not present in the map pass through untouched, so digits/punctuation
keep working.  The map is keyed by the character the key produces on a
US layout (so look it up with the same ``vk_to_char`` used by the IME).
"""
from __future__ import annotations

KEYMAP = {
    # --- independent vowels ---
    "A": "\u0b05",  # ଅ
    "z": "\u0b07",  # ଇ
    "Z": "\u0b08",  # ଈ
    "q": "\u0b09",  # ଉ
    "Q": "\u0b0a",  # ଊ
    "+": "\u0b0b",  # ଋ
    "w": "\u0b0f",  # ଏ
    "W": "\u0b10",  # ଐ
    "`": "\u0b13",  # ଓ
    "~": "\u0b14",  # ଔ
    # --- vowel signs (matras) ---
    "a": "\u0b3e",  # ା
    "i": "\u0b3f",  # ି
    "I": "\u0b40",  # ୀ
    "u": "\u0b41",  # ୁ
    "U": "\u0b42",  # ୂ
    "=": "\u0b43",  # ୃ
    "e": "\u0b47",  # େ
    "E": "\u0b48",  # ୈ
    "o": "\u0b4c\u0b3e",  # ୌା
    "O": "\u0b4c",  # ୌ
    # --- consonants ---
    "k": "\u0b15",  # କ
    "K": "\u0b16",  # ଖ
    "g": "\u0b17",  # ଗ
    "G": "\u0b18",  # ଘ
    "*": "\u0b19",  # ଙ
    "c": "\u0b1a",  # ଚ
    "C": "\u0b1b",  # ଛ
    "j": "\u0b1c",  # ଜ
    "J": "\u0b1d",  # ଝ
    "_": "\u0b1e",  # ଞ
    "'": "\u0b1f",  # ଟ
    '"': "\u0b20",  # ଠ
    "[": "\u0b21",  # ଡ
    "{": "\u0b22",  # ଢ
    "N": "\u0b23",  # ଣ
    "t": "\u0b24",  # ତ
    "T": "\u0b25",  # ଥ
    "d": "\u0b26",  # ଦ
    "D": "\u0b27",  # ଧ
    "n": "\u0b28",  # ନ
    "p": "\u0b2a",  # ପ
    "P": "\u0b2b",  # ଫ
    "b": "\u0b2c",  # ବ
    "v": "\u0b2c",  # ବ
    "B": "\u0b2d",  # ଭ
    "m": "\u0b2e",  # ମ
    "F": "\u0b2f",  # ଯ (uninflected ja)
    "y": "\u0b5f",  # ୟ (ya)
    "Y": "\u0b4d\u0b5f",  # ୍ୟ (ya-phala conjunct)
    "r": "\u0b30",  # ର
    "l": "\u0b32",  # ଲ
    "L": "\u0b33",  # ଳ
    "V": "\u0b5c",  # ଡ଼
    "M": "\u0b5d",  # ଢ଼
    "s": "\u0b38",  # ସ
    "S": "\u0b36",  # ଶ
    "h": "\u0b39",  # ହ
    "H": "\u0b37",  # ଷ
    "}": "\u0b0c",  # ଌ
    # --- signs ---
    "x": "\u0b02",  # ଂ anusvara
    "X": "\u0b01",  # ଁ chandrabindu
    ":": "\u0b03",  # ଃ visarga
    "f": "\u0b4d",  # ୍ virama / halanta
    "|": "\u0b3d",  # ଽ avagraha
    # --- common conjuncts / special ---
    "^": "\u0b4d\u0b30",   # ୍ର ra-phala
    "&": "\u0b30\u0b4d",   # ର୍ reph
    "$": "\u0b24\u0b4d\u0b30",  # ତ୍ର
    "%": "\u0b1c\u0b4d\u0b1e",  # ଜ୍ଞ
    "#": "\u0b15\u0b4d\u0b37",  # କ୍ଷ
    "@": "\u0b36\u0b4d\u0b30",  # ଶ୍ର
    "\\": "\u0b70",  # ୰
    # --- Odia digits ---
    "0": "\u0b66", "1": "\u0b67", "2": "\u0b68", "3": "\u0b69", "4": "\u0b6a",
    "5": "\u0b6b", "6": "\u0b6c", "7": "\u0b6d", "8": "\u0b6e", "9": "\u0b6f",
    # --- passthrough punctuation (kept identical to the layout) ---
    "-": "-", "]": "]", ";": ";", ",": ",", ".": ".", "/": "/", "!": "!",
    "(": "(", ")": ")", "?": "?", "<": "%", ">": "\u0964",
}


def convert_key(ch: str) -> str | None:
    """Return the Odia output for a US-layout character, or None to pass."""
    return KEYMAP.get(ch)
