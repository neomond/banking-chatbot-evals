"""Lightweight language detection for az / ru / en.

Deliberately simple and transparent (no model download), but handles the cases that
matter in Baku: Cyrillic Russian, Azerbaijani with diacritics, Azerbaijani typed
WITHOUT diacritics ("12 ayliq depozit faizi neqederdir"), and code-switching.
"""
from __future__ import annotations

import re

AZ_CHARS = set("əğışçöü")
# Common Azerbaijani words as typed on Latin keyboards without diacritics.
AZ_HINT_WORDS = {
    "salam", "ayliq", "aylıq", "faiz", "faizi", "neqeder", "neqederdir", "nece", "necedir",
    "nedir", "men", "menim", "ucun", "karti", "kartim", "depozit", "depoziti", "kredit",
    "krediti", "haqqi", "var", "yoxdur", "isteyirem", "olar", "mumkundur", "zehmet", "olmasa",
    "edin", "verin", "gun", "ay", "manat",
}
_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)

LANG_NAMES = {"az": "Azerbaijani", "ru": "Russian", "en": "English"}


def detect_language(text: str) -> str:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"
    cyr = sum(1 for c in letters if "Ѐ" <= c <= "ӿ")
    if cyr / len(letters) > 0.3:
        return "ru"
    lowered = text.lower()
    if any(c in AZ_CHARS for c in lowered):
        return "az"
    words = _WORD.findall(lowered)
    if sum(1 for w in words if w in AZ_HINT_WORDS) >= 2:
        return "az"
    return "en"


def language_instruction(lang: str) -> str:
    """Pin the model to the detected user language. The bank is in AZ; models otherwise default to Azerbaijani."""
    name = LANG_NAMES.get(lang, "English")
    others = [label for code, label in LANG_NAMES.items() if code != lang]
    return (
        f"CURRENT USER LANGUAGE: {name} ({lang}). "
        f'The JSON "text" field MUST be written entirely in {name}. '
        f"Do not use {' or '.join(others)} in the reply, even though Lumen Bank is in Azerbaijan."
    )
