# Knowledge notes — road infrastructure agents

Distilled design notes, written in original prose. All examples use the
fictional Mossmere Highways operator and the synthetic demo network
(6 junctions, 8 segments). No source text is copied here.

## The network model

Nodes are junctions; edges are road segments carrying length, hourly
capacity, a 0–100 condition score, daily traffic, and a 0–1 risk factor.
The model is deliberately small: it exists to make agent decisions
checkable, not to resemble a real road map. "Open-map-style" here means
only the shape of the data (nodes and edges with attributes), not any
imported map dataset — no real map data is used anywhere in this repo.

## Why ranking needs three inputs, not one

Condition alone would send crews to quiet, low-risk segments while busy
arteries deteriorate. Traffic load alone would ignore segments that are
already failing. Risk alone would chase rare events. The planner's score
weights condition deficit most (0.5), then load (0.3), then risk (0.2),
so the top of the ranking is a segment that is simultaneously worn, busy,
and exposed. On the demo network that is S5 (condition 24, load 0.94,
risk 0.6, score 0.689).

## Closure simulation as response planning

Closing a segment does not just remove one road: it reroutes every
origin–destination pair whose shortest path used it. The simulator
recomputes all pairs, so the impact statement covers affected routes,
added minutes, and which alternates tip over capacity. A closure whose
alternates overload gets low confidence (0.55 on the demo S2 closure),
which is exactly the case the human gate treats as needing a senior
approver. A closure that strands routes entirely scores 0.3.

## The gate is the safety story

The simulation is advisory; the gate is the control. Four properties
make it trustworthy in tests: approvals name a person, work once, apply
to one segment, and expire. Consent language is parsed, not assumed:
a message that both agrees and reverses ("yes, wait, no") is ambiguous
and blocks issuance, as does silence (no approval object at all).

## Audit as evidence

A hash chain makes each entry commit to the previous one, so editing an
old entry breaks verification. The seal goes one step further: it commits
to the entry count and the final hash, so quietly deleting entries from
the end is also detected. This matters because a log that can be trimmed
without detection is not evidence.

## Measurement closes the loop

Each cycle ends with a snapshot: average condition, segments below the
alert threshold, overloaded segments, total length. Governance is not a
separate report; it is the same numbers the agents already computed,
recorded in the same audit trail.
