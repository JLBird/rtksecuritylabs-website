#!/usr/bin/env python3
"""
Standalone verifier for RTK-1 signed evidence envelopes (v0.7.0).

This script confirms two things about an RTK-1 evidence envelope, using ONLY
public libraries and RTK Security Labs' published public key. It does not import
or require any RTK-1 source code, and it does not contact RTK-1 at verification
time beyond fetching the published public key.

    1. SIGNATURE: the ECDSA P-256 signature is valid for the canonical hash,
       against the published public key.
    2. HASH INTEGRITY: the canonical_hash in the envelope actually matches the
       envelope's own body (recomputed via RFC 8785 JCS + SHA-256), proving the
       body was not altered after signing.

Verification procedure (RTK-1/SEILX Integration Spec):
    - Exclude the `signature` and `canonical_hash` fields from the body.
    - Canonicalize the remaining body with RFC 8785 (JCS).
    - SHA-256 the canonical bytes -> 64-char lowercase hex digest.
    - The signature is an ECDSA P-256 signature computed over the ASCII bytes of
      that hex string (the hash is signed as text, with SHA-256 applied by the
      signing primitive). Verify accordingly.

Dependencies (install with pip):
    pip install rfc8785 cryptography

Usage:
    python verify_rtk1.py <path-to-envelope.json>

Public key (trust anchor), fetched at runtime:
    https://rtksecuritylabs.com/keys/rtk-key-2026-01.pem
"""

import base64
import hashlib
import json
import sys
import urllib.request

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_public_key

PUBLIC_KEY_URL = "https://rtksecuritylabs.com/keys/rtk-key-2026-01.pem"
EXCLUDED_FIELDS = ("signature", "canonical_hash")


def fetch_public_key():
    """Fetch RTK Security Labs' published P-256 public key."""
    with urllib.request.urlopen(PUBLIC_KEY_URL, timeout=30) as resp:
        pem_bytes = resp.read()
    key = load_pem_public_key(pem_bytes)
    if not isinstance(key, ec.EllipticCurvePublicKey):
        raise ValueError("Published key is not an EC public key.")
    return key


def recompute_canonical_hash(envelope: dict) -> str:
    """SHA-256 over RFC 8785 JCS canonical bytes of the body (excluding
    signature and canonical_hash)."""
    body = {k: v for k, v in envelope.items() if k not in EXCLUDED_FIELDS}
    canonical_bytes = rfc8785.dumps(body)
    return hashlib.sha256(canonical_bytes).hexdigest()


def verify_signature(public_key, canonical_hash_hex: str, signature_b64: str) -> bool:
    """Verify the ECDSA P-256 signature over the ASCII bytes of the hash hex."""
    try:
        signature_der = base64.b64decode(signature_b64)
        public_key.verify(
            signature_der,
            canonical_hash_hex.encode("ascii"),
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except (InvalidSignature, ValueError):
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python verify_rtk1.py <path-to-envelope.json>")
        sys.exit(2)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        envelope = json.load(f)

    stored_hash = envelope.get("canonical_hash", "")
    signature_b64 = envelope.get("signature", "")

    print(f"Envelope:        {path}")
    print(f"Evidence ID:     {envelope.get('evidence_id', '(none)')}")
    print(f"Verdict:         {envelope.get('verdict', '(none)')}")
    print(f"Signing key ID:  {envelope.get('signing_key_id', '(none)')}")
    print(f"Public key URL:  {PUBLIC_KEY_URL}")
    print()

    # 1. Hash integrity — does the stored hash match the body?
    recomputed = recompute_canonical_hash(envelope)
    hash_ok = recomputed == stored_hash
    print(f"Stored hash:     {stored_hash}")
    print(f"Recomputed hash: {recomputed}")
    print(f"HASH INTEGRITY:  {'PASS' if hash_ok else 'FAIL'}")
    print()

    # 2. Signature — is the signature valid for that hash, against the
    #    published key?
    public_key = fetch_public_key()
    sig_ok = verify_signature(public_key, stored_hash, signature_b64)
    print(f"SIGNATURE:       {'PASS' if sig_ok else 'FAIL'}")
    print()

    if hash_ok and sig_ok:
        print("RESULT: VERIFIED — signature valid against the published key, and")
        print("        the canonical hash matches the envelope body. The verdict")
        print("        and coverage declaration in this envelope are authentic and")
        print("        unaltered since signing.")
        sys.exit(0)
    else:
        print("RESULT: NOT VERIFIED — do not rely on this envelope.")
        sys.exit(1)


if __name__ == "__main__":
    main()
