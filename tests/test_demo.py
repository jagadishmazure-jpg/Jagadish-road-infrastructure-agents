from road_agents.demo import main


def test_demo_top_priority():
    out = main()
    assert out["top"] == "S5"
    assert out["top3"] == ["S5", "S2", "S7"]


def test_demo_closure_numbers():
    out = main()
    assert out["affected"] == 6
    assert out["stranded"] == 0
    assert out["added_minutes"] == 37.8
    assert out["confidence"] == 0.55
    assert sorted(out["overloaded"]) == ["S1", "S3", "S4"]


def test_demo_network_numbers():
    out = main()
    assert out["below_alert"] == 3
    assert out["avg_condition"] == 56.1
    assert out["total_km"] == 46.2
