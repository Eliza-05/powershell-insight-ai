"""Pure bounded transformations of strings and bytes, with explicit encodings."""

import base64
import binascii
import re
import unicodedata

from .budget import Budget

ENCODINGS = {"unicode": "utf-16-le", "bigendianunicode": "utf-16-be", "utf8": "utf-8", "ascii": "ascii"}


class RecoveryError(Exception):
    pass


def decode_base64(value: str, budget: Budget) -> bytes:
    budget.spend(len(value))
    # Only .NET's ASCII whitespace subset is ignored; no padding repair or alphabet guessing.
    compact = value.translate(str.maketrans("", "", " \t\r\n"))
    if not re.fullmatch(r"[A-Za-z0-9+/]*={0,2}", compact) or len(compact) % 4:
        raise RecoveryError("Invalid or truncated standard Base64; padding is not repaired.")
    estimated = len(compact) // 4 * 3 - (len(compact) - len(compact.rstrip("=")))
    budget.check_value(estimated)
    try:
        return base64.b64decode(compact, validate=True)
    except (ValueError, binascii.Error) as error:
        raise RecoveryError("Invalid standard Base64.") from error


def decode_text(value: bytes, encoding: str, budget: Budget) -> str:
    codec = ENCODINGS.get(encoding.casefold())
    if codec is None:
        raise RecoveryError("Encoding is unknown or outside Unicode/BigEndianUnicode/UTF8/ASCII.")
    budget.spend(len(value))
    if codec == "utf-16-le" and value.startswith(b"\xfe\xff"):
        raise RecoveryError("UTF-16BE BOM contradicts the explicit UTF-16LE encoding.")
    if codec == "utf-16-be" and value.startswith(b"\xff\xfe"):
        raise RecoveryError("UTF-16LE BOM contradicts the explicit UTF-16BE encoding.")
    try:
        text = value.decode(codec, errors="strict")
    except UnicodeError as error:
        raise RecoveryError("Bytes are incompatible with the explicit encoding.") from error
    if any(unicodedata.category(c) in {"Cc", "Cs", "Cn"} and c not in "\t\n\r" for c in text):
        raise RecoveryError("Decoded data contains binary/control or unassigned characters; not accepted as text.")
    budget.check_value(len(text.encode("utf-8")))
    return text


def concatenate(parts: list[str], terms: int, budget: Budget) -> str:
    if terms > budget.limits.max_concat_terms:
        from .budget import LimitReached
        raise LimitReached("max_concat_terms")
    size = sum(len(p.encode("utf-8")) for p in parts)
    budget.check_value(size)
    budget.spend(size)
    return "".join(parts)
