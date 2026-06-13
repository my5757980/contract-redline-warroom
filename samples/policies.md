# Compliance Policy Library (demo)

The Compliance agent checks inbound contracts against these enterprise policies.

- **P1 — Data Processing Agreement required.** Any clause permitting the counterparty
  to process Personal Data MUST be backed by a signed DPA. Absence ⇒ **FAIL + VETO**;
  required addendum: "GDPR DPA".
- **P2 — Data residency.** Personal Data must be confined to approved regions
  (EU/US). "any region at Provider's discretion" ⇒ required addendum:
  "EU data-residency rider".
- **P3 — Liability cap.** Uncapped liability or full consequential damages is a
  high-risk policy breach (escalate to Risk; not an automatic veto).
- **P4 — Security addendum.** Cloud processing of regulated data requires a security
  addendum (SOC 2 / ISO 27001 attestation).
