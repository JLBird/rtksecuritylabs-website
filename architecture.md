# RTK-1 Architecture

## Vision

"For your exact model/agent we tested X vectors using Y workflow —
we achieved Z outcomes you care about, and here is proof it's improving week over week."

## System Flow

┌─────────────────────────────────────────────────────────────────────┐
│                        CUSTOMER ENTRY POINTS                        │
│                                                                     │
│   API Request          Streamlit Portal       CI/CD Webhook         │
│   (FastAPI /docs)      (Self-service UI)      (GitHub Actions)      │
└────────────────────────────┬────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────────┐
│                   FASTAPI ROUTER (thin layer)                       │
│                  app/api/v1/redteam.py                              │
│                                                                     │
│   POST /redteam/crescendo-with-report                               │
│   POST /redteam/ci          GET /redteam/trend/{model}              │
│   GET  /redteam/history     GET /health                             │
└────────────────────────────┬────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────────┐
│              LANGGRAPH ORCHESTRATOR (stateful workflow)             │
│             app/orchestrator/claude_orchestrator.py                 │
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐ │
│   │  Supervisor  │───▶│  Run Attack  │───▶│   Report Generator   │ │
│   │     Node     │◀───│     Node     │    │        Node          │ │
│   │  (decides    │    │ (calls RTK   │    │ (compliance-mapped    │ │
│   │  next action)│    │   Facade)    │    │   PDF + metrics)     │ │
│   └──────────────┘    └──────────────┘    └──────────────────────┘ │
│                                                                     │
│   State: RedTeamState (Pydantic, immutable, checkpointable)         │
│   Checkpoint: SqliteSaver → rtk1_checkpoints.db                    │
└────────────────────────────┬────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────────┐
│                      RTK FACADE (swappable)                         │
│                        app/facade.py                                │
│                                                                     │
│   Single entry point for all attack orchestration.                  │
│   Hides all provider complexity. Returns only domain models.        │
│                                                                     │
│   Step 1: ScorerGenerator                                           │
│           Derives customer-defined true/false scoring question      │
│           from EngagementConfig.success_criteria                    │
│                                                                     │
│   Step 2: AttackProvider (runtime-injected, swappable)              │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  PyRITProvider    GarakProvider    DeepTeamProvider          │   │
│   │  (active)         (Tuesday)        (Tuesday)                 │   │
│   │                                                              │   │
│   │  promptfooProvider   MultimodalProvider   RAGProvider        │   │
│   │  (Tuesday)           (roadmap)            (roadmap)          │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   Step 3: Returns OrchestratorResult (domain model)                 │
│           No raw provider objects cross this boundary               │
└────────────────────────────┬────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────────┐
│                     DOMAIN MODEL BOUNDARY                           │
│                    app/domain/models.py                             │
│                                                                     │
│   AttackResult        OrchestratorResult      CampaignConfig        │
│   ScorerConfig        EngagementConfig        AttackVector          │
│                                                                     │
│   ⚠️  Business logic NEVER touches raw provider responses.          │
│   All provider output is immediately converted to domain objects.   │
└────────────────────────────┬────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────────┐
│                      CORE SERVICES (always-on)                      │
│                          app/core/                                  │
│                                                                     │
│   AuditTrail            — Every event logged, immutable append-only │
│   CampaignHistory       — ASR trends, week-over-week delta          │
│   BehavioralFingerprint — Regression detection on fine-tune deploy  │
│   SemanticDriftMonitor  — Verbosity, refusal rate, hedge tracking   │
│   MutationEngine        — Auto-generates jailbreak variants         │
│   DeterministicScorer   — Rule-based ground truth (fires first)     │
│   MultiJudgeConsensus   — 3-judge LLM voting, HITL on low confidence│
│   AlertManager          — Slack webhook on ASR spike                │
│   RegulatoryTracker     — EU AI Act / NIST / OWASP update flags     │
│   CampaignScheduler     — 24/7 autonomous campaign runner           │
│   Settings              — Single source of truth for all config     │
│   StructuredLogging     — JSON output → ELK / Loki ready            │
└────────────────────────────┬────────────────────────────────────────┘
↓
┌─────────────────────────────────────────────────────────────────────┐
│                         DELIVERY LAYER                              │
│                                                                     │
│   PDF Report            WeasyPrint — compliance-mapped, branded     │
│   Grafana Dashboard     Prometheus metrics, ASR trend panels        │
│   PR Comment            GitHub Actions — ASR on every pull request  │
│   Slack Alert           Webhook — ASR spike, campaign complete      │
│   Executive Email       Auto-scheduled weekly/monthly               │
│   JSON Logs             Raw audit trail for legal/compliance        │
│   Streamlit Portal      Self-service UI for customers               │
└─────────────────────────────────────────────────────────────────────┘

---

## Domain Model Boundary Rule

Provider Layer          Domain Boundary              Orchestration Layer
─────────────────       ───────────────              ───────────────────
PyRIT result      ──▶   AttackResult          ──▶   Supervisor
Garak result      ──▶   AttackResult          ──▶   Report Generator
Deepteam result   ──▶   AttackResult          ──▶   History Store
Raw dict          ✗      Never crosses          ✗   Never seen above facade

---

## Configuration: Single Source of Truth

.env (root)
└── app/core/config.py (Settings — Pydantic BaseSettings)
└── imported by every module that needs configuration
No hardcoded values anywhere else in the codebase

---

## Attack Provider Interface

```python
# Every provider implements exactly this interface
class AttackProvider(ABC):
    async def run_campaign(
        self,
        config: CampaignConfig,
        scorer_config: ScorerConfig,
    ) -> List[AttackResult]: ...

    def is_available(self) -> bool: ...

    @property
    def tool_name(self) -> str: ...
```

---

## Compliance Coverage

Framework          Articles / Functions          RTK-1 Evidence Generated
─────────────────  ────────────────────          ────────────────────────────
EU AI Act          Article 9                     Attack plan + execution logs
EU AI Act          Article 15                    Quantified ASR metric
EU AI Act          Annex IV                      Full campaign records (PDF)
EU AI Act          Article 72                    Continuous monitoring proof
NIST AI RMF        GOVERN 1.2                    Engagement scope + RoE
NIST AI RMF        MAP 5.1                       Risk scoping document
NIST AI RMF        MEASURE 2.7                   Adversarial test results
NIST AI RMF        MANAGE 4.1                    Residual risk documentation
OWASP LLM Top 10   LLM01 Prompt Injection        Crescendo multi-turn results
OWASP LLM Top 10   LLM02 Output Handling         RAG injection results
OWASP LLM Top 10   LLM06 Data Disclosure         Exfiltration probe results
OWASP LLM Top 10   LLM08 Excessive Agency        Tool abuse probe results
MITRE ATLAS        AML.T0054 Multi-Turn          Crescendo sequences
MITRE ATLAS        AML.T0051 Jailbreak           Jailbreak variant results
MITRE ATLAS        AML.T0043 Adversarial Data    Mutation engine output

---

## CI/CD Integration

Git Push / PR Merge / Nightly Schedule
↓
.github/workflows/redteam.yml
↓
POST /api/v1/redteam/ci
↓
┌───────────────────────────────┐
│  ASR < threshold?             │
│  YES → ✅ PR passes           │
│  NO  → ❌ PR blocked          │
│        Slack alert sent       │
│        Report uploaded        │
└───────────────────────────────┘
↓
PR Comment posted with:

ASR %
Job ID
Report link
Pass / Fail status

---

## Always-On Defense Schedule

Every git push     → Lightweight CI campaign (3 sequences)
Every PR merge     → Full CI campaign (configurable sequences)
Nightly 2am UTC    → Scheduled autonomous campaign
Weekly Sunday      → PDF report auto-generated + emailed
Monthly 1st        → Executive dashboard email + trend summary
On ASR spike       → Immediate Slack alert + HITL flag
On fingerprint Δ   → Regression campaign auto-triggered

---

## File Structure

app/
├── api/
│   └── v1/
│       └── redteam.py          # Thin FastAPI router
├── core/
│   ├── config.py               # Single source of truth
│   ├── logging.py              # Structured JSON logging
│   ├── audit.py                # Immutable audit trail
│   ├── history.py              # Campaign history + ASR trends
│   ├── alerts.py               # Slack alerting
│   ├── scheduler.py            # 24/7 autonomous runner
│   ├── mutation.py             # Jailbreak mutation engine
│   ├── scoring.py              # Deterministic + multi-judge scorer
│   ├── fingerprint.py          # Behavioral fingerprinting
│   ├── semantic_drift.py       # Drift monitoring
│   ├── regulatory.py           # EU AI Act / NIST tracker
│   └── metrics.py              # Prometheus counters
├── domain/
│   ├── models.py               # AttackResult, OrchestratorResult
│   └── engagement.py           # EngagementConfig, SuccessCriteria
├── orchestrator/
│   └── claude_orchestrator.py  # LangGraph workflow
├── providers/
│   ├── base.py                 # AttackProvider interface
│   ├── pyrit_provider.py       # PyRIT 0.12.0 implementation
│   └── scorer_generator.py     # Customer-defined scorer
├── facade.py                   # RTKFacade — single entry point
├── schemas.py                  # API request/response models
├── pyrit_langchain_target.py   # LangChain bridge for PyRIT
└── main.py                     # FastAPI app (minimal)
.github/
└── workflows/
└── redteam.yml             # CI/CD pipeline
docs/
└── architecture.md             # This file

---

## Business Value Statement

"You defined success as [customer_success_metrics].
RTK-1 tested [total_sequences] attack sequences against [target_model]
using Crescendo multi-turn escalation orchestrated by Claude Sonnet 4.6

LangGraph stateful checkpoints + FastAPI production backend.

Attack Success Rate: [asr]% ([robustness_rating])
Week-over-week change: [delta]% ([framing])
A single breach of this type could cost $5M+ in regulatory fines
and customer loss. This engagement reduced that exposure by [pct_change]%.
Evidence package: PDF report + JSON audit logs + Grafana dashboard
Compliance coverage: EU AI Act Articles 9, 15, Annex IV | NIST MEASURE 2.7
OWASP LLM01-LLM08 | MITRE ATLAS AML.T0054"

---

## Objective Completion Status

See `OBJECTIVES.md` for the full list of 66 objectives and current status.

---

*RTK-1 v0.3.0 — Claude Sonnet 4.6 + LangGraph + PyRIT 0.12.0*
*Architecture last updated: 2026-04-05*
