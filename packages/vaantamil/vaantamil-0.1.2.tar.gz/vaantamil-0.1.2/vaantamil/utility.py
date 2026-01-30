# encoding.py
import re
from typing import List, Dict
from functools import lru_cache

# =========================================================
# 1. Character classification
# =========================================================

def is_independent_vowel(c: str) -> bool:
    return '\u0B85' <= c <= '\u0B94'


def is_consonant(c: str) -> bool:
    return '\u0B95' <= c <= '\u0BB9'


def is_vowel_sign(c: str) -> bool:
    return c in {
        '\u0BBE', '\u0BBF', '\u0BC0', '\u0BC1', '\u0BC2',
        '\u0BC6', '\u0BC7', '\u0BC8',
        '\u0BCA', '\u0BCB', '\u0BCC', '\u0BD7'
    }


def is_virama(c: str) -> bool:
    return c == '\u0BCD'


# =========================================================
# 2. split_graphemes
# =========================================================

INDEPENDENT_VOWEL = r'[\u0B85-\u0B94]'
CONSONANT = r'[\u0B95-\u0BB9]'
VOWEL_SIGNS = r'[\u0BBE-\u0BCC\u0BD7\u0BCA\u0BC7\u0BC6\u0BC8\u0BCB\u0BC0\u0BBF]'
VIRAMA = r'\u0BCD'
GRAPHEME_RE = re.compile(rf'(?:{INDEPENDENT_VOWEL}|{CONSONANT}(?:{VOWEL_SIGNS}|{VIRAMA})*)')

def split_graphemes(word: str) -> List[str]:
    #word = normalize_text(word)
    #if not word: return []
    matches = GRAPHEME_RE.findall(word)
    if ''.join(matches) == word: return matches
    return list(word)


# =========================================================
# 3. decompose_to_components
# =========================================================

VOWEL_SIGN_MAP = {
    '\u0BBE': '\u0B86',
    '\u0BBF': '\u0B87',
    '\u0BC0': '\u0B88',
    '\u0BC1': '\u0B89',
    '\u0BC2': '\u0B8A',
    '\u0BC6': '\u0B8E',
    '\u0BC7': '\u0B8F',
    '\u0BC8': '\u0B90',
    '\u0BCA': '\u0B92',
    '\u0BCB': '\u0B93',
    '\u0BCC': '\u0B94',
    '\u0BD7': '\u0B85',
}


def decompose_to_components(g: str) -> List[str]:
    first = g[0]

    if is_independent_vowel(first):
        return [g]

    if g.endswith('\u0BCD'):
        return [g]

    if is_consonant(first):
        mei = first + '\u0BCD'
        rest = g[1:]

        if not rest or rest == '\u0BCD':
            return [mei, "அ"]

        for ch in rest:
            if ch in VOWEL_SIGN_MAP:
                return [mei, VOWEL_SIGN_MAP[ch]]

        return [mei, rest]

    return [g]


# =========================================================
# 4. split_mode_native
# =========================================================

def split_mode_native(word: str, mode: int) -> List[str]:
    if mode == 0:
        return split_graphemes(word)

    if mode == 1:
        out = []
        graphemes = split_graphemes(word)
        i = 0

        while i < len(graphemes):
            if (
                i + 1 < len(graphemes)
                and graphemes[i] == "க்"
                and graphemes[i + 1].startswith("ஷ")
            ):
                out.append("க்ஷ்")
                parts = decompose_to_components(graphemes[i + 1])
                if len(parts) > 1:
                    out.append(parts[-1])
                i += 2
                continue

            out.extend(decompose_to_components(graphemes[i]))
            i += 1

        return out

    return []


def component_array(word: str) -> list[str]:
    return split_mode_native(word, 1) if word else []

def உயிர்_மெய்_எழுத்துகள்(word: str) -> list[str]:
    return split_mode_native(word, 1) if word else []

# =========================================================
# 5. Utility helpers
# =========================================================

def is_ends_with_suffix(word: str, suffix: str) -> bool:
    if not word or not suffix:
        return False
    word_parts = split_mode_native(word, 1)
    suffix_parts = split_mode_native(suffix, 1)

    return word_parts[-len(suffix_parts):] == suffix_parts


def first_component(word: str) -> str:
    parts = component_array(word)
    return parts[0] if parts else ""


def final_component(word: str) -> str:
    parts = component_array(word)
    return parts[-1] if parts else ""


SHORT_VOWELS = {"அ", "இ", "உ", "எ", "ஒ"}
LONG_VOWELS = ["ஆ", "ஈ", "ஊ", "ஏ", "ஓ", "ஐ", "ஔ" ]

def is_mei(letter: str) -> bool:
    return letter.endswith('\u0BCD')

def is_netil(letter: str) -> bool:
    return letter in LONG_VOWELS

def மெய்யா(letter: str) -> bool:
    return letter.endswith('\u0BCD')

def நெடிலா(letter: str) -> bool:
    return letter in LONG_VOWELS

def letter_count(root: str) -> int:
    return len(component_array(root))

def is_doubling(root: str) -> bool:
    parts = component_array(root)
    n = len(parts)

    if n == 2:
        return parts[0] in SHORT_VOWELS and is_mei(parts[1])

    if n == 3:
        return is_mei(parts[0]) and parts[1] in SHORT_VOWELS and is_mei(parts[2])

    return False


# =========================================================
# 6. Uyir / Mei maps
# =========================================================

TAMIL_UYIR = [
    "அ","ஆ","இ","ஈ","உ","ஊ",
    "எ","ஏ","ஐ","ஒ","ஓ","ஔ"
]

UYIR_INDEX = {v: i for i, v in enumerate(TAMIL_UYIR)}

UYIRMEI_MAP = {
    "க்": ["க","கா","கி","கீ","கு","கூ","கெ","கே","கை","கொ","கோ","கௌ"],
    "ங்": ["ங","ஙா","ஙி","ஙீ","ஙு","ஙூ","ஙெ","ஙே","ஙை","ஙொ","ஙோ","ஙௌ"],
    "ச்": ["ச","சா","சி","சீ","சு","சூ","செ","சே","சை","சொ","சோ","சௌ"],
    "ஞ்": ["ஞ","ஞா","ஞி","ஞீ","ஞு","ஞூ","ஞெ","ஞே","ஞை","ஞொ","ஞோ","ஞௌ"],
    "ட்": ["ட","டா","டி","டீ","டு","டூ","டெ","டே","டை","டொ","டோ","டௌ"],
    "ண்": ["ண","ணா","ணி","ணீ","ணு","ணூ","ணெ","ணே","ணை","ணொ","ணோ","ணௌ"],
    "த்": ["த","தா","தி","தீ","து","தூ","தெ","தே","தை","தொ","தோ","தௌ"],
    "ந்": ["ந","நா","நி","நீ","நு","நூ","நெ","நே","நை","நொ","நோ","நௌ"],
    "ப்": ["ப","பா","பி","பீ","பு","பூ","பெ","பே","பை","பொ","போ","பௌ"],
    "ம்": ["ம","மா","மி","மீ","மு","மூ","மெ","மே","மை","மொ","மோ","மௌ"],
    "ய்": ["ய","யா","யி","யீ","யு","யூ","யெ","யே","யை","யொ","யோ","யௌ"],
    "ர்": ["ர","ரா","ரி","ரீ","ரு","ரூ","ரெ","ரே","ரை","ரொ","ரோ","ரௌ"],
    "ல்": ["ல","லா","லி","லீ","லு","லூ","லெ","லே","லை","லொ","லோ","லௌ"],
    "வ்": ["வ","வா","வி","வீ","வு","வூ","வெ","வே","வை","வொ","வோ","வௌ"],
    "ழ்": ["ழ","ழா","ழி","ழீ","ழு","ழூ","ழெ","ழே","ழை","ழொ","ழோ","ழௌ"],
    "ள்": ["ள","ளா","ளி","ளீ","ளு","ளூ","ளெ","ளே","ளை","ளொ","ளோ","ளௌ"],
    "ற்": ["ற","றா","றி","றீ","று","றூ","றெ","றே","றை","றொ","றோ","றௌ"],
    "ன்": ["ன","னா","னி","னீ","னு","னூ","னெ","னே","னை","னொ","னோ","னௌ"],
    "க்ஷ்": ["க்ஷ","க்ஷா","க்ஷி","க்ஷீ","க்ஷு","க்ஷூ","க்ஷெ","க்ஷே","க்ஷை","க்ஷொ","க்ஷோ","க்ஷௌ"],
}

MEI_SET = set(UYIRMEI_MAP.keys())


# =========================================================
# 7. to_word
# =========================================================

def to_word(text: str) -> str:
    tokens = component_array(text)
    out = []
    i = 0

    while i < len(tokens):
        if (
            i + 1 < len(tokens)
            and tokens[i] in MEI_SET
            and tokens[i + 1] in UYIR_INDEX
        ):
            idx = UYIR_INDEX[tokens[i + 1]]
            out.append(UYIRMEI_MAP[tokens[i]][idx])
            i += 2
        else:
            out.append(tokens[i])
            i += 1

    return "".join(out)


def to_letters(word: str) -> str:
    tokens = component_array(word)
    return "".join(tokens)
# =========================================================
# 8. remove_final_suffix
# =========================================================

def remove_final_suffix(root: str, suffix: str) -> str:
    r = component_array(root)
    s = component_array(suffix)

    if r[-len(s):] == s:
        trimmed = "".join(r[:-len(s)])
        return to_word(trimmed)

    return root


