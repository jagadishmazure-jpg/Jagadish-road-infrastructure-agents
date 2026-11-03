import pytest

from road_agents.agents import DetourSimulatorAgent
from road_agents.network import (Junction, RoadNetwork, Segment,
                                 sample_network)

SIM = DetourSimulatorAgent()


def test_closure_affected_route_count():
    impact = SIM.simulate_closure(sample_network(), "S2")
    assert len(impact.affected_routes) == 6


def test_closure_strands_nothing_on_sample():
    impact = SIM.simulate_closure(sample_network(), "S2")
    assert impact.stranded_routes == 0


def test_closure_total_added_minutes():
    impact = SIM.simulate_closure(sample_network(), "S2")
    assert impact.total_added_minutes == pytest.approx(37.8, abs=0.1)


def test_closure_confidence_is_low_when_alternates_overload():
    impact = SIM.simulate_closure(sample_network(), "S2")
    assert impact.confidence == 0.55


def test_closure_overloaded_alternates():
    impact = SIM.simulate_closure(sample_network(), "S2")
    assert {o.segment_id for o in impact.overloaded_alternates} == {
        "S1", "S3", "S4"}


def test_specific_reroute_added_minutes():
    impact = SIM.simulate_closure(sample_network(), "S2")
    route = [r for r in impact.affected_routes
             if (r.origin, r.destination) == ("J2", "J3")][0]
    assert route.added_minutes == pytest.approx(13.7, abs=0.1)
    assert route.reroute_segments == ["S1", "S3", "S4"]


def test_every_affected_reroute_is_longer():
    impact = SIM.simulate_closure(sample_network(), "S2")
    for route in impact.affected_routes:
        assert route.added_minutes is not None and route.added_minutes > 0


def test_unknown_segment_raises():
    with pytest.raises(KeyError):
        SIM.simulate_closure(sample_network(), "S99")


def test_closure_can_strand_routes():
    net = RoadNetwork(
        [Junction("A", "A"), Junction("B", "B"), Junction("C", "C")],
        [Segment("S1", "A", "B", 2.0, 1000, 90, 100),
         Segment("S2", "B", "C", 2.0, 1000, 90, 100)])
    impact = SIM.simulate_closure(net, "S1")
    assert impact.stranded_routes == 4  # ordered pairs: A->B, A->C, B->A, C->A
    assert impact.confidence == 0.3
    stranded = [r for r in impact.affected_routes if r.stranded]
    assert stranded[0].added_minutes is None
