"""UTF-8 text ↔ byte strings in base 2 / 8 / 10 / 16."""

from __future__ import annotations

import re
from dataclasses import dataclass

BASES = (2, 8, 10, 16)


@dataclass
class Result:
    ok: bool
    text: str
    error: str = ""


def _fmt_byte(b: int, base: int, upper: bool) -> str:
    if base == 2:
        return f"{b:08b}"
    if base == 8:
        return f"{b:03o}"
    if base == 10:
        return str(b)
    # 16
    return f"{b:02X}" if upper else f"{b:02x}"


def to_bytes_view(
    text: str,
    *,
    base: int = 16,
    spaced: bool = True,
    upper: bool = True,
) -> Result:
    if base not in BASES:
        return Result(False, text, "основание: 2, 8, 10 или 16")
    data = text.encode("utf-8")
    if not data:
        return Result(True, "")
    parts = [_fmt_byte(b, base, upper) for b in data]
    out = " ".join(parts) if spaced else "".join(parts)
    return Result(True, out)


def from_bytes_view(raw: str, *, base: int = 16) -> Result:
    if base not in BASES:
        return Result(False, raw, "основание: 2, 8, 10 или 16")
    s = raw.strip()
    if not s:
        return Result(True, "")

    # tokenized by whitespace if present; else split by fixed width
    if re.search(r"\s", s):
        tokens = re.split(r"\s+", s)
    else:
        tokens = _split_compact(s, base)
        if tokens is None:
            return Result(False, raw, _compact_error(base))

    data = bytearray()
    for i, tok in enumerate(tokens):
        if not tok:
            continue
        ok, val, err = _parse_token(tok, base)
        if not ok:
            return Result(False, raw, f"токен {i + 1}: {err}")
        data.append(val)

    try:
        text = bytes(data).decode("utf-8")
    except UnicodeDecodeError:
        return Result(False, raw, "байты не UTF-8 — не получается текст")
    return Result(True, text)


def _split_compact(s: str, base: int) -> list[str] | None:
    if base == 10:
        # один байт без пробела ок (65); несколько — только с пробелами
        if re.fullmatch(r"[0-9]+", s):
            try:
                val = int(s, 10)
            except ValueError:
                return None
            if 0 <= val <= 255:
                return [s]
        return None
    if base == 16:
        compact = re.sub(r"\s+", "", s)
        if len(compact) % 2 != 0:
            return None
        return [compact[i : i + 2] for i in range(0, len(compact), 2)]
    if base == 2:
        if not re.fullmatch(r"[01]+", s):
            return None
        # 1100110 → 01100110 (часто пишут без ведущих нулей)
        bits = s
        pad = (-len(bits)) % 8
        if pad:
            bits = ("0" * pad) + bits
        return [bits[i : i + 8] for i in range(0, len(bits), 8)]
    if base == 8:
        if not re.fullmatch(r"[0-7]+", s):
            return None
        # дополняем слева до кратности 3
        digits = s
        pad = (-len(digits)) % 3
        if pad:
            digits = ("0" * pad) + digits
        tokens = [digits[i : i + 3] for i in range(0, len(digits), 3)]
        # каждый токен должен быть байтом
        for t in tokens:
            if int(t, 8) > 255:
                return None
        return tokens
    return None


def _compact_error(base: int) -> str:
    if base == 10:
        return "для десятичной нужны пробелы между байтами (напр. 72 101)"
    if base == 16:
        return "нечётная длина hex"
    if base == 2:
        return "ожидались только 0 и 1"
    if base == 8:
        return "ожидались восьмеричные цифры 0-7"
    return "не удалось разобрать"


def _parse_token(tok: str, base: int) -> tuple[bool, int, str]:
    try:
        if base == 16:
            if not re.fullmatch(r"[0-9A-Fa-f]+", tok):
                return False, 0, "ожидались hex-цифры"
            if len(tok) > 2:
                return False, 0, "слишком длинный hex-байт (макс 2 цифры)"
            val = int(tok, 16)
        elif base == 2:
            if not re.fullmatch(r"[01]+", tok):
                return False, 0, "ожидались 0 и 1"
            if len(tok) > 8:
                return False, 0, "слишком длинный бит-байт (макс 8)"
            # 1100110 → как 01100110
            val = int(tok, 2)
        elif base == 8:
            if not re.fullmatch(r"[0-7]+", tok):
                return False, 0, "ожидались восьмеричные цифры"
            val = int(tok, 8)
        else:
            if not re.fullmatch(r"[0-9]+", tok):
                return False, 0, "ожидались цифры"
            val = int(tok, 10)
    except ValueError:
        return False, 0, "не число"

    if val < 0 or val > 255:
        return False, 0, f"байт вне 0..255 ({val})"
    return True, val, ""


# backward-compatible aliases
def to_hex(text: str, *, spaced: bool = True, upper: bool = True) -> Result:
    return to_bytes_view(text, base=16, spaced=spaced, upper=upper)


def from_hex(raw: str) -> Result:
    return from_bytes_view(raw, base=16)
