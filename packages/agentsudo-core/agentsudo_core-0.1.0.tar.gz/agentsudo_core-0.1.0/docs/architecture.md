# AgentSudo Architecture

## Overview

AgentSudo is a **Zero Trust Middleware** for AI agents implementing:
- Just-In-Time (JIT) access control
- Human-in-the-Loop (HITL) approval workflows
- Multi-signal risk analysis
- Transparency logging (Why-Logs)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                               AI AGENTS                                      │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐                │
│  │ Research  │  │   Intern  │  │  Customer │  │   Data    │                │
│  │    Bot    │  │    Bot    │  │ Service   │  │  Analyst  │                │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘                │
└────────┼──────────────┼──────────────┼──────────────┼───────────────────────┘
         │              │              │              │
         └──────────────┴──────────────┴──────────────┘
                                │
                     AgentSudo SDK (get_session)
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AGENTSUDO SERVER                                    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         MIDDLEWARE STACK                              │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │   Logging   │  │   Metrics   │  │ Rate Limit  │  │    CORS    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          API LAYER (v1)                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │  │
│  │  │   Access    │  │  Approvals  │  │    Audit    │  │   Health   │  │  │
│  │  │   Control   │  │    HITL     │  │   Why-Logs  │  │   Checks   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          CORE SERVICES                                │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                     POLICY ENGINE                                │ │  │
│  │  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌────────────┐  │ │  │
│  │  │  │   Rules   │  │ Behavioral│  │  Semantic │  │    LLM     │  │ │  │
│  │  │  │  Analyzer │  │  Analyzer │  │  Analyzer │  │  Analyzer  │  │ │  │
│  │  │  │  (0.4)    │  │   (0.3)   │  │   (0.2)   │  │   (0.3)    │  │ │  │
│  │  │  └───────────┘  └───────────┘  └───────────┘  └────────────┘  │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                        │  │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │  │
│  │  │    Token      │  │   Approval    │  │    Budget     │            │  │
│  │  │   Manager     │  │   Service     │  │    Tracker    │            │  │
│  │  │   (JWT)       │  │   (HITL)      │  │   (Spend)     │            │  │
│  │  └───────────────┘  └───────────────┘  └───────────────┘            │  │
│  │                                                                        │  │
│  │  ┌───────────────────────────────────────────────────────────────┐   │  │
│  │  │                    AUDIT LOGGER (Why-Logs)                     │   │  │
│  │  └───────────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           STORAGE LAYER                                       │
│                                                                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                  │
│  │     Redis      │  │    Policies    │  │   Prometheus   │                  │
│  │  (State/Cache) │  │    (YAML)      │  │   (Metrics)    │                  │
│  └────────────────┘  └────────────────┘  └────────────────┘                  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Request Flow

### 1. Standard Access Request

```
Agent                    AgentSudo                    Tool
  │                          │                          │
  │  get_session(tool)       │                          │
  │─────────────────────────>│                          │
  │                          │                          │
  │            ┌─────────────┴─────────────┐            │
  │            │ 1. Authenticate           │            │
  │            │ 2. Validate tool          │            │
  │            │ 3. Policy Engine eval     │            │
  │            │ 4. Budget check           │            │
  │            │ 5. Issue JWT token        │            │
  │            └─────────────┬─────────────┘            │
  │                          │                          │
  │  200 OK + Token          │                          │
  │<─────────────────────────│                          │
  │                          │                          │
  │  API call with token     │                          │
  │──────────────────────────┼─────────────────────────>│
  │                          │                          │
```

### 2. Human-in-the-Loop (HITL) Flow

```
Agent                  AgentSudo               Human                Tool
  │                        │                     │                    │
  │ get_session(amt=$100)  │                     │                    │
  │───────────────────────>│                     │                    │
  │                        │                     │                    │
  │      ┌─────────────────┴─────────────────┐   │                    │
  │      │ Amount $100 > threshold $50       │   │                    │
  │      │ Create approval ticket            │   │                    │
  │      └─────────────────┬─────────────────┘   │                    │
  │                        │                     │                    │
  │  202 Accepted          │  Notify             │                    │
  │  + Ticket ID           │────────────────────>│                    │
  │<───────────────────────│                     │                    │
  │                        │                     │                    │
  │  Notify user           │                     │  Review            │
  │  "Need approval"       │                     │  request           │
  │                        │                     │                    │
  │                        │     Approve         │                    │
  │                        │<────────────────────│                    │
  │                        │                     │                    │
  │  Poll for status       │                     │                    │
  │───────────────────────>│                     │                    │
  │                        │                     │                    │
  │  200 OK + Token        │                     │                    │
  │<───────────────────────│                     │                    │
  │                        │                     │                    │
  │  API call              │                     │                    │
  │────────────────────────┼─────────────────────┼───────────────────>│
  │                        │                     │                    │
```

---

## Policy Engine

### Multi-Signal Risk Analysis

The Policy Engine combines multiple analyzers:

| Analyzer | Weight | Purpose |
|----------|--------|---------|
| **Rule-Based** | 0.4 | Fast pattern matching for known threats |
| **Behavioral** | 0.3 | Anomaly detection (rate, errors, sprawl) |
| **Semantic** | 0.2 | Similarity to known dangerous intents |
| **LLM** | 0.3 | Reasoning about complex threats |

### Risk Score Calculation

```python
risk_score = Σ(analyzer_score × analyzer_weight) / Σ(weights)
```

### Risk Levels

| Level | Threshold | Action |
|-------|-----------|--------|
| LOW | < 0.3 | Allow |
| MEDIUM | 0.3 - 0.5 | Allow + Monitor |
| HIGH | 0.5 - 0.7 | Block |
| CRITICAL | > 0.7 | Block + Alert |

---

## Token Architecture

### JWT Structure

```json
{
  "jti": "jti_abc123...",      // Token ID
  "sub": "research_bot_01",    // Agent ID
  "iss": "agentsudo",          // Issuer
  "iat": 1706180000,           // Issued at
  "exp": 1706180300,           // Expires (5 min)
  "nbf": 1706180000,           // Not before
  "tool": "openai_api",        // Tool access
  "scopes": ["invoke"],        // Permissions
  "budget_allocation": 0.03,   // Cost
  "risk_score": 0.15,          // Risk at issuance
  "approval_ticket": null      // HITL ticket if any
}
```

### Token Lifecycle

```
Issue → Active → [Revoke] → Expired
         │
         └─→ Introspect
```

---

## Deployment Options

### Development

```bash
make dev
make run
```

### Production (Docker)

```bash
docker-compose -f deploy/docker/docker-compose.yml up -d
```

### Kubernetes

```yaml
# Deployment with HPA
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentsudo
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: agentsudo
        image: ghcr.io/agentsudo/agentsudo:latest
        env:
        - name: AGENTSUDO_ENV
          value: production
        - name: AGENTSUDO_REDIS_URL
          valueFrom:
            secretKeyRef:
              name: agentsudo-secrets
              key: redis-url
```

---

## Security Principles

Based on **Auth0 2025 Identity Report**:

1. **Zero Trust**: Every request verified, no implicit trust
2. **Least Privilege**: Agents only access allowed tools
3. **Time-Bound**: 5-minute token lifetime
4. **Human-in-the-Loop**: Approval for high-risk operations
5. **Audit Trail**: Every decision logged with reasoning
6. **Budget Enforcement**: Prevent Denial of Wallet
7. **Sponsor Accountability**: Each agent has a human owner
