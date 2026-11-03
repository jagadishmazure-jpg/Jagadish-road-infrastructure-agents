import dataclasses

from road_agents.gates import AuditLog


def _log_with_entries():
    log = AuditLog()
    log.append("cycle.detect", {"alerts": ["S2", "S5", "S7"]})
    log.append("cycle.triage", {"ranking": ["S5", "S2", "S7"]})
    return log


def test_chain_verifies():
    assert _log_with_entries().verify() is True


def test_tampered_detail_detected():
    log = _log_with_entries()
    entry = log.entries[0]
    log.entries[0] = dataclasses.replace(entry, detail={"alerts": ["S1"]})
    assert log.verify() is False


def test_sequence_mismatch_detected():
    log = _log_with_entries()
    entry = log.entries[1]
    log.entries[1] = dataclasses.replace(entry, seq=99)
    assert log.verify() is False


def test_seal_verifies_on_intact_log():
    log = _log_with_entries()
    seal = log.seal()
    assert log.verify(seal) is True


def test_tail_truncation_detected_by_seal():
    log = _log_with_entries()
    seal = log.seal()
    log.entries.pop()
    assert log.verify(seal) is False


def test_empty_log_seals_and_verifies():
    log = AuditLog()
    seal = log.seal()
    assert log.verify(seal) is True
