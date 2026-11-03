# Security policy

This is a demonstration project over synthetic data. It has no deployed
service, no user accounts, and no real-world actuation.

## Reporting a vulnerability

If you find a security issue in this repo (for example, a bypass of the
closure gate, a redaction miss, or an audit-log verification hole), please
open a GitHub issue describing the failing case. Do not include any real
personal data in the report.

## What is protected here

- The closure gate: approvals are named-person, single-use, scoped, and
  expiring; low-confidence recommendations need a senior approver.
- PII redaction: phone, SSN, card numbers, and email addresses are
  stripped before logging.
- Audit integrity: hash-chained entries with a seal that detects edits
  and tail truncation.
- Brand hygiene: real operator names are guarded by SHA-256 hash, never
  stored in plain text.

## What is not protected

This repo must not be used to plan real road closures. Its traffic model
is an approximation, its network is fictional, and its outputs are
advisory only.
