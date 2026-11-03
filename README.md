# Jagadish-road-infrastructure-agents

**Recruiter summary.** A multi-agent planning system over a synthetic road
network: one agent ranks road segments for maintenance by condition, traffic
load, and risk; a second simulates a segment closure (affected routes, added
travel time, overloaded alternates); and a human gate must approve any
closure recommendation before it is issued. Proof: **70 tests pass** from a
fresh local run (Python 3.12, pytest 9.1.1, standard library only).

> **Disclaimer.** This is an independent learning and demonstration project.
> It is not affiliated with, endorsed by, or connected to any real road
> operator, highway authority, or company. Every operator name, place label,
> and number in this repo is fictional or synthetic. Nothing here issues,
> approves, or models a real road closure.

## Why this is not energy-grid work

This repo is deliberately distinct from energy-grid graph work: the network
is roads, not power lines; the nodes are junctions, not substations; the
decisions are maintenance ranking and closure/detour planning, not load
balancing or outage restoration; and the metrics are condition scores,
travel-time minutes, and alternate-route overload, not megawatts, voltage,
or grid frequency. No energy-domain concept is reused here.

## The fictional operator

The demo network belongs to **Mossmere Highways**, a fictional regional
roads operator invented for this repo. Name check, 2026-11-03: the
provisional name for this operator was dropped because a web search
found a real, active UK company sharing its stem name (financial
management, an unrelated sector). A further search for "Mossmere" found only a
dissolved, dormant company sharing that stem (also unrelated to roads)
and no roads or highways operator of that name. Mossmere Highways is
presented throughout as fictional and unaffiliated.

## How it works

```
detect (condition alerts) -> triage (ranked maintenance)
  -> respond (closure simulation, human-gated)
  -> recover (reopening checklist) -> measure (network metrics)
```

1. **Detection.** `MaintenancePlannerAgent.detect` flags segments at or
   below condition 50.
2. **Triage.** `MaintenancePlannerAgent.rank` scores each segment as
   `0.5 * condition deficit + 0.3 * load share + 0.2 * risk`.
   `plan_within_budget` walks the ranking until the budget is spent;
   negative budgets are rejected, never clamped.
3. **Response.** `DetourSimulatorAgent.simulate_closure` recomputes every
   shortest path without the closed segment and reports affected routes,
   added minutes, and alternates pushed over capacity.
4. **Human gate.** `ClosureGate.issue` is the only path that issues a
   closure recommendation. Approval must be named-person, single-use,
   scoped to the segment, unexpired, and clearly consented. Low-confidence
   recommendations (stranded routes or overloaded alternates) need a
   senior approver. Ambiguous consent ("yes, wait, no") is rejected.
5. **Recovery.** `RecoveryChecklist` blocks reopening until surface,
   signage, and traffic-count steps all pass.
6. **Governance and measurement.** Every cycle step is appended to a
   hash-chained `AuditLog`; `seal()` lets later verification detect even
   tail truncation. `measure()` reports average condition, alert counts,
   overload counts, and total length.

## Real output (from the demo, asserted by tests)

```
$ python3 src/road_agents/demo.py
Top maintenance priority: S5 score=0.689
Top 3: S5, S2, S7
Segments below condition alert: 3
Average condition: 56.1
Total network length (km): 46.2
Closure S2 affected routes: 6
Closure S2 stranded routes: 0
Closure S2 total added minutes: 37.8
Closure S2 confidence: 0.55
Closure S2 overloaded alternates: ['S3', 'S4', 'S1']
Pipeline audit entries: ['cycle.detect', 'cycle.triage', 'cycle.simulate_closure']
```

Because the S2 closure's confidence is 0.55 (below the 0.6 low-confidence
threshold), issuing its recommendation requires a senior approver — that
rule is tested in `tests/test_gates.py`.

## How to run

```bash
python3 -m pytest tests/          # full suite (70 tests, stdlib only)
python3 src/road_agents/demo.py   # demo numbers above
python3 scripts/count_tests.py    # prints the test total from a real run
```

No installation, no network access, no virtual environment. Python 3.11+
and pytest are the only requirements.

## Guardrails and security controls

- **PII redaction** (`redaction.redact`): phone numbers, SSNs, card
  numbers, and email addresses are replaced before any note is logged.
- **Confirmation gates**: bypass (no approval object), reject (expired,
  anonymous, wrong-scope, reused, ambiguous-consent), and absent-path
  cases are all tested, plus low-confidence and self-contradicting-consent
  ("yes, wait, no") cases.
- **Approvals**: named-person, single-use, scoped, expiring.
- **Budgets**: negative cost/budget inputs raise `ValueError`.
- **Brand check**: `brand_blocklist.json` stores SHA-256 hashes only, never
  plain names; `scan_for_blocked_names` flags text matching a blocked
  hash. A test asserts the blocklist is non-empty.
- **Audit**: hash-chained entries; tampering, sequence mismatch, and
  seal-verified tail truncation are all detected (tested).

## Limitations and known failures

- Travel time is a simple length/speed/congestion approximation, not a
  traffic-engineering model; it ignores signals, time of day, and vehicle
  mix.
- Overload figures are a conservative upper bound: each affected route
  pair is assumed to carry the closed segment's full daily traffic onto
  its alternate, so utilisation numbers after diversion can exceed what
  real reassignment would produce.
- The demo network is 6 junctions and 8 segments; results do not
  generalise to a real road network.
- The agents are deterministic planners, not LLM agents; there is no
  model call, no live map data, and no deployment.

## Built / Written-not-run / Planned

| Item | Status |
|---|---|
| Road graph + Dijkstra routing | Built, tested |
| MaintenancePlannerAgent (rank, budget) | Built, tested |
| DetourSimulatorAgent (closure simulation) | Built, tested |
| Human gate + approvals + consent parsing | Built, tested |
| Hash-chained audit log with seal | Built, tested |
| PII redaction + hashed brand blocklist | Built, tested |
| Recovery checklist + network metrics | Built, tested |
| CI workflow (`.github/workflows/ci.yml`) | Written, **not run — CI NOT verified** |
| Live map data import | Planned, not built |
| LLM-based agent reasoning | Planned, not built |
| Deployment | Planned, not built |

## Docs

- [knowledge/notes.md](knowledge/notes.md) — distilled design notes
- [knowledge/architecture.md](knowledge/architecture.md) — architecture
  (Mermaid) and decision notes
- [docs/implementation-guide.md](docs/implementation-guide.md) — adopter guide
- [docs/threat-model.md](docs/threat-model.md) — threat model
- [SECURITY.md](SECURITY.md) — reporting and handling

## License

MIT. See [LICENSE](LICENSE).
