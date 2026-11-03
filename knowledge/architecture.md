# Architecture

## Agent pipeline

```mermaid
flowchart LR
    N[RoadNetwork\njunctions + segments] --> D[Detection\ncondition <= 50]
    D --> T[Triage\nMaintenancePlannerAgent\nrank + budget plan]
    T --> S[Response\nDetourSimulatorAgent\nclosure simulation]
    S --> G{Human gate\nClosureGate}
    G -->|approved| I[Closure recommendation\nissued]
    G -->|blocked| B[Blocked\nreason recorded]
    S --> R[Recovery\nRecoveryChecklist]
    R --> M[Measurement\nnetwork metrics]
    D --> A[AuditLog\nhash-chained + sealed]
    T --> A
    S --> A
    G --> A
```

## Module map

```mermaid
flowchart TB
    subgraph src/road_agents
        NET[network.py\nRoadNetwork, Segment,\nDijkstra routing]
        AG[agents.py\nMaintenancePlannerAgent,\nDetourSimulatorAgent,\nRecoveryChecklist, measure]
        GT[gates.py\nClosureGate, Approval,\nparse_consent, AuditLog]
        RD[redaction.py\nredact, brand blocklist\nSHA-256 hashes only]
        DM[demo.py\nprints asserted numbers]
    end
    NET --> AG
    AG --> GT
    GT --> RD
```

## Decisions

- **Standard library only.** No dependency can break the demo or hide a
  behaviour; every computation is readable in one file.
- **Deterministic agents, no model calls.** Ranking and rerouting are
  arithmetic and shortest-path search, so tests can assert exact numbers
  (S5 first, 37.8 added minutes for the S2 closure).
- **Gate separate from simulation.** The simulator cannot issue anything;
  only `ClosureGate.issue` with a valid `Approval` can, and the pipeline
  function never calls it. This separation is itself a test.
- **Hashes, not names, in the brand blocklist.** The repo guards against
  accidental use of real operator names without containing those names.
- **Seal over the audit log.** A plain hash chain detects edits but not
  trimming; the seal commits to count and tail hash, closing that gap.
