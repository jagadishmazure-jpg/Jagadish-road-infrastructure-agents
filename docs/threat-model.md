# Threat model

Scope: a local planning demo over synthetic data. There is no network
service, no user account, and no real-world actuation — but the controls
are designed as if the recommendations mattered, because the pattern is
the point.

## STRIDE

- **Spoofing.** An unnamed or forged approver could issue a closure.
  Mitigation: approvals require a named approver; anonymous approvals
  are invalid (tested).
- **Tampering.** Audit entries could be edited or trimmed to hide a
  blocked recommendation. Mitigation: hash chain plus seal; edits,
  sequence changes, and tail truncation are all detected (tested).
- **Repudiation.** An issued recommendation could be denied later.
  Mitigation: the approval object, its scope, and the audit entry record
  who approved what, and single-use prevents replay.
- **Information disclosure.** Free-text notes may carry PII (phone, SSN,
  card, email). Mitigation: `redact()` before logging (tested for all
  four categories).
- **Denial of service.** Not applicable to a local library; a malformed
  network raises `ValueError`/`KeyError` instead of hanging (invalid
  inputs are tested).
- **Elevation of privilege.** A regular operator could approve a
  low-confidence closure. Mitigation: confidence below 0.6 requires a
  senior approver (tested).

## Misuse cases

- **Ambiguous consent treated as approval.** A message like "yes, wait,
  no" must never count as yes. Mitigation: consent parsing returns
  "ambiguous" for self-contradicting text (tested).
- **Budget manipulation.** A negative budget could be read as unlimited
  or as zero spending. Mitigation: negative budgets raise (tested).
- **Real operator names leaking in.** Copying a real authority's name
  into docs or data would imply affiliation. Mitigation: hashed brand
  blocklist, non-empty by test; all names in the repo are fictional and
  the README carries an unaffiliated disclaimer.

## Out of scope

Real traffic data, real closures, live map imports, and model-based
agents are all out of scope for this scaffold and listed as Planned in
the README.
