# Bilateral Credentials Exchange Procedure

**Purpose:** Operational procedure for exchanging the credentials that govern
the RTK-1 ↔ partner integration channel. Used during pilot kickoff and
ongoing partnership management.

**Authority:** RTK-1/SEILX Integration Spec v1.0 §5.1 (callback authentication)
and §10 open item #3.

---

## Credential Inventory

The integration uses three distinct credential types, each with its own
exchange mechanism and lifecycle:

| Credential | Purpose | Exchange Mechanism | Lifecycle |
|---|---|---|---|
| HMAC shared secret | Authenticates RTK-1 ↔ partner callbacks | Bilateral 1Password shared vault | Rotates every 90 days, or on partnership dissolution |
| RTK-1 public key | Asymmetric verification of evidence signatures | Public publication at `rtksecuritylabs.com/keys/` | Per signing key rotation (no more than every 90 days, per Integration Spec §4.4) |
| Test credentials (system-under-test API keys, etc.) | Single pilot's authorized access to the SUT | Encrypted Signal exchange | One-shot — deleted/rotated within 14 days of pilot close |

---

## 1. HMAC Shared Secret Exchange — Bilateral 1Password Shared Vault

**When:** Bilateral partnership initiation (e.g., before SEILX pilot kickoff)
and on rotation cadence (every 90 days).

**Procedure:**

1. RTK-1 creates a 1Password shared vault titled `RTK1-{Partner}-Integration`
   (e.g., `RTK1-SEILX-Integration`)
2. Both parties' principal accounts are added with edit permissions
3. RTK-1 generates a 32-byte HMAC secret using a cryptographically secure
   source. From PowerShell with the venv_rtk active:

    ```powershell
    python -c "import secrets; print(secrets.token_hex(32))"
    ```

4. RTK-1 adds the secret to the vault as a "Secure Note" titled:
   `HMAC Secret v1 (active from YYYY-MM-DD)`
5. Partner acknowledges receipt and applies the secret on their side
6. Both parties confirm the secret is loaded into their respective environment
   variable (e.g., `RTK1_PARTNER_HMAC_SECRET`) without committing to any Git
   repo or plain-text file

**Rotation:**

- New secret generated 7 days before old secret expires
- Both parties run in dual-secret mode for the overlap window (accept either)
- Old secret retired after partner confirms successful use of new secret

**Dissolution:**

- On partnership dissolution, both parties revoke vault access within 24 hours
- Old secret is deleted from the vault and from all environments

---

## 2. Test Credentials Exchange — Encrypted Signal (One-Shot Pilot)

**When:** Single pilot engagement requiring shared access to client's
system-under-test (e.g., API keys for the SEILX pilot client's AI system).

**Why Signal and not 1Password:** Pilot test credentials are *single-use,
short-lived, and client-owned*. They should never enter a permanent vault on
either party's side. Signal's disappearing-messages feature provides a clean
delete-after-use property.

**Procedure:**

1. Verify Signal identity out-of-band (e.g., confirm safety number over Zoom
   during pilot kickoff call)
2. Create a Signal chat with disappearing messages set to 24 hours
3. Sender pastes the test credential block into the chat. Recommended format:

    ```
    System: {client-name} {sut-name} {sut-version}
    Endpoint: {url}
    API Key: {key}
    Authorized Until: {ISO-8601 timestamp}
    Notes: {scope of authorized adversarial testing}
    ```

4. Recipient acknowledges by replying with the SHA-256 hash of the credential
   block (out of caution — confirms received without re-transmitting plaintext)
5. Recipient loads credentials into environment-isolated test runner
   (NOT committed to any repo, NOT entered into 1Password)
6. Within 14 days of pilot close: recipient deletes credentials from local
   environment; both parties delete the Signal chat

**Forbidden:**

- Pasting test credentials into Slack, email, or any platform without E2EE
- Storing test credentials in any Git repo, even private
- Reusing test credentials across multiple clients

---

## 3. Public Key Distribution — Public Web Publication

**When:** RTK-1 generates a new signing key (or rotates an existing key).

**Procedure:**

1. RTK-1 generates ECDSA P-256 keypair locally
2. Private key stored in 1Password personal vault (`RTK-1 Signing Key {date} (PRIVATE)`)
3. Public key published at:

    ```
    https://rtksecuritylabs.com/keys/{signing_key_id}.pem
    ```

4. Key rotation announced to active integration partners 30 days in advance
5. Old keys remain published for the v1.0 backward-compatibility window
   (12 months, renewable per Integration Spec §7.2)

**Verification by partners:**

Partners verify evidence signatures by fetching the published public key
matching the `signing_key_id` in the evidence object's `signature` block.
No bilateral exchange of public keys is needed — publication is the
exchange.

---

## Operational Checklist for SEILX Pilot Kickoff

Pre-kickoff (Daniel and Ramon, before pilot day 1):

- [ ] 1Password shared vault `RTK1-SEILX-Integration` created and shared
- [ ] HMAC secret v1 generated, vault-stored, applied on both sides
- [ ] Both parties confirm secret loaded via environment variable
- [ ] Signal safety number verified between Daniel and Ramon
- [ ] Disappearing-messages enabled on the bilateral Signal chat
- [ ] Public key for v0.6 signing key generated and published at
      `rtksecuritylabs.com/keys/rtk-key-2026-01.pem`

Pilot day 1 (client onboarded):

- [ ] Pilot client confirms scope of authorized adversarial testing
- [ ] Client provides test credentials via SEILX's preferred secure channel
      to SEILX
- [ ] SEILX forwards relevant test credentials to RTK-1 via the bilateral
      Signal chat
- [ ] RTK-1 acknowledges receipt with SHA-256 hash confirmation
- [ ] RTK-1 loads credentials into isolated test runner

Pilot close (within 14 days post-completion):

- [ ] All test credentials deleted from RTK-1 local environments
- [ ] Signal chat deleted by both parties
- [ ] Joint pilot review document signed
- [ ] Verifier letter received (per Integration Spec §6.5.3)
- [ ] Go/no-go decision on Mode B activation
- [ ] HMAC secret either retained (if partnership continues) or rotated
      and old secret revoked (if pilot was no-go)

---

*RTK Security Labs · ramon@rtksecuritylabs.com — Bilateral procedure document, confidential to RTK-1 and active integration partners.*
