import pytest

from road_agents.agents import (MaintenancePlannerAgent, priority_score,
                                repair_cost)
from road_agents.network import sample_network

PLANNER = MaintenancePlannerAgent()


def test_top_priority_is_worst_condition_high_load_segment():
    ranking = PLANNER.rank(sample_network())
    assert ranking[0].segment.id == "S5"
    assert ranking[0].score == pytest.approx(0.689, abs=0.001)


def test_top_three_order():
    ranking = PLANNER.rank(sample_network())
    assert [r.segment.id for r in ranking[:3]] == ["S5", "S2", "S7"]


def test_ranking_scores_descend():
    scores = [r.score for r in PLANNER.rank(sample_network())]
    assert scores == sorted(scores, reverse=True)


def test_detect_flags_condition_alert_segments():
    detected = PLANNER.detect(sample_network())
    assert [s.id for s in detected] == ["S2", "S5", "S7"]


def test_negative_budget_rejected():
    with pytest.raises(ValueError):
        PLANNER.plan_within_budget(sample_network(), -100)


def test_zero_budget_selects_nothing():
    assert PLANNER.plan_within_budget(sample_network(), 0) == []


def test_budget_selects_only_fitting_top_segment():
    # S5 costs 49,248; the next-ranked segments do not fit after it.
    chosen = PLANNER.plan_within_budget(sample_network(), 50000)
    assert [r.segment.id for r in chosen] == ["S5"]


def test_large_budget_selects_all():
    chosen = PLANNER.plan_within_budget(sample_network(), 10_000_000)
    assert len(chosen) == 8


def test_repair_cost_formula():
    net = sample_network()
    assert repair_cost(net.segment("S5")) == pytest.approx(49248.0, abs=0.01)


def test_priority_score_reorders_on_condition_change():
    net = sample_network()
    good = net.segment("S1")
    bad = net.segment("S5")
    assert priority_score(bad) > priority_score(good)
