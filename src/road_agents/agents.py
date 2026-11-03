"""Agents: maintenance planning, closure/detour simulation, recovery, metrics.

These are deterministic planning agents over the synthetic road graph: they
detect (condition thresholds), triage (ranked maintenance), respond (detour
simulation behind a human gate), recover (reopening checklist), and measure
(network health metrics). Nothing here issues a real closure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .network import RoadNetwork, Segment

CONDITION_ALERT = 50.0
COST_PER_KM = 12000.0


def priority_score(seg: Segment) -> float:
    """0..1-ish score: worse condition, higher load, higher risk rank first."""
    condition_part = 0.5 * (100.0 - seg.condition) / 100.0
    load_part = 0.3 * min(seg.utilisation(), 1.5) / 1.5
    risk_part = 0.2 * seg.risk
    return condition_part + load_part + risk_part


def repair_cost(seg: Segment) -> float:
    """Synthetic estimate: worse condition costs more per kilometre."""
    if seg.length_km < 0:
        raise ValueError("length_km must not be negative")
    return seg.length_km * COST_PER_KM * (100.0 - seg.condition) / 100.0


@dataclass(frozen=True)
class RankedSegment:
    segment: Segment
    score: float
    cost: float


class MaintenancePlannerAgent:
    """Ranks segments for maintenance by condition, traffic load, and risk."""

    def detect(self, network: RoadNetwork) -> list[Segment]:
        """Segments at or below the condition alert threshold."""
        return [s for s in network.segments if s.condition <= CONDITION_ALERT]

    def rank(self, network: RoadNetwork) -> list[RankedSegment]:
        ranked = [RankedSegment(s, priority_score(s), repair_cost(s))
                  for s in network.segments]
        ranked.sort(key=lambda r: r.score, reverse=True)
        return ranked

    def plan_within_budget(self, network: RoadNetwork,
                           budget: float) -> list[RankedSegment]:
        """Top-ranked segments whose cumulative cost fits the budget.

        Negative budgets are rejected, never silently clamped to zero.
        """
        if budget < 0:
            raise ValueError("budget must not be negative")
        chosen: list[RankedSegment] = []
        spent = 0.0
        for item in self.rank(network):
            if spent + item.cost <= budget:
                chosen.append(item)
                spent += item.cost
        return chosen


@dataclass(frozen=True)
class AffectedRoute:
    origin: str
    destination: str
    original_segments: list[str]
    original_minutes: float
    reroute_segments: list[str] | None
    reroute_minutes: float | None

    @property
    def added_minutes(self) -> float | None:
        if self.reroute_minutes is None:
            return None
        return self.reroute_minutes - self.original_minutes

    @property
    def stranded(self) -> bool:
        return self.reroute_segments is None


@dataclass(frozen=True)
class OverloadedAlternate:
    segment_id: str
    utilisation_before: float
    utilisation_after: float


@dataclass(frozen=True)
class ClosureImpact:
    closed_segment: str
    affected_routes: list[AffectedRoute]
    overloaded_alternates: list[OverloadedAlternate]
    total_added_minutes: float
    stranded_routes: int

    @property
    def confidence(self) -> float:
        """Lower when many routes strand or alternates overload."""
        if self.stranded_routes:
            return 0.3
        if self.overloaded_alternates:
            return 0.55
        return 0.9


class DetourSimulatorAgent:
    """Simulates a closure: affected routes, added time, overloaded alternates."""

    def simulate_closure(self, network: RoadNetwork,
                         segment_id: str) -> ClosureImpact:
        closed = network.segment(segment_id)  # KeyError on unknown id
        baseline = network.all_pairs_paths()
        rerouted = network.all_pairs_paths(excluded={segment_id})
        affected: list[AffectedRoute] = []
        diverted_traffic: dict[str, float] = {}
        for (origin, destination), base in baseline.items():
            if base is None or segment_id not in base[0]:
                continue
            alt = rerouted[(origin, destination)]
            if alt is None:
                affected.append(AffectedRoute(origin, destination, base[0],
                                              base[1], None, None))
            else:
                affected.append(AffectedRoute(origin, destination, base[0],
                                              base[1], alt[0], alt[1]))
                for seg_id in alt[0]:
                    diverted_traffic[seg_id] = (
                        diverted_traffic.get(seg_id, 0.0) + closed.daily_traffic)
        overloaded = []
        for seg_id, extra in diverted_traffic.items():
            seg = network.segment(seg_id)
            before = seg.utilisation()
            after = seg.utilisation(extra)
            if after > 1.0 and after > before:
                overloaded.append(OverloadedAlternate(seg_id, before, after))
        total_added = sum(r.added_minutes or 0.0 for r in affected)
        stranded = sum(1 for r in affected if r.stranded)
        return ClosureImpact(segment_id, affected, overloaded, total_added,
                             stranded)


@dataclass
class RecoveryChecklist:
    """Reopening steps after a closure; all must pass before reopening."""

    closed_segment: str
    surface_verified: bool = False
    signage_removed: bool = False
    traffic_counted: bool = False

    @property
    def ready_to_reopen(self) -> bool:
        return self.surface_verified and self.signage_removed \
            and self.traffic_counted

    def missing_steps(self) -> list[str]:
        missing = []
        if not self.surface_verified:
            missing.append("surface_verified")
        if not self.signage_removed:
            missing.append("signage_removed")
        if not self.traffic_counted:
            missing.append("traffic_counted")
        return missing


@dataclass(frozen=True)
class NetworkMetrics:
    average_condition: float
    segments_below_alert: int
    segments_overloaded: int
    total_length_km: float


def measure(network: RoadNetwork) -> NetworkMetrics:
    """Governance measurement snapshot for the network."""
    conditions = [s.condition for s in network.segments]
    avg = sum(conditions) / len(conditions) if conditions else 0.0
    below = sum(1 for s in network.segments if s.condition <= CONDITION_ALERT)
    overloaded = sum(1 for s in network.segments if s.utilisation() > 1.0)
    total_km = sum(s.length_km for s in network.segments)
    return NetworkMetrics(avg, below, overloaded, total_km)


@dataclass
class PipelineResult:
    """One detect -> triage -> respond -> recover -> measure cycle."""

    alerts: list[str]
    ranking: list[str]
    closure_impact: ClosureImpact | None
    recovery: RecoveryChecklist | None
    metrics: NetworkMetrics
    audit_entries: list[str] = field(default_factory=list)


def run_cycle(network: RoadNetwork, closure_segment: str | None = None,
              audit_log=None) -> PipelineResult:
    """Run the full agent cycle; closure simulation stays advisory only.

    A closure recommendation is never issued here: issuing requires the
    human gate in gates.py, which this function deliberately does not call.
    """
    planner = MaintenancePlannerAgent()
    simulator = DetourSimulatorAgent()
    alerts = [s.id for s in planner.detect(network)]
    ranking = [r.segment.id for r in planner.rank(network)]
    impact = simulator.simulate_closure(network, closure_segment) \
        if closure_segment else None
    recovery = RecoveryChecklist(closure_segment) if closure_segment else None
    entries: list[str] = []
    if audit_log is not None:
        audit_log.append("cycle.detect", {"alerts": alerts})
        audit_log.append("cycle.triage", {"ranking": ranking})
        if impact is not None:
            audit_log.append("cycle.simulate_closure",
                             {"segment": impact.closed_segment,
                              "affected": len(impact.affected_routes)})
        entries = [e.action for e in audit_log.entries]
    return PipelineResult(alerts, ranking, impact, recovery, measure(network),
                          entries)
