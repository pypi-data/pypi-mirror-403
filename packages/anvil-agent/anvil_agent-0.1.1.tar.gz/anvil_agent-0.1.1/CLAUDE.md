# Anvil SDK

## Overview

Anvil SDK is a **JIT (Just-In-Time) Infrastructure & Self-Healing SDK for AI Agents** that solves the "Tool Rot" problem. Instead of hardcoding tool implementations that break when APIs change, Anvil generates tool code on the fly using LLMs.

---

## What We Have: The Execution Engine (Muscle)

### Core Features - BUILT

| Feature | Status | Location |
|---------|--------|----------|
| JIT Code Generation | ✅ Done | `anvil/generators/` |
| Self-Healing | ✅ Done | `anvil/core.py` |
| Credential Resolution | ✅ Done | `anvil/credentials.py` |
| Multi-Provider LLM (Claude, GPT-4, Grok) | ✅ Done | `anvil/llm/` |
| Framework Adapters (LangChain, CrewAI, AutoGen, OpenAI) | ✅ Done | `anvil/adapters/` |
| Sandbox Execution | ✅ Done | `anvil/sandbox.py` |
| Tool Chaining | ✅ Done | `anvil/chain.py` |
| CLI Tools | ✅ Done | `anvil/cli.py` |
| Local Caching | ✅ Done | `./anvil_tools` |

---

## What We Need: The Control Plane (Brain + Report Card)

> **Goal:** Turn from "Developer Tool" → "Infrastructure Platform"
> **Target Customer:** CTOs who need to sleep at night

---

## Enterprise Roadmap

### Phase 1: Anvil Cloud (SaaS Dashboard)

**Priority: HIGH** | Monetization Layer

| Component | Description | Business Value |
|-----------|-------------|----------------|
| **Health Monitor** | Datadog-style dashboard with traffic lights (Green/Yellow/Red) | Real-time visibility into agent fleet |
| **Fix Timeline** | Log showing when tools broke and how Anvil fixed them | Proves ROI: "Saved 40 engineering hours this week" |
| **Remote Config** | Push config updates (rotate API keys) without redeploying | Reduces operational overhead |

**Immediate Action:** Build a "Ghost Dashboard" (React/Next.js mockup with fake data) to sell the vision.

---

### Phase 2: Telemetry Link (The Glue)

**Priority: HIGH** | Connects SDK to Cloud

Update `logger.py` and `core.py` to send events asynchronously:

| Event Type | Payload | Purpose |
|------------|---------|---------|
| **Heartbeats** | Agent ID, timestamp | "I'm alive" monitoring |
| **Incident Reports** | Original error, generated patch, success/fail | Track self-healing effectiveness |
| **Usage Metrics** | Tool calls, latency, token costs | Billing & optimization |

**Schema Needed:** JSON schema for Incident Reports (defines the SaaS API contract)

---

### Phase 3: Enterprise Governance (Permission to Buy)

**Priority: CRITICAL** | Enterprise Sales Blocker

Large companies won't let self-healing code run wild. Need **Policy-as-Code**.

| Feature | Description | Why It Matters |
|---------|-------------|----------------|
| **Human-in-the-Loop Gate** | Pause execution + Slack/Email admin when sensitive imports detected (`os`, `subprocess`) | Compliance requirement |
| **Allowed/Blocked Lists** | Centralized policy for approved libraries | Security control |
| **Secret Redaction** | Auto-strip API keys and PII from cloud-bound logs | Data privacy |

**Blocked Imports Example:**
```python
ALLOWED = ['requests', 'pandas', 'numpy', 'httpx']
BLOCKED = ['socket', 'ftplib', 'subprocess', 'os.system']
```

---

### Phase 4: Private Registry (Internal PyPI)

**Priority: MEDIUM** | Standardization & Reuse

Enterprises want "Golden Tools" not generated-from-scratch every time.

**Workflow:**
1. Developer A builds a "Salesforce Query Tool" that works perfectly
2. Push to **Anvil Private Registry** (versioned)
3. Developer B's agent pulls exact version (no regeneration)
4. When Salesforce API changes, Anvil updates once → all agents inherit fix

---

### Phase 5: Collaboration Features

**Priority: MEDIUM** | Enterprise Table Stakes

| Feature | Description |
|---------|-------------|
| **SSO** | Okta/Google Workspace integration (non-negotiable) |
| **RBAC** | Admin (approve patches) / Developer (view logs) / Viewer (dashboard only) |
| **Audit Logs** | Complete trail of who did what |

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Customer Infrastructure                      │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────────┐  │
│  │ AI Agent │───▶│ Anvil SDK │───▶│ ./anvil_tools Cache  │  │
│  └──────────┘    └─────┬─────┘    └──────────────────────┘  │
│                        │                                     │
│              ┌─────────┴─────────┐                          │
│              │                   │                          │
│        Logs & Alerts      Pull Policies                     │
│              │                   │                          │
└──────────────┼───────────────────┼──────────────────────────┘
               │                   │
               ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Anvil Cloud (The Business)                │
│                                                              │
│  ┌────────────────┐    ┌──────────┐    ┌─────────────────┐  │
│  │ Telemetry      │───▶│ Database │───▶│ Web Dashboard   │  │
│  │ Ingest         │    └────┬─────┘    └─────────────────┘  │
│  └────────────────┘         │                               │
│                             ▼                               │
│  ┌─────────────────┐   ┌─────────────────────────────────┐  │
│  │ Policy Engine   │   │ Private Tool Registry           │  │
│  └─────────────────┘   └─────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
               ▲                   ▲
               │                   │
         Views Health      Approves Patches
               │                   │
          ┌────┴───────────────────┴────┐
          │        DevOps Lead          │
          └─────────────────────────────┘
```

---

## Implementation Plan

### Sprint 1: Ghost Dashboard (Week 1-2)
- [ ] Build React/Next.js mockup dashboard
- [ ] Mock data: "Tools Broken vs Fixed" graph
- [ ] Mock data: "Recent Incidents" list
- [ ] Pitch deck with demo

**Validation Question:** "Would you pay $20/month per agent for this view?"

### Sprint 2: Telemetry Foundation (Week 3-4)
- [ ] Design Incident Report JSON schema
- [ ] Add async event emission to `logger.py`
- [ ] Add heartbeat mechanism to SDK
- [ ] Build telemetry ingest endpoint

### Sprint 3: Governance MVP (Week 5-6)
- [ ] Implement Policy-as-Code in sandbox
- [ ] Add allowed/blocked import lists
- [ ] Build Slack/Email notification for approvals
- [ ] Secret redaction in logs

### Sprint 4: Registry v1 (Week 7-8)
- [ ] Design registry data model
- [ ] Build push/pull API for Golden Tools
- [ ] Version management
- [ ] SDK integration for registry fallback

### Sprint 5: Auth & Access (Week 9-10)
- [ ] SSO integration (Okta, Google)
- [ ] RBAC implementation
- [ ] Audit logging

---

## Pricing Model (Proposed)

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | SDK only, local execution |
| **Team** | $20/agent/month | Dashboard, telemetry, basic policies |
| **Enterprise** | Custom | Private registry, SSO, RBAC, SLA |

---

## Current Tech Stack

**SDK (Built):**
- Python 3.10+
- httpx, click, rich, python-dotenv
- anthropic, openai (optional)

**Cloud (To Build):**
- Frontend: React/Next.js
- Backend: FastAPI or Node.js
- Database: PostgreSQL + TimescaleDB (for metrics)
- Queue: Redis or SQS (for async telemetry)
- Auth: Auth0 or Clerk (SSO-ready)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to first paid customer | 30 days after ghost dashboard |
| Self-healing saves (hours/week) | Trackable in dashboard |
| Enterprise pilot | 1 company within 60 days |
