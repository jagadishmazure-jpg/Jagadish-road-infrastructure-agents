from road_agents.agents import RecoveryChecklist, measure, run_cycle
from road_agents.gates import AuditLog
from road_agents.network import sample_network


def test_cycle_alerts_and_ranking():
    result = run_cycle(sample_network(), closure_segment="S2")
    assert result.alerts == ["S2", "S5", "S7"]
    assert result.ranking[0] == "S5"
    assert result.closure_impact is not None
    assert result.closure_impact.closed_segment == "S2"


def test_cycle_without_closure_has_no_impact_or_recovery():
    result = run_cycle(sample_network())
    assert result.closure_impact is None
    assert result.recovery is None


def test_cycle_records_audit_entries():
    result = run_cycle(sample_network(), closure_segment="S2",
                       audit_log=AuditLog())
    assert result.audit_entries == ["cycle.detect", "cycle.triage",
                                    "cycle.simulate_closure"]


def test_recovery_checklist_gates_reopening():
    checklist = RecoveryChecklist("S2")
    assert checklist.ready_to_reopen is False
    assert checklist.missing_steps() == ["surface_verified",
                                         "signage_removed",
                                         "traffic_counted"]
    checklist.surface_verified = True
    checklist.signage_removed = True
    checklist.traffic_counted = True
    assert checklist.ready_to_reopen is True
    assert checklist.missing_steps() == []


def test_network_metrics():
    metrics = measure(sample_network())
    assert metrics.average_condition == 56.125
    assert metrics.segments_below_alert == 3
    assert metrics.segments_overloaded == 0
    assert metrics.total_length_km == 46.2


def test_cycle_never_issues_a_closure():
    # run_cycle is advisory only; issuing requires ClosureGate + Approval.
    result = run_cycle(sample_network(), closure_segment="S2")
    assert not hasattr(result, "issued_recommendation")
