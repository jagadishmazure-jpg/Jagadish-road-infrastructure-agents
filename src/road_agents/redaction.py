"""PII redaction and brand-name check.

Redaction checklist (all tested): phone numbers, SSNs, card numbers, and
email addresses. Anything matching is replaced with a placeholder; nothing
is logged in the clear.

Brand check: the blocklist is stored as SHA-256 hashes only, never as plain
names, so the repo itself never contains the names it guards against. The
hashes were computed from real operator names out of band; the check flags
any text whose normalised words hash to a blocked value.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

_PHONE = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def redact(text: str) -> str:
    """Replace phone, SSN, card-number, and email matches with placeholders."""
    text = _EMAIL.sub("[EMAIL]", text)
    text = _SSN.sub("[SSN]", text)

    def _card_repl(match: re.Match) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        if 13 <= len(digits) <= 19:
            return "[CARD]"
        return match.group(0)

    text = _CARD.sub(_card_repl, text)
    text = _PHONE.sub("[PHONE]", text)
    return text


def _blocklist_path() -> Path:
    return Path(__file__).resolve().parent / "brand_blocklist.json"


def load_blocklist() -> list[str]:
    data = json.loads(_blocklist_path().read_text())
    return data["hashes"]


def scan_for_blocked_names(text: str) -> list[str]:
    """Return blocked hashes found in the text (words + adjacent word pairs)."""
    blocked = set(load_blocklist())
    words = re.findall(r"[a-z]+", text.lower())
    candidates = set(words)
    candidates.update(f"{a} {b}" for a, b in zip(words, words[1:]))
    candidates.update(f"{a} {b} {c}"
                      for a, b, c in zip(words, words[1:], words[2:]))
    found = []
    for candidate in candidates:
        digest = hashlib.sha256(candidate.encode()).hexdigest()
        if digest in blocked:
            found.append(digest)
    return sorted(found)
