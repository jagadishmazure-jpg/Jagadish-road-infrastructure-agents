import time


from road_agents.gates import Approval, ClosureGate, parse_consent

GATE = ClosureGate()
NOW = time.time()


def _approval(**overrides):
    base = dict(approver="Priya Raman", role="operator", scope_segment="S2",
                expires_at=NOW + 3600, consent_text="yes, approved")
    base.update(overrides)
    return Approval(**base)


def test_valid_approval_issues():
    rec = GATE.issue("S2", 0.9, 37.8, _approval(), now=NOW)
    assert rec.status == "issued"


def test_approval_is_single_use():
    approval = _approval()
    assert GATE.issue("S2", 0.9, 1.0, approval, now=NOW).status == "issued"
    assert GATE.issue("S2", 0.9, 1.0, approval, now=NOW).status == "blocked"


def test_expired_approval_blocked():
    rec = GATE.issue("S2", 0.9, 1.0, _approval(expires_at=NOW - 10), now=NOW)
    assert rec.status == "blocked" and rec.reason == "invalid approval"


def test_anonymous_approval_blocked():
    rec = GATE.issue("S2", 0.9, 1.0, _approval(approver="  "), now=NOW)
    assert rec.status == "blocked"


def test_wrong_scope_approval_blocked():
    rec = GATE.issue("S2", 0.9, 1.0, _approval(scope_segment="S5"), now=NOW)
    assert rec.status == "blocked"


def test_absent_approval_blocked():
    rec = GATE.issue("S2", 0.9, 1.0, None, now=NOW)
    assert rec.status == "blocked" and rec.reason == "absent approval"


def test_low_confidence_operator_blocked():
    rec = GATE.issue("S2", 0.55, 37.8, _approval(), now=NOW)
    assert rec.status == "blocked"
    assert "senior" in rec.reason


def test_low_confidence_senior_issues():
    rec = GATE.issue("S2", 0.55, 37.8, _approval(role="senior"), now=NOW)
    assert rec.status == "issued"


def test_high_confidence_operator_issues():
    rec = GATE.issue("S2", 0.9, 1.0, _approval(), now=NOW)
    assert rec.status == "issued"


def test_self_contradicting_consent_is_ambiguous():
    assert parse_consent("yes, wait, no") == "ambiguous"
    assert parse_consent("approved, hold on, no") == "ambiguous"


def test_clear_consent_parses():
    assert parse_consent("yes please") == "approved"
    assert parse_consent("no") == "rejected"
    assert parse_consent("maybe later") == "ambiguous"


def test_ambiguous_consent_approval_blocked():
    rec = GATE.issue("S2", 0.9, 1.0,
                     _approval(consent_text="yes, wait, no"), now=NOW)
    assert rec.status == "blocked"


def test_rejected_consent_approval_blocked():
    rec = GATE.issue("S2", 0.9, 1.0, _approval(consent_text="no"), now=NOW)
    assert rec.status == "blocked"
