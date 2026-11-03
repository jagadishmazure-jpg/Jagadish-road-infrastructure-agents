"""Human gate for closure recommendations + hash-chained audit log.

Rules (all tested):
- An approval is named-person, single-use, scoped to one segment, and
  expiring. Anonymous, reused, expired, or wrong-scope approvals fail.
- Low-confidence recommendations (stranded routes or overloaded alternates)
  need a senior approver; a regular approver is not enough.
- Ambiguous consent text is rejected: a message that both agrees and
  reverses ("yes, wait, no") is self-contradicting and counts as no consent.
- Absent approval is rejected: there is no path that issues a closure
  recommendation without a valid approval object.
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field

AGREE = {"yes", "approve", "approved", "go", "confirm", "confirmed"}
REVERSE = {"no", "wait", "stop", "hold", "cancel", "not yet", "on hold"}


def parse_consent(text: str) -> str:
    """Return 'approved', 'rejected', or 'ambiguous'.

    Ambiguous covers self-contradicting consent ("yes, wait, no") and any
    message with no clear signal at all.
    """
    words = set(re.findall(r"[a-z]+", text.lower()))
    agrees = bool(words & AGREE)
    reverses = bool(words & REVERSE)
    if agrees and reverses:
        return "ambiguous"
    if agrees:
        return "approved"
    if reverses:
        return "rejected"
    return "ambiguous"


@dataclass
class Approval:
    """A single-use, scoped, expiring human approval."""

    approver: str  # named person; empty means anonymous and is invalid
    role: str = "operator"  # "operator" or "senior"
    scope_segment: str = ""
    expires_at: float = 0.0
    consent_text: str = ""
    _used: bool = field(default=False, repr=False)

    def is_valid(self, segment_id: str, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        if not self.approver.strip():
            return False
        if self._used:
            return False
        if self.scope_segment != segment_id:
            return False
        if now > self.expires_at:
            return False
        if parse_consent(self.consent_text) != "approved":
            return False
        return True

    def consume(self) -> None:
        self._used = True


@dataclass(frozen=True)
class ClosureRecommendation:
    segment_id: str
    confidence: float
    total_added_minutes: float
    status: str  # "issued" or "blocked"
    reason: str = ""


class ClosureGate:
    """The only path that may issue a closure recommendation."""

    LOW_CONFIDENCE = 0.6

    def issue(self, segment_id: str, confidence: float,
              total_added_minutes: float,
              approval: Approval | None,
              now: float | None = None) -> ClosureRecommendation:
        if approval is None:
            return ClosureRecommendation(segment_id, confidence,
                                         total_added_minutes, "blocked",
                                         "absent approval")
        if not approval.is_valid(segment_id, now=now):
            return ClosureRecommendation(segment_id, confidence,
                                         total_added_minutes, "blocked",
                                         "invalid approval")
        if confidence < self.LOW_CONFIDENCE and approval.role != "senior":
            return ClosureRecommendation(segment_id, confidence,
                                         total_added_minutes, "blocked",
                                         "low confidence requires senior approver")
        approval.consume()
        return ClosureRecommendation(segment_id, confidence,
                                     total_added_minutes, "issued", "")


@dataclass
class AuditEntry:
    seq: int
    action: str
    detail: dict
    prev_hash: str
    entry_hash: str


class AuditLog:
    """Hash-chained audit trail with a seal that detects tail truncation."""

    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []
        self._seal: str | None = None

    def append(self, action: str, detail: dict) -> AuditEntry:
        prev = self.entries[-1].entry_hash if self.entries else "GENESIS"
        payload = f"{len(self.entries)}|{action}|{sorted(detail.items())}|{prev}"
        digest = hashlib.sha256(payload.encode()).hexdigest()
        entry = AuditEntry(len(self.entries), action, detail, prev, digest)
        self.entries.append(entry)
        return entry

    def seal(self) -> str:
        """Seal the log; verify(seal) later fails if entries were removed."""
        tail = self.entries[-1].entry_hash if self.entries else "EMPTY"
        self._seal = hashlib.sha256(
            f"seal|{len(self.entries)}|{tail}".encode()).hexdigest()
        return self._seal

    def verify(self, seal: str | None = None) -> bool:
        prev = "GENESIS"
        for i, entry in enumerate(self.entries):
            if entry.seq != i or entry.prev_hash != prev:
                return False
            payload = (f"{i}|{entry.action}|{sorted(entry.detail.items())}"
                       f"|{prev}")
            if hashlib.sha256(payload.encode()).hexdigest() != entry.entry_hash:
                return False
            prev = entry.entry_hash
        if seal is not None:
            tail = self.entries[-1].entry_hash if self.entries else "EMPTY"
            expect = hashlib.sha256(
                f"seal|{len(self.entries)}|{tail}".encode()).hexdigest()
            if expect != seal:
                return False
        return True
