# Implementation guide

For adopters who want to reuse this pattern on their own network data.

## 1. Bring your own network

Build a `RoadNetwork` from your junctions and segments. Keep the same
invariants the constructor enforces: unique ids, positive length and
capacity, condition in 0–100, non-negative traffic, risk in 0–1. The
planner and simulator only depend on those fields.

```python
from road_agents.network import Junction, RoadNetwork, Segment

network = RoadNetwork(
    [Junction("A", "North"), Junction("B", "South")],
    [Segment("S1", "A", "B", 3.0, 1200, 70, 800, 0.2)],
)
```

## 2. Run the cycle

```python
from road_agents.agents import run_cycle
from road_agents.gates import AuditLog

result = run_cycle(network, closure_segment="S1", audit_log=AuditLog())
print(result.alerts, result.ranking)
```

`run_cycle` is advisory only. It never issues a closure recommendation.

## 3. Gate any closure decision

```python
import time
from road_agents.gates import Approval, ClosureGate

approval = Approval(
    approver="Named Person", role="senior", scope_segment="S1",
    expires_at=time.time() + 3600, consent_text="yes, approved",
)
rec = ClosureGate().issue("S1", impact.confidence,
                          impact.total_added_minutes, approval)
assert rec.status == "issued"  # or "blocked" with a reason
```

Treat `role="senior"` as required whenever `impact.confidence < 0.6`
(stranded routes or overloaded alternates). Reuse the same approval
object twice and the second issue is blocked — that is the single-use
rule working as designed.

## 4. Redact before logging

Pass any free-text note (crew reports, public feedback) through
`redact()` before it reaches the audit log. It removes phone numbers,
SSNs, card numbers, and email addresses. Verify with the redaction tests
before changing the patterns.

## 5. Seal the audit log

Call `log.seal()` at the end of a cycle and store the seal separately
from the log. Later, `log.verify(seal)` returns `False` if any entry was
edited or if entries were removed from the end.

## 6. Recalibrate before real use

The score weights (0.5 / 0.3 / 0.2), the condition alert threshold (50),
and the cost model (12,000 per km scaled by condition deficit) are demo
values. Recalibrate them against your own maintenance history, and
replace the congestion approximation with a real traffic model, before
using any output operationally.
