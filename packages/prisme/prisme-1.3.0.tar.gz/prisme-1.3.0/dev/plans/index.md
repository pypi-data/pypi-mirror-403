# Implementation Plans

Detailed implementation plans for features and significant changes to Prism.

## Plan Status Overview

```mermaid
pie title Plans by Priority
    "P0 - Critical" : 2
    "P1 - Important" : 4
    "P2 - Medium" : 0
    "P3 - Nice-to-have" : 0
```

## Active Plans

### P0 - Critical Priority

| Plan | Description | Status |
|------|-------------|--------|
| [Background Jobs & Scheduling](background-jobs-scheduling-plan.md) | APScheduler integration for data ingestion | :material-circle-outline: Not Started |
| [TimescaleDB Support](timescaledb-support-plan.md) | Time-series hypertables, compression, retention | :material-circle-outline: Not Started |

### P1 - Important Priority

| Plan | Description | Status |
|------|-------------|--------|
| [External Service Integration](external-service-integration-plan.md) | Type-safe HTTP clients for external APIs | :material-circle-outline: Not Started |
| [Webhook/Event Handling](webhook-event-handling-plan.md) | Authenticated webhook endpoints | :material-circle-outline: Not Started |
| [Authentik Integration](authentik-integration-plan.md) | Self-hosted auth with MFA, IAM, subdomains | :material-circle-outline: Not Started |

### Platform / Developer Experience

| Plan | Description | Status |
|------|-------------|--------|
| [Managed Subdomain + HTTPS](managed-subdomain-plan.md) | `*.madewithpris.me` subdomains with auto-SSL for Hetzner | :material-progress-clock: In Progress (85%) |
| [Dev Container with Claude Code](devcontainer-claude-code-plan.md) | Self-hosted Codespaces with Claude Code pre-installed | :material-progress-clock: In Progress (85%) |

## Plan Dependencies

```mermaid
graph LR
    subgraph "P0 - Foundation"
        BG[Background Jobs]
        TS[TimescaleDB]
    end

    subgraph "P1 - Integration"
        ES[External Services]
        WH[Webhooks]
        AU[Authentik]
        DC[Dev Container + Claude Code]
    end

    subgraph "P2+ - Extensions"
        CA[Continuous Aggregates]
        MF[Media Files]
    end

    TS --> CA
    BG --> WH
    ES --> AU
    WH --> AU

    style BG fill:#ff6b6b
    style TS fill:#ff6b6b
    style ES fill:#ffd93d
    style WH fill:#ffd93d
    style AU fill:#ffd93d
    style DC fill:#6bcff6
```

## Creating New Plans

Follow the template in [Documentation Guide](../dev-docs.md#plans-plans):

```markdown
# Plan: <Feature Name>

**Status**: Draft | Approved | In Progress | Complete
**Author**: <name>
**Created**: YYYY-MM-DD
**Updated**: YYYY-MM-DD

## Overview
## Goals
## Non-Goals
## Design
## Implementation Steps
## Testing Strategy
## Rollout Plan
## Open Questions
```
