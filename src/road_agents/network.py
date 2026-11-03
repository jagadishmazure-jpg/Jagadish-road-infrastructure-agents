"""Road-network model: junctions and segments with validation.

Synthetic data only. No real road network, operator, or place is represented.
Travel time is a simple deterministic function of length, free-flow speed,
and a congestion factor from traffic volume over capacity. It is a planning
approximation, not a traffic-engineering model.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field

FREE_FLOW_KMH = 50.0


@dataclass(frozen=True)
class Junction:
    """A node in the road graph (a junction, not a real place)."""

    id: str
    label: str


@dataclass(frozen=True)
class Segment:
    """An undirected road segment between two junctions."""

    id: str
    start: str
    end: str
    length_km: float
    capacity_veh_per_hour: float
    condition: float  # 0 (failed) .. 100 (new)
    daily_traffic: float = 0.0
    risk: float = 0.0  # 0..1, e.g. flood / incident exposure, synthetic

    def __post_init__(self) -> None:
        if self.length_km <= 0:
            raise ValueError("length_km must be positive")
        if self.capacity_veh_per_hour <= 0:
            raise ValueError("capacity_veh_per_hour must be positive")
        if not 0.0 <= self.condition <= 100.0:
            raise ValueError("condition must be between 0 and 100")
        if self.daily_traffic < 0:
            raise ValueError("daily_traffic must not be negative")
        if not 0.0 <= self.risk <= 1.0:
            raise ValueError("risk must be between 0 and 1")

    def travel_minutes(self, extra_traffic: float = 0.0) -> float:
        """Free-flow time inflated by congestion (traffic over capacity)."""
        if extra_traffic < 0:
            raise ValueError("extra_traffic must not be negative")
        load = (self.daily_traffic + extra_traffic) / self.capacity_veh_per_hour
        congestion = 1.0 + 0.5 * min(load, 2.0)
        return self.length_km / FREE_FLOW_KMH * 60.0 * congestion

    def utilisation(self, extra_traffic: float = 0.0) -> float:
        if extra_traffic < 0:
            raise ValueError("extra_traffic must not be negative")
        return (self.daily_traffic + extra_traffic) / self.capacity_veh_per_hour


@dataclass
class RoadNetwork:
    """An undirected graph of junctions and segments."""

    junctions: list[Junction] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)

    def __post_init__(self) -> None:
        junction_ids = {j.id for j in self.junctions}
        if len(junction_ids) != len(self.junctions):
            raise ValueError("duplicate junction id")
        segment_ids = {s.id for s in self.segments}
        if len(segment_ids) != len(self.segments):
            raise ValueError("duplicate segment id")
        for seg in self.segments:
            if seg.start not in junction_ids or seg.end not in junction_ids:
                raise ValueError(f"segment {seg.id} references an unknown junction")

    def segment(self, segment_id: str) -> Segment:
        for seg in self.segments:
            if seg.id == segment_id:
                return seg
        raise KeyError(f"unknown segment {segment_id}")

    def neighbours(self, junction_id: str, excluded: set[str] | None = None):
        excluded = excluded or set()
        for seg in self.segments:
            if seg.id in excluded:
                continue
            if seg.start == junction_id:
                yield seg.end, seg
            elif seg.end == junction_id:
                yield seg.start, seg

    def shortest_path(self, origin: str, destination: str,
                      excluded: set[str] | None = None):
        """Dijkstra by travel minutes. Returns (segment ids, minutes) or None."""
        if origin == destination:
            return [], 0.0
        dist: dict[str, float] = {origin: 0.0}
        prev: dict[str, tuple[str, str]] = {}
        queue: list[tuple[float, str]] = [(0.0, origin)]
        while queue:
            cost, node = heapq.heappop(queue)
            if cost > dist.get(node, float("inf")):
                continue
            if node == destination:
                break
            for nxt, seg in self.neighbours(node, excluded):
                new_cost = cost + seg.travel_minutes()
                if new_cost < dist.get(nxt, float("inf")):
                    dist[nxt] = new_cost
                    prev[nxt] = (node, seg.id)
                    heapq.heappush(queue, (new_cost, nxt))
        if destination not in dist:
            return None
        path: list[str] = []
        node = destination
        while node != origin:
            node, seg_id = prev[node]
            path.append(seg_id)
        path.reverse()
        return path, dist[destination]

    def all_pairs_paths(self, excluded: set[str] | None = None):
        """Shortest path for every ordered junction pair (excluding self-pairs)."""
        ids = [j.id for j in self.junctions]
        out = {}
        for origin in ids:
            for destination in ids:
                if origin != destination:
                    out[(origin, destination)] = self.shortest_path(
                        origin, destination, excluded)
        return out


def sample_network() -> RoadNetwork:
    """The demo network: 6 fictional junctions, 8 synthetic segments.

    Junction labels are generic descriptors, not real places. All numbers
    are invented for the demo and are asserted by the test suite.
    """
    junctions = [
        Junction("J1", "Northgate"),
        Junction("J2", "Millcross"),
        Junction("J3", "Eastfield"),
        Junction("J4", "Harborview"),
        Junction("J5", "Old Quarry"),
        Junction("J6", "Riverside"),
    ]
    segments = [
        Segment("S1", "J1", "J2", 4.2, 1800, 82, 900, 0.10),
        Segment("S2", "J2", "J3", 6.0, 1500, 38, 1400, 0.40),
        Segment("S3", "J1", "J4", 8.5, 1200, 61, 700, 0.20),
        Segment("S4", "J4", "J3", 3.1, 2000, 74, 1100, 0.10),
        Segment("S5", "J2", "J5", 5.4, 900, 24, 850, 0.60),
        Segment("S6", "J5", "J6", 2.8, 800, 55, 400, 0.30),
        Segment("S7", "J3", "J6", 7.2, 1600, 47, 1300, 0.50),
        Segment("S8", "J1", "J6", 9.0, 1000, 68, 500, 0.15),
    ]
    return RoadNetwork(junctions, segments)
