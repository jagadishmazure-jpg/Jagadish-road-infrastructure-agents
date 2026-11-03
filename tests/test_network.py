import pytest

from road_agents.network import (Junction, RoadNetwork, Segment,
                                 sample_network)


def test_sample_network_shape():
    net = sample_network()
    assert len(net.junctions) == 6
    assert len(net.segments) == 8


def test_negative_length_rejected():
    with pytest.raises(ValueError):
        Segment("X", "J1", "J2", -1.0, 100, 50)


def test_zero_capacity_rejected():
    with pytest.raises(ValueError):
        Segment("X", "J1", "J2", 1.0, 0, 50)


def test_condition_out_of_range_rejected():
    with pytest.raises(ValueError):
        Segment("X", "J1", "J2", 1.0, 100, 101)


def test_negative_traffic_rejected():
    with pytest.raises(ValueError):
        Segment("X", "J1", "J2", 1.0, 100, 50, daily_traffic=-5)


def test_unknown_junction_reference_rejected():
    with pytest.raises(ValueError):
        RoadNetwork([Junction("J1", "A")],
                    [Segment("S1", "J1", "J9", 1.0, 100, 50)])


def test_duplicate_segment_id_rejected():
    net = sample_network()
    with pytest.raises(ValueError):
        RoadNetwork(net.junctions,
                    net.segments + [Segment("S1", "J1", "J2", 1.0, 100, 50)])


def test_shortest_path_direct_segment():
    net = sample_network()
    path, minutes = net.shortest_path("J2", "J3")
    assert path == ["S2"]
    assert minutes == pytest.approx(10.6, abs=0.1)


def test_travel_time_rises_with_extra_traffic():
    seg = Segment("X", "J1", "J2", 5.0, 1000, 80, daily_traffic=500)
    assert seg.travel_minutes(extra_traffic=500) > seg.travel_minutes()


def test_negative_extra_traffic_rejected():
    seg = Segment("X", "J1", "J2", 5.0, 1000, 80)
    with pytest.raises(ValueError):
        seg.travel_minutes(extra_traffic=-1)


def test_same_node_path_is_empty():
    net = sample_network()
    assert net.shortest_path("J1", "J1") == ([], 0.0)


def test_disconnected_pair_returns_none():
    net = RoadNetwork([Junction("A", "A"), Junction("B", "B")], [])
    assert net.shortest_path("A", "B") is None


def test_unknown_segment_raises():
    net = sample_network()
    with pytest.raises(KeyError):
        net.segment("S99")
