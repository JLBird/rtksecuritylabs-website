# Reproducibility and Determinism

RTK-1 evidence is engineered to be **independently verifiable, deterministic, and reproducible** by third parties without trust in RTK-1's infrastructure.

This document describes the deterministic chain that supports this property, and the boundaries within which it holds.

---

## The Deterministic Chain

```
evidence_object → RFC 8785 canonicalization → SHA-256 → signing → signed_evidence
```

Three primitives compose to make this chain deterministic:

### 1. RFC 8785 — JSON Canonicalization Scheme

RTK-1 serializes evidence using [RFC 8785 JCS](https://datatracker.ietf.org/doc/html/rfc8785), the IETF standard for deterministic JSON serialization:

- Object keys sorted lexicographically (UTF-16 code-unit order)
- No insignificant whitespace
- Number serialization per ECMA-262
- UTF-8 encoding throughout

The same evidence object always produces the same canonical bytes. Any deviation in serialization (key order, whitespace, number formatting, escape sequences) is excluded by the standard.

### 2. SHA-256

The canonical bytes are hashed with SHA-256 ([FIPS 180-4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)) — a NIST-approved cryptographic hash function. Anyone receiving the evidence can independently recompute the hash and compare against the claimed `canonical_hash` field.

### 3. Version Pinning

Every signed evidence object carries explicit version identifiers:

- `evidence_version` — the schema version (currently `1.0`)
- `rtk1_version` — the RTK-1 platform version that produced the evidence
- `attack_providers[].provider_version` — each adversarial provider's version

Re-running RTK-1 with the same versions against the same system in the same configuration produces equivalent evidence under the reproducibility scope below.

---

## Reproducibility Scope

The reproducibility guarantee **covers**:

- ✅ Canonical bytes from any conforming serializer
- ✅ Canonical hash from any conforming SHA-256 implementation
- ✅ Signature verification against published public keys
- ✅ Schema validation against the published Pydantic models / JSON Schema

The reproducibility guarantee **does not** cover:

- ❌ Identical adversarial outcomes from non-deterministic AI systems under test (the SUT may produce different outputs on different runs by its own nature)
- ❌ Stable verdicts across RTK-1 version changes (provider behavior may evolve)

This boundary is structural, not a limitation: it reflects honestly what RTK-1 evidence claims. A verdict represents observation under specified adversarial pressure at a bound moment, with explicit version identification — not a claim about underlying system determinism.

---

## Independent Verification

Anyone can verify an RTK-1 signed evidence object using the procedure in [Integration Spec §4.3](../specs/01_RTK1_SEILX_Integration_Spec_v1_0.pdf):

1. Extract the evidence object
2. Remove `signature` and `canonical_hash` fields
3. Apply RFC 8785 canonicalization
4. Compute SHA-256 over the canonical bytes
5. Compare against the received `canonical_hash`
6. Validate `signature.signature_value` against the canonical hash using RTK-1's published public key for `signature.signing_key_id`

A reference CLI (`verify_evidence.py`) is provided in this repository for this purpose. No RTK-1 infrastructure is required.

---

## Public Key Publication

RTK-1 publishes its signing keys at versioned URLs:

```
https://rtksecuritylabs.com/keys/{signing_key_id}.pem
```

Public keys remain published for the full v1.0 backward-compatibility window (12 months, renewable; see Integration Spec §7.2). Verification of historical evidence remains possible after key rotation.

---

## Why This Matters

Independent verifiability is what makes adversarial evidence audit-grade. A claim that cannot be independently checked is not evidence; it is assertion.

The composed properties of RFC 8785 canonicalization + SHA-256 + version pinning + published public keys produce a chain where:

- The signature can be falsified or verified by any third party
- The canonical hash can be recomputed by any conforming implementation
- The originating versions are explicit and citable
- The verification procedure is published, not proprietary

This is the architectural primitive that supports procurement-grade use, regulatory submission, audit defense, and peer review.

---

*RTK Security Labs · `ramon@rtksecuritylabs.com`*
*Methodologies protected as trade secrets under DTSA (18 U.S.C. § 1836) and TX UTSA (§ 134A). Verification procedure and evidence schema are public.*
