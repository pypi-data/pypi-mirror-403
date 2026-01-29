# MK10-PRO v1.0 — Deterministic Pre‑Delivery Truth Infrastructure

> **STATUS:** FINAL / AUTHORITATIVE / CLOSED / FINISHABLE
>
> **SCOPE (HARD BOUNDARY):** Pre‑delivery truth only. Formal playability under declared specifications. No cinema playback. No devices. No operators. No trust. No exceptions.

---

## EXECUTIVE DEFINITION (NON‑MARKETING)

**MK10‑PRO is deterministic audiovisual infrastructure that converts mastering into provable, durable facts instead of trusted outputs.**

If a claim cannot be proven — how a master was produced, what transformed it, which rules governed it, who approved its promotion, or whether it is *formally playable under a declared specification* — MK10‑PRO treats that claim as invalid.

This is not a tool. It is infrastructure.

---

## SYSTEM AXIOMS (IMMUTABLE)

1. **Truth is executable** — claims emerge only from execution.
2. **Evidence is the product** — files are inputs, not outcomes.
3. **Policy is law** — configuration cannot override rules.
4. **Verification is hostile** — no engine, no trust, no authority required.
5. **Determinism is mandatory** — same inputs must yield identical outputs.
6. **Scope ends before institutions** — hardware, venues, operators are out of bounds.

If any axiom is violated, MK10‑PRO is invalid by definition.

---

## QUICK START

```bash
# Install dependencies
pip install -r requirements.txt
# OR
make install

# Ingest source assets
mk10 ingest --source /path/to/assets

# Execute mastering pipeline
mk10 execute --dag pipeline.yaml

# Promote to release
mk10 promote --title "MyTitle" --version "v1.0" --state RELEASE

# Verify an MTB
mk10 verify --mtb /path/to/mtb.zip
```

### Runtime Dependencies

**Required:**
- `pyyaml>=6.0` — YAML parsing (policy rules, config)
- `jsonschema>=4.0` — JSON schema validation (MTB, evidence, ingest)
- `click>=8.0` — CLI framework
- `cryptography>=41.0` — Cryptographic operations
- `pycryptodome>=3.19.0` — Additional crypto support

**Full list:** See `requirements.txt`

---

## THE ACTUAL PRODUCT: MASTER TRUTH BUNDLE (MTB)

Files are not the product.

The **Master Truth Bundle (MTB)** is the product.

An MTB is a sealed, self‑contained, verifiable object that represents a title/version as fact.

If the MTB validates, the title exists.
If it does not, the title is not real.

---

## GOVERNING PROMISE — "NO FILE FALLS AGAIN"

A master is considered safe only if it can always:

1. Be located
2. Be verified
3. Be explained
4. Be reproduced
5. Be proven formally playable under its specification
6. Be re‑delivered without ambiguity

If any condition fails, MK10‑PRO refuses the claim.

---

## LICENSE

See LICENSE file for details.

---

## FINAL AUTHORITY STATEMENT

If MK10‑PRO says a title exists, it exists.
If MK10‑PRO refuses a claim, the claim is invalid.

There is no appeal to trust.
There is only proof.

