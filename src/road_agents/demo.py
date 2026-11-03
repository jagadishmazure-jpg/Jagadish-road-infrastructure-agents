"""Demo: run the agent cycle on the synthetic network and print numbers.

Every number printed here is also asserted by the test suite; the README
quotes only these numbers.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from road_agents.agents import (DetourSimulatorAgent, MaintenancePlannerAgent,
                                measure, run_cycle)
from road_agents.gates import AuditLog
from road_agents.network import sample_network


def main() -> dict:
    network = sample_network()
    planner = MaintenancePlannerAgent()
    ranking = planner.rank(network)
    simulator = DetourSimulatorAgent()
    impact = simulator.simulate_closure(network, "S2")
    metrics = measure(network)
    result = run_cycle(network, closure_segment="S2", audit_log=AuditLog())

    print("Top maintenance priority:", ranking[0].segment.id,
          f"score={ranking[0].score:.3f}")
    print("Top 3:", ", ".join(r.segment.id for r in ranking[:3]))
    print("Segments below condition alert:",
          metrics.segments_below_alert)
    print("Average condition:", f"{metrics.average_condition:.1f}")
    print("Total network length (km):", f"{metrics.total_length_km:.1f}")
    print("Closure S2 affected routes:", len(impact.affected_routes))
    print("Closure S2 stranded routes:", impact.stranded_routes)
    print("Closure S2 total added minutes:",
          f"{impact.total_added_minutes:.1f}")
    print("Closure S2 confidence:", impact.confidence)
    print("Closure S2 overloaded alternates:",
          [o.segment_id for o in impact.overloaded_alternates])
    print("Pipeline audit entries:", result.audit_entries)
    return {
        "top": ranking[0].segment.id,
        "top3": [r.segment.id for r in ranking[:3]],
        "below_alert": metrics.segments_below_alert,
        "avg_condition": round(metrics.average_condition, 1),
        "total_km": round(metrics.total_length_km, 1),
        "affected": len(impact.affected_routes),
        "stranded": impact.stranded_routes,
        "added_minutes": round(impact.total_added_minutes, 1),
        "confidence": impact.confidence,
        "overloaded": [o.segment_id for o in impact.overloaded_alternates],
    }


if __name__ == "__main__":
    main()
