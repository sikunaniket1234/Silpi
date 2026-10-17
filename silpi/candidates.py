# -*- coding: utf-8 -*-
"""Odia phonetic word predictor and candidate generator for Silpi.

Generates 1 to 5 ranked candidates for a typed Roman buffer:
1. Primary transliteration output (via translit.phonetic).
2. Lexicon/dictionary matches with accurate Odia spelling.
3. Common variant spellings (e.g., inherent vs long vowel variants).
4. Raw Roman text fallback.
"""
from __future__ import annotations

from . import translit

# High-frequency Odia vocabulary words (roman prefix -> list of Unicode words)
ODIA_DICTIONARY: dict[str, list[str]] = {
    "namaskar": ["ନମସ୍କାର", "ନମସ୍କାରମ୍"],
    "namaskara": ["ନମସ୍କାର", "ନମସ୍କାରମ୍"],
    "bharat": ["ଭାରତ", "ଭରତ", "ଭାରତୀ", "ଭାରତୀୟ"],
    "bharata": ["ଭାରତ", "ଭରତ", "ଭାରତୀ", "ଭାରତୀୟ"],
    "odia": ["ଓଡ଼ିଆ", "ଓଡିଆ"],
    "orissa": ["ଓଡ଼ିଶା", "ଓଡିଶା"],
    "odisha": ["ଓଡ଼ିଶା", "ଓଡିଶା"],
    "jagannath": ["ଜଗନ୍ନାଥ", "ଜଗନ୍ନାଥଙ୍କ"],
    "jagannatha": ["ଜଗନ୍ନାଥ", "ଜଗନ୍ନାଥଙ୍କ"],
    "bhubaneswar": ["ଭୁବନେଶ୍ୱର", "ଭୁବନେଶ୍ଵର"],
    "cuttack": ["କଟକ", "କଟକୀ"],
    "puri": ["ପୁରୀ", "ପୁରୀର"],
    "mandira": ["ମନ୍ଦିର", "ମନ୍ଦିରର"],
    "mandir": ["ମନ୍ଦିର", "ମନ୍ଦିରର"],
    "shakti": ["ଶକ୍ତି", "ଶକ୍ତିଶାଳୀ"],
    "shanti": ["ଶାନ୍ତି", "ଶାନ୍ତିପୂର୍ଣ୍ଣ"],
    "vidyalaya": ["ବିଦ୍ୟାଳୟ", "ବିଦ୍ୟାଳୟର"],
    "karyalaya": ["କାର୍ଯ୍ୟାଳୟ", "କାର୍ଯ୍ୟାଳୟର"],
    "dhanyabad": ["ଧନ୍ୟବାଦ"],
    "dhanyabada": ["ଧନ୍ୟବାଦ"],
    "swagatam": ["ସ୍ୱାଗତମ୍", "ସ୍ୱାଗତ"],
    "swagata": ["ସ୍ୱାଗତ", "ସ୍ୱାଗତମ୍"],
    "pustaka": ["ପୁସ୍ତକ", "ପୁସ୍ତକାଳୟ"],
    "sahitya": ["ସାହିତ୍ୟ", "ସାହିତ୍ୟିକ"],
    "samaja": ["ସମାଜ", "ସାମାଜିକ"],
    "desha": ["ଦେଶ", "ଦେଶବାସୀ"],
    "rajya": ["ରାଜ୍ୟ", "ରାଜ୍ୟସଭା"],
    "bhasa": ["ଭାଷା", "ଭାଷାର"],
    "shikshya": ["ଶିକ୍ଷା", "ଶିକ୍ଷକ", "ଶିକ୍ଷୟିତ୍ରୀ"],
    "dharma": ["ଧର୍ମ", "ଧାର୍ମିକ"],
    "karma": ["କର୍ମ", "କର୍ମୀ"],
    "satya": ["ସତ୍ୟ", "ସତ୍ୟବାଦୀ"],
    "prem": ["ପ୍ରେମ", "ପ୍ରେମିକ"],
    "mitra": ["ମିତ୍ର", "ମିତ୍ରତା"],
    "bandhu": ["ବନ୍ଧୁ", "ବନ୍ଧୁତା"],
    "sundara": ["ସୁନ୍ଦର", "ସୌନ୍ଦର୍ଯ୍ୟ"],
    "ananda": ["ଆନନ୍ଦ", "ଆନନ୍ଦଦାୟକ"],
}


def get_candidates(buffer: str, max_count: int = 5) -> list[str]:
    """Return a ranked list of candidate words for the typed Roman string."""
    if not buffer:
        return []

    results: list[str] = []
    seen = set()

    def add(word: str):
        if word and word not in seen:
            seen.add(word)
            results.append(word)

    buf_lower = buffer.lower()

    # 1. Exact dictionary matches
    if buf_lower in ODIA_DICTIONARY:
        for w in ODIA_DICTIONARY[buf_lower]:
            add(w)

    # 2. Primary phonetic transliteration output
    primary = translit.phonetic(buffer)
    add(primary)

    # 3. Transliterate with capitalized first vowel if starts with 'a' (e.g. bharat -> ଭାରତ)
    if "a" in buf_lower:
        variant_a = translit.phonetic(buffer.replace("a", "aa", 1))
        add(variant_a)

    # 4. Partial dictionary prefix matches (predictive completion)
    for k, word_list in ODIA_DICTIONARY.items():
        if k.startswith(buf_lower) and k != buf_lower:
            for w in word_list:
                add(w)
                if len(results) >= max_count:
                    break
        if len(results) >= max_count:
            break

    # 5. English Roman fallback
    add(buffer)

    return results[:max_count]
