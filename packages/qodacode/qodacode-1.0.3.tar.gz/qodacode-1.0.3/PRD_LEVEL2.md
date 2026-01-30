# Qodacode PRD Level 2
## From Wrapper to Platform: Enterprise Security for AI-Assisted Development

> **Version:** 2.0.0-draft
> **Date:** 2026-01-20
> **Author:** Product & Engineering
> **Status:** Planning

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Vision & Mission](#2-vision--mission)
3. [Market Analysis](#3-market-analysis)
4. [User Personas](#4-user-personas)
5. [Product Requirements](#5-product-requirements)
6. [Technical Architecture](#6-technical-architecture)
7. [System Design](#7-system-design)
8. [API Specifications](#8-api-specifications)
9. [Data Models](#9-data-models)
10. [Infrastructure](#10-infrastructure)
11. [Security & Compliance](#11-security--compliance)
12. [Roadmap & Milestones](#12-roadmap--milestones)
13. [Success Metrics](#13-success-metrics)
14. [Risk Analysis](#14-risk-analysis)
15. [Appendix](#15-appendix)

---

# 1. Executive Summary

## 1.1 The Problem

Developers using AI coding assistants (Cursor, Claude Code, GitHub Copilot) generate code 10x faster than before. But this velocity creates a security gap:

- **AI generates insecure code** — SQL injection, hardcoded secrets, command injection
- **No real-time feedback** — Security tools run after the fact, not during development
- **Enterprise tools don't fit** — Snyk, SonarQube designed for pre-AI workflows
- **Configuration hell** — 5+ tools to configure, maintain, and understand

## 1.2 The Solution

**Qodacode** is the first security scanner built natively for AI-assisted development:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   Developer writes with Cursor/Claude Code                      │
│                    ↓                                            │
│   Qodacode watches in real-time (<100ms)                        │
│                    ↓                                            │
│   Security issue detected → AI receives feedback                │
│                    ↓                                            │
│   AI fixes automatically → Developer continues                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 1.3 Key Differentiators

| Differentiator | Description | Competitive Advantage |
|----------------|-------------|----------------------|
| **MCP Native** | First security scanner with Model Context Protocol | Claude Code integration out-of-box |
| **<100ms Scans** | Diff-aware, cached, parallel execution | 10-100x faster than Snyk/Sonar |
| **Zero Config** | `npx qodacode` — works immediately | No YAML hell, no accounts |
| **Local-First** | No cloud required, GDPR compliant | Enterprise security teams love this |
| **AI-Native Output** | Structured for AI consumption and auto-fix | Closes the feedback loop |

## 1.4 Interface Strategy: Same Core, Different UX

```
┌─────────────────────────────────────────────────────────────────┐
│                    QODACODE INTERFACES                           │
├─────────────────┬────────────────┬────────────────┬─────────────┤
│      CLI        │      TUI       │      MCP       │   REPORT    │
│   Developer     │   Explorer     │   AI Agent     │  Stakeholder│
├─────────────────┼────────────────┼────────────────┼─────────────┤
│ • CI/CD         │ • Interactive  │ • Claude Code  │ • PDF/HTML  │
│ • Pre-commit    │ • Real-time    │ • Cursor       │ • Executive │
│ • Automation    │ • Filter/Sort  │ • AUTO-FIX     │ • Compliance│
│ • JSON output   │ • Navigation   │ • Explain+Fix  │ • Trends    │
└─────────────────┴────────────────┴────────────────┴─────────────┘
```

**What's Common (ALL interfaces):**
- Typosquatting detection
- Security/robustness scanning
- Dependency vulnerabilities (CVEs)
- Secret detection
- Same verdicts (READY / NOT READY)

**What's UNIQUE to MCP:**
- `fix_issue` - AI generates actual code patches
- `explain_and_fix` - Combined learning + remediation
- Auto-remediation workflow (AI reads issue → generates fix → applies it)

**The "fix_issue" Advantage:**
```
Human workflow:  See issue → Read docs → Write fix → Test
AI workflow:     See issue → Call fix_issue → Apply patch → Done

MCP makes Qodacode an "agentic security tool" - AI doesn't just find
issues, it FIXES them automatically.
```

## 1.5 Business Model

| Tier | Price | Target |
|------|-------|--------|
| **Free** | $0 | Individual developers, OSS projects |
| **Pro** | $9/dev/month | Freelancers, indie hackers |
| **Team** | $19/dev/month | Startups, teams 5-50 |
| **Business** | $39/dev/month | Scale-ups, teams 50-200 |

**Open Core Model:**
- CLI, MCP Server, all rules → **Free forever**
- Dashboard, team features, history → **Paid**

---

# 2. Vision & Mission

## 2.1 Vision Statement

> **Be the security infrastructure layer for AI-assisted development.**

In 3 years, every developer using Cursor, Claude Code, or similar tools will have Qodacode running in the background — not because they chose it, but because it's the default.

## 2.2 Mission Statement

> **Make enterprise-grade security accessible to every developer, at any scale, with zero friction.**

## 2.3 Strategic Pillars

```
                    QODACODE STRATEGY
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │  SPEED  │      │   UX    │      │   AI    │
   │         │      │         │      │ NATIVE  │
   │ <100ms  │      │  Zero   │      │  MCP    │
   │  scans  │      │ config  │      │  First  │
   └─────────┘      └─────────┘      └─────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                    ┌─────▼─────┐
                    │  MOAT:    │
                    │ Enterprise│
                    │ for All   │
                    └───────────┘
```

## 2.4 What We Are NOT

- ❌ Not a replacement for Snyk/Sonar in Fortune 500 companies
- ❌ Not a compliance certification tool (SOC2, HIPAA audits)
- ❌ Not a penetration testing platform
- ❌ Not a cloud security posture management (CSPM) tool

## 2.5 What We ARE

- ✅ The fastest security scanner for developers
- ✅ The only MCP-native security tool
- ✅ Enterprise features at indie prices
- ✅ The security layer for AI-generated code

---

# 3. Market Analysis

## 3.1 Market Size

### Total Addressable Market (TAM)

| Segment | Size | Source |
|---------|------|--------|
| Global DevSecOps Market | $8.2B (2025) | Gartner |
| Application Security Testing | $4.1B (2025) | MarketsandMarkets |
| Developer Tools | $15B (2025) | IDC |

### Serviceable Addressable Market (SAM)

| Segment | Developers | Value |
|---------|------------|-------|
| Developers using AI coding tools | 15M+ | Growing 50% YoY |
| Teams 5-50 developers | 500K teams | Underserved by enterprise |
| Indie developers / freelancers | 10M+ | Price-sensitive, need simple tools |

### Serviceable Obtainable Market (SOM) — Year 1

| Target | Users | Revenue Potential |
|--------|-------|-------------------|
| Indie devs (free) | 10,000 | $0 (funnel) |
| Pro conversions (2%) | 200 | $21,600/year |
| Team conversions (0.5%) | 50 teams × 10 devs | $114,000/year |
| **Total Year 1** | | **$135,600 ARR** |

## 3.2 Competitive Landscape

### Direct Competitors

| Competitor | Strengths | Weaknesses | Our Advantage |
|------------|-----------|------------|---------------|
| **Snyk** | CVE database, enterprise | Slow, expensive, cloud-only | Speed, local-first, price |
| **SonarQube** | Established, comprehensive | Complex setup, slow | Zero config, speed |
| **CodeQL** | Deep analysis, GitHub native | Slow, requires Actions | Real-time, MCP native |
| **Semgrep** | Fast, good rules | CLI-only, no AI integration | MCP, AI explanations |
| **CodeRabbit** | AI-native, PR reviews | Cloud-only, expensive, not real-time | Local, real-time, cheaper |

### Competitive Positioning Matrix

```
                    SPEED
                      ▲
                      │
         Qodacode ◆   │
                      │
    ──────────────────┼──────────────────▶ ENTERPRISE
                      │                     FEATURES
         Semgrep ◆    │         ◆ SonarQube
                      │
         Gitleaks ◆   │         ◆ Snyk
                      │
                      │              ◆ CodeRabbit
```

### Why Now?

1. **AI Coding Explosion** — Cursor, Claude Code, Copilot growing exponentially
2. **Security Debt Accumulating** — AI-generated code = more vulnerabilities
3. **Enterprise Tools Too Slow** — Designed for CI/CD, not real-time
4. **MCP Standard Emerging** — Anthropic's protocol becoming standard
5. **Developer-First Buying** — Bottom-up adoption replacing enterprise sales

## 3.3 Market Trends

| Trend | Implication for Qodacode |
|-------|-------------------------|
| AI-assisted development mainstream | Core market growing rapidly |
| Shift-left security | Developers want tools during coding, not after |
| Developer experience matters | Zero-config wins over feature-rich |
| Local-first / privacy concerns | Cloud-only tools losing favor |
| MCP adoption | Early mover advantage |

---

# 4. User Personas

## 4.1 Primary Personas

### Persona 1: "Vibe Coder" — Alex

```
┌──────────────────────────────────────────────────────────────┐
│ ALEX — The Vibe Coder                                        │
├──────────────────────────────────────────────────────────────┤
│ Age: 24 | Location: Remote | Experience: 2 years            │
│ Tools: Cursor, Claude Code, Vercel, Supabase                 │
├──────────────────────────────────────────────────────────────┤
│ GOALS                          │ FRUSTRATIONS                │
│ • Ship fast                    │ • Security is boring        │
│ • Learn while building         │ • Too many tools to config  │
│ • Build portfolio projects     │ • Enterprise tools expensive│
│ • Get hired at startup         │ • Don't know what's insecure│
├──────────────────────────────────────────────────────────────┤
│ QUOTE: "I just want to build. Tell me if I'm doing           │
│         something stupid, but don't slow me down."           │
├──────────────────────────────────────────────────────────────┤
│ QODACODE VALUE:                                              │
│ • Junior mode explains WHY something is insecure             │
│ • Zero config — just works                                   │
│ • Free tier covers all their needs                           │
│ • Learns security while coding                               │
└──────────────────────────────────────────────────────────────┘
```

### Persona 2: "The Pragmatic Senior" — Maya

```
┌──────────────────────────────────────────────────────────────┐
│ MAYA — The Pragmatic Senior                                  │
├──────────────────────────────────────────────────────────────┤
│ Age: 32 | Location: San Francisco | Experience: 8 years     │
│ Tools: Claude Code, NeoVim, GitHub Actions                   │
├──────────────────────────────────────────────────────────────┤
│ GOALS                          │ FRUSTRATIONS                │
│ • Ship quality code fast       │ • AI generates insecure code│
│ • Mentor junior devs           │ • PR reviews catch issues   │
│ • Reduce tech debt             │   too late                  │
│ • Automate security checks     │ • Snyk is overkill for team │
├──────────────────────────────────────────────────────────────┤
│ QUOTE: "I use AI to code faster, but I need guardrails.      │
│         Something that catches issues before commit."        │
├──────────────────────────────────────────────────────────────┤
│ QODACODE VALUE:                                              │
│ • Watch mode catches issues in real-time                     │
│ • Pre-commit hooks block bad code                            │
│ • Senior mode — just facts, no fluff                         │
│ • MCP integration with Claude Code                           │
└──────────────────────────────────────────────────────────────┘
```

### Persona 3: "The Startup Tech Lead" — Jordan

```
┌──────────────────────────────────────────────────────────────┐
│ JORDAN — The Startup Tech Lead                               │
├──────────────────────────────────────────────────────────────┤
│ Age: 35 | Location: Austin | Team: 15 developers            │
│ Tools: GitHub, Cursor, Slack, Linear                         │
├──────────────────────────────────────────────────────────────┤
│ GOALS                          │ FRUSTRATIONS                │
│ • Keep team velocity high      │ • No budget for Snyk        │
│ • Avoid security incidents     │ • Can't hire security eng   │
│ • Make security automatic      │ • Manual reviews don't scale│
│ • Track security posture       │ • No visibility into trends │
├──────────────────────────────────────────────────────────────┤
│ QUOTE: "We need enterprise security without enterprise       │
│         complexity or enterprise pricing."                   │
├──────────────────────────────────────────────────────────────┤
│ QODACODE VALUE:                                              │
│ • Team dashboard shows trends                                │
│ • $285/month vs $2000+/month for Snyk                       │
│ • GitHub Action blocks insecure PRs                          │
│ • Slack notifications on criticals                           │
└──────────────────────────────────────────────────────────────┘
```

## 4.2 Secondary Personas

| Persona | Description | Key Need |
|---------|-------------|----------|
| **OSS Maintainer** | Maintains popular open-source project | Free scanning, GitHub integration |
| **Security Champion** | Developer who cares about security | Advanced rules, custom policies |
| **Freelance Consultant** | Works with multiple clients | Quick setup per project, professional reports |
| **Bootcamp Graduate** | Learning to code professionally | Educational explanations, learning path |

## 4.3 Anti-Personas (Who We Don't Serve)

| Anti-Persona | Why Not |
|--------------|---------|
| Fortune 500 CISO | Need SOC2, HIPAA, vendor management |
| Compliance Auditor | Need formal reports, attestations |
| Penetration Tester | Need exploitation tools, not scanning |
| Legacy Enterprise | No AI tools, waterfall process |

---

# 5. Product Requirements

## 5.1 Core Product Principles

1. **Speed Over Features** — A fast tool with fewer features beats a slow tool with many
2. **Zero Config by Default** — Must work with no setup, configuration is optional
3. **Local-First** — No cloud required, no accounts required for core functionality
4. **AI-Native** — Built for AI workflows, not adapted from pre-AI tools
5. **Developer Experience** — Every interaction should feel good, not like a chore

## 5.2 Feature Requirements by Release

### v0.2.0 — "Solid Foundation"

| Feature | Priority | Description | Success Criteria |
|---------|----------|-------------|------------------|
| **Cleanup Dead Code** | P0 | Remove Memory, LSP stub, login | Zero unused code |
| **Watch Mode Stable** | P0 | Real-time file watching | <500ms detection |
| **CI Tested** | P0 | GitHub Actions verified | Passing in real repos |
| **Performance Benchmarks** | P0 | Documented scan times | Published numbers |
| **Error Handling** | P1 | Graceful degradation | Works without engines |

### v0.3.0 — "The Security MCP"

| Feature | Priority | Description | Success Criteria |
|---------|----------|-------------|------------------|
| **MCP Server Bulletproof** | P0 | All tools tested and documented | 100% test coverage |
| **scan_diff Tool** | P0 | Scan only changed files | <100ms for typical diff |
| **fix_issue Tool** | P0 | AI can request fixes | Returns fix code |
| **Claude Code Docs** | P0 | Setup documentation | 30-second onboarding |
| **Cursor Docs** | P1 | Setup documentation | 30-second onboarding |
| **explain_and_fix Tool** | P1 | Combined explanation + fix | Junior mode enhanced |

### v0.4.0 — "Fastest Scanner"

| Feature | Priority | Description | Success Criteria |
|---------|----------|-------------|------------------|
| **Diff-Aware Scanning** | P0 | Git-based change detection | Only scan changes |
| **Result Caching** | P0 | Hash-based cache | Skip unchanged files |
| **Parallel Execution** | P0 | Run engines concurrently | Gitleaks ∥ AST |
| **<100ms Diff Scans** | P0 | Target performance | Verified benchmarks |
| **Public Benchmarks** | P1 | vs Snyk, Sonar, Semgrep | Marketing asset |

### v0.5.0 — "Native Rules Engine"

| Feature | Priority | Description | Success Criteria |
|---------|----------|-------------|------------------|
| **50+ AST Rules** | P0 | Expand native ruleset | Cover OWASP Top 10 |
| **Taint Tracking (Basic)** | P1 | Data flow analysis | SQL injection sources |
| **Go Support** | P1 | Tree-sitter Go | Full rule coverage |
| **Rust Support** | P2 | Tree-sitter Rust | Full rule coverage |
| **Custom Rules API** | P2 | User-defined rules | YAML-based |

### v1.0.0 — "Enterprise for Everyone"

| Feature | Priority | Description | Success Criteria |
|---------|----------|-------------|------------------|
| **Dashboard Web** | P0 | Scan history, trends | Vercel + Supabase |
| **GitHub OAuth** | P0 | Login with GitHub | 1-click signup |
| **Team Management** | P0 | Invite developers | Share projects |
| **Scan History** | P0 | Last 30 scans | Trend visualization |
| **Slack Webhook** | P1 | Critical notifications | Real-time alerts |
| **Stripe Integration** | P1 | Payment processing | Pro/Team tiers |
| **GitHub App** | P2 | Deep integration | Auto-PR comments |

## 5.3 Non-Functional Requirements

### Performance

| Metric | Requirement | Stretch Goal |
|--------|-------------|--------------|
| Full scan (50 files) | <1 second | <500ms |
| Diff scan (5 files) | <100ms | <50ms |
| Watch mode latency | <500ms | <200ms |
| Memory usage | <200MB | <100MB |
| Startup time | <1 second | <500ms |

### Reliability

| Metric | Requirement |
|--------|-------------|
| Uptime (Dashboard) | 99.9% |
| CLI crash rate | <0.1% |
| False positive rate | <5% |
| Engine failure recovery | Graceful degradation |

### Scalability

| Metric | Requirement |
|--------|-------------|
| Max repo size | 100K files |
| Max concurrent users (dashboard) | 10K |
| Max scan history (per project) | 1 year |

### Compatibility

| Platform | Requirement |
|----------|-------------|
| macOS | 12+ (Monterey) |
| Linux | Ubuntu 20.04+, Debian 11+ |
| Windows | 10+ (WSL2) |
| Node.js | 18+ (for npx) |
| Python | 3.10+ |

---

# 6. Technical Architecture

## 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              QODACODE PLATFORM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CLIENT LAYER                                 │   │
│  ├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┤   │
│  │    CLI      │    TUI      │  MCP Server │  VS Code    │  Dashboard  │   │
│  │  (Click)    │ (Textual)   │ (Anthropic) │  Extension  │   (React)   │   │
│  └──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┘   │
│         │             │             │             │             │           │
│         └─────────────┴─────────────┼─────────────┴─────────────┘           │
│                                     │                                       │
│  ┌──────────────────────────────────▼──────────────────────────────────┐   │
│  │                          CORE ENGINE                                 │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│  │  │  Orchestrator│  │   Scanner   │  │   Cache     │  │  Reporter │  │   │
│  │  │             │  │  (Parallel) │  │  (Hash-based)│  │           │  │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘  │   │
│  │         │                │                │                │        │   │
│  └─────────┼────────────────┼────────────────┼────────────────┼────────┘   │
│            │                │                │                │            │
│  ┌─────────▼────────────────▼────────────────▼────────────────▼────────┐   │
│  │                        ANALYSIS LAYER                                │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│  │  │  AST Engine │  │  Gitleaks   │  │   Semgrep   │  │    OSV    │  │   │
│  │  │ (Tree-sitter)│ │   Runner   │  │   Runner    │  │  Scanner  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │Taint Tracker│  │  License    │  │ Typosquat   │                  │   │
│  │  │  (Future)   │  │  Checker    │  │  Detector   │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         DATA LAYER                                   │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│  │  │   Local     │  │   Rules     │  │   Config    │  │ Suppression│  │   │
│  │  │   Cache     │  │   Registry  │  │   Store     │  │   Store   │  │   │
│  │  │ (.qodacode/)│  │  (Built-in) │  │   (JSON)    │  │   (JSON)  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    │ (Optional - Paid Features)
                                    ▼

┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLOUD LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Vercel    │  │  Supabase   │  │   Stripe    │  │   Resend    │        │
│  │  (Frontend) │  │ (Database)  │  │ (Payments)  │  │  (Email)    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6.2 Component Architecture

### 6.2.1 CLI Component

```
qodacode/
├── cli.py                    # Click command definitions
├── commands/
│   ├── scan.py              # Quick scan command
│   ├── check.py             # Full check command
│   ├── watch.py             # Watch mode
│   ├── ci.py                # CI/CD integration
│   └── config.py            # Configuration management
└── output/
    ├── terminal.py          # Rich terminal output
    ├── json.py              # JSON output
    ├── sarif.py             # SARIF output
    └── markdown.py          # Markdown output
```

### 6.2.2 Core Engine Component

```
qodacode/
├── core/
│   ├── orchestrator.py      # Coordinates all engines
│   ├── scanner.py           # Parallel file scanning
│   ├── cache.py             # Hash-based result caching
│   ├── diff.py              # Git diff detection
│   └── dedup.py             # Issue deduplication
└── models/
    ├── issue.py             # Pydantic Issue model
    ├── scan_result.py       # Scan result container
    └── config.py            # Configuration model
```

### 6.2.3 Analysis Layer Component

```
qodacode/
├── engines/
│   ├── base.py              # Abstract EngineRunner
│   ├── ast_engine.py        # Tree-sitter analysis
│   ├── gitleaks_runner.py   # Gitleaks integration
│   ├── semgrep_runner.py    # Semgrep integration
│   └── osv_runner.py        # OSV dependency scan
├── rules/
│   ├── base.py              # Abstract Rule class
│   ├── registry.py          # Auto-registering rules
│   ├── security/            # SEC-* rules
│   ├── robustness/          # ROB-* rules
│   ├── maintainability/     # MNT-* rules
│   └── operability/         # OPS-* rules
└── analyzers/
    ├── taint.py             # Taint tracking (future)
    ├── license.py           # License checking
    └── typosquat.py         # Typosquatting detection
```

### 6.2.4 MCP Server Component

```
qodacode/
└── mcp/
    ├── server.py            # MCP server entry point
    ├── tools/
    │   ├── scan.py          # scan_code, scan_diff
    │   ├── fix.py           # fix_issue, explain_and_fix
    │   ├── query.py         # list_rules, explain_issue
    │   └── health.py        # get_project_health
    └── protocol/
        ├── handlers.py      # Request handlers
        └── responses.py     # Response formatters
```

## 6.3 Data Flow Architecture

### 6.3.1 Scan Flow

```
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  CLI    │───▶│ Orchestrator│───▶│   Scanner   │───▶│   Engines   │
│  scan   │    │             │    │  (parallel) │    │ (parallel)  │
└─────────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
                      │                  │                  │
                      │                  │                  │
               ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
               │    Cache    │    │    Files    │    │   Issues    │
               │   (check)   │◀───│  (filtered) │    │  (merged)   │
               └─────────────┘    └─────────────┘    └──────┬──────┘
                                                            │
                      ┌─────────────────────────────────────┘
                      │
               ┌──────▼──────┐    ┌─────────────┐    ┌─────────────┐
               │    Dedup    │───▶│  Reporter   │───▶│   Output    │
               │             │    │             │    │ (terminal)  │
               └─────────────┘    └─────────────┘    └─────────────┘
```

### 6.3.2 Watch Mode Flow

```
┌─────────────┐
│  Filesystem │
│   Watcher   │
└──────┬──────┘
       │ file changed
       ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    Diff     │───▶│   Scanner   │───▶│   Output    │
│  Detector   │    │ (single file│    │ (streaming) │
└─────────────┘    └─────────────┘    └─────────────┘
       │
       │ debounce 100ms
       │
┌──────▼──────┐
│   Batch     │
│  Processor  │
└─────────────┘
```

### 6.3.3 MCP Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Claude Code │───▶│ MCP Server  │───▶│   Tool      │
│   (Client)  │    │  (stdio)    │    │  Handler    │
└─────────────┘    └──────┬──────┘    └──────┬──────┘
                          │                  │
                   ┌──────▼──────┐    ┌──────▼──────┐
                   │   Request   │    │   Core      │
                   │   Parser    │    │   Engine    │
                   └─────────────┘    └──────┬──────┘
                                             │
                   ┌─────────────┐    ┌──────▼──────┐
                   │  Response   │◀───│   Result    │
                   │  Formatter  │    │  Processor  │
                   └──────┬──────┘    └─────────────┘
                          │
                   ┌──────▼──────┐
                   │   JSON-RPC  │
                   │   Response  │
                   └─────────────┘
```

## 6.4 Technology Stack

### Core (Python)

| Component | Technology | Why |
|-----------|------------|-----|
| CLI Framework | Click | Battle-tested, great DX |
| Terminal UI | Rich | Beautiful output, tables, progress |
| TUI Framework | Textual | Modern terminal apps |
| AST Parsing | Tree-sitter | Fast, multi-language, incremental |
| Data Validation | Pydantic v2 | Fast validation, serialization |
| MCP Server | mcp-python | Official Anthropic SDK |
| HTTP Client | httpx | Modern async HTTP |
| File Watching | watchdog | Cross-platform FS events |

### External Engines

| Engine | Purpose | Integration |
|--------|---------|-------------|
| Gitleaks | Secret detection | Binary, auto-download |
| Semgrep | Deep SAST | pip install, CLI |
| OSV Scanner | Dependency CVEs | Go binary or API |

### Dashboard (TypeScript)

| Component | Technology | Why |
|-----------|------------|-----|
| Framework | Next.js 14 | App router, RSC |
| Styling | Tailwind CSS | Rapid UI development |
| Components | shadcn/ui | Beautiful, accessible |
| Database | Supabase | PostgreSQL + Auth + Realtime |
| Hosting | Vercel | Zero-config deployment |
| Payments | Stripe | Industry standard |
| Charts | Recharts | Simple, React-native |

### Distribution

| Method | Technology | Target |
|--------|------------|--------|
| PyPI | pip install qodacode | Python developers |
| npm | npx qodacode | JavaScript developers |
| Homebrew | brew install qodacode | macOS power users |
| GitHub Releases | Binary downloads | CI/CD environments |

---

# 7. System Design

## 7.1 Scanning System Design

### 7.1.1 Parallel Scanning Architecture

```python
# Conceptual implementation
class ParallelScanner:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers)
        self.engines = [ASTEngine(), GitleaksEngine(), SemgrepEngine()]

    async def scan(self, files: list[Path]) -> list[Issue]:
        # Stage 1: File filtering (sync, fast)
        filtered = self.filter_files(files)

        # Stage 2: Cache check (sync, fast)
        uncached = self.check_cache(filtered)

        # Stage 3: Parallel engine execution
        tasks = []
        for engine in self.engines:
            task = asyncio.create_task(engine.scan(uncached))
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Stage 4: Merge and deduplicate
        issues = self.merge_results(results)
        issues = self.deduplicate(issues)

        # Stage 5: Update cache
        self.update_cache(uncached, issues)

        return issues
```

### 7.1.2 Caching Strategy

```
Cache Key Formula:
  hash = SHA256(file_path + file_content + engine_version + rules_version)

Cache Structure (.qodacode/cache/):
  ├── index.json          # Hash -> result mapping
  ├── results/
  │   ├── {hash1}.json    # Cached scan result
  │   ├── {hash2}.json
  │   └── ...
  └── metadata.json       # Cache stats, last cleanup

Cache Invalidation:
  - File content changes → new hash → cache miss
  - Engine version changes → global invalidation
  - Rules version changes → global invalidation
  - Manual: qodacode cache clear

TTL: 7 days (configurable)
Max Size: 100MB (configurable)
```

### 7.1.3 Diff-Aware Scanning

```python
class DiffDetector:
    def get_changed_files(self, base: str = "HEAD") -> list[Path]:
        """Get files changed since base commit."""
        # Staged changes
        staged = git("diff", "--cached", "--name-only")

        # Unstaged changes
        unstaged = git("diff", "--name-only")

        # Untracked files
        untracked = git("ls-files", "--others", "--exclude-standard")

        return set(staged + unstaged + untracked)

    def get_changed_lines(self, file: Path) -> list[tuple[int, int]]:
        """Get line ranges that changed."""
        diff = git("diff", "-U0", str(file))
        return parse_unified_diff(diff)
```

## 7.2 MCP Server Design

### 7.2.1 Tool Specifications

```json
{
  "tools": [
    {
      "name": "scan_code",
      "description": "Scan code for security issues",
      "inputSchema": {
        "type": "object",
        "properties": {
          "path": {
            "type": "string",
            "description": "Path to scan (default: current directory)"
          },
          "severity": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low", "all"],
            "default": "high"
          }
        }
      }
    },
    {
      "name": "scan_diff",
      "description": "Scan only changed files since last commit",
      "inputSchema": {
        "type": "object",
        "properties": {
          "base": {
            "type": "string",
            "description": "Base commit to compare (default: HEAD)",
            "default": "HEAD"
          }
        }
      }
    },
    {
      "name": "fix_issue",
      "description": "Get fix suggestion for a specific issue",
      "inputSchema": {
        "type": "object",
        "properties": {
          "file": {
            "type": "string",
            "description": "File path"
          },
          "line": {
            "type": "integer",
            "description": "Line number"
          },
          "rule_id": {
            "type": "string",
            "description": "Rule ID (e.g., SEC-001)"
          }
        },
        "required": ["file", "line", "rule_id"]
      }
    },
    {
      "name": "explain_and_fix",
      "description": "Get explanation and fix for an issue",
      "inputSchema": {
        "type": "object",
        "properties": {
          "file": {
            "type": "string"
          },
          "line": {
            "type": "integer"
          },
          "rule_id": {
            "type": "string"
          },
          "context_lines": {
            "type": "integer",
            "default": 5
          }
        },
        "required": ["file", "line", "rule_id"]
      }
    },
    {
      "name": "get_project_health",
      "description": "Get overall security health score",
      "inputSchema": {
        "type": "object",
        "properties": {}
      }
    }
  ]
}
```

### 7.2.2 Response Format for AI Consumption

```json
{
  "issues": [
    {
      "id": "issue-abc123",
      "rule_id": "SEC-002",
      "severity": "critical",
      "file": "src/api/users.py",
      "line": 42,
      "column": 15,
      "message": "SQL injection vulnerability",
      "context": {
        "before": ["def get_user(user_id):", "    conn = get_db()"],
        "line": "    cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")",
        "after": ["    return cursor.fetchone()"]
      },
      "fix": {
        "description": "Use parameterized query",
        "code": "cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))",
        "diff": "@@ -42 +42 @@\n-    cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")\n+    cursor.execute(\"SELECT * FROM users WHERE id = ?\", (user_id,))"
      },
      "learn_more": "https://owasp.org/www-community/attacks/SQL_Injection"
    }
  ],
  "summary": {
    "total": 1,
    "critical": 1,
    "high": 0,
    "medium": 0,
    "low": 0,
    "verdict": "NOT_READY",
    "message": "Fix 1 critical issue before production"
  }
}
```

## 7.3 Watch Mode Design

### 7.3.1 Debounced File Watching

```python
class WatchMode:
    def __init__(self, debounce_ms: int = 100):
        self.debounce_ms = debounce_ms
        self.pending_files: set[Path] = set()
        self.timer: Optional[Timer] = None

    def on_file_change(self, path: Path):
        """Called by watchdog on file change."""
        self.pending_files.add(path)

        # Cancel existing timer
        if self.timer:
            self.timer.cancel()

        # Start new debounce timer
        self.timer = Timer(
            self.debounce_ms / 1000,
            self.process_batch
        )
        self.timer.start()

    def process_batch(self):
        """Process accumulated file changes."""
        files = list(self.pending_files)
        self.pending_files.clear()

        # Scan only changed files
        issues = scanner.scan(files)

        # Stream output
        for issue in issues:
            self.output_issue(issue)
```

### 7.3.2 Terminal Output Streaming

```
┌─ QODACODE WATCH ─────────────────────────────────────────────┐
│ Watching: /Users/dev/myproject                               │
│ Files: 152 | Engines: AST, Gitleaks | Mode: Senior           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ [14:32:05] 📝 src/api/users.py changed                       │
│ [14:32:05] ⏳ Scanning...                                    │
│ [14:32:05] 🔴 CRITICAL SEC-002: SQL injection (line 42)      │
│                                                              │
│ [14:32:15] 📝 src/utils/helpers.py changed                   │
│ [14:32:15] ⏳ Scanning...                                    │
│ [14:32:15] ✅ No issues found                                │
│                                                              │
│ [14:32:30] 📝 src/api/users.py changed                       │
│ [14:32:30] ⏳ Scanning...                                    │
│ [14:32:30] ✅ SEC-002 fixed!                                 │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│ Total: 0 critical | 0 high | 0 medium | Press Ctrl+C to stop│
└──────────────────────────────────────────────────────────────┘
```

## 7.4 Rules Engine Design

### 7.4.1 Rule Definition Structure

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Category(Enum):
    SECURITY = "security"
    ROBUSTNESS = "robustness"
    MAINTAINABILITY = "maintainability"
    OPERABILITY = "operability"
    DEPENDENCIES = "dependencies"

@dataclass
class RuleMetadata:
    id: str                    # SEC-001
    name: str                  # hardcoded-secret
    severity: Severity
    category: Category
    description: str
    rationale: str
    fix_suggestion: str
    references: list[str]      # OWASP, CWE links
    languages: list[str]       # python, javascript, etc.
    tags: list[str]           # owasp-top-10, injection, etc.

class Rule(ABC):
    metadata: RuleMetadata

    @abstractmethod
    def check(self, tree: Tree, source: str, filepath: Path) -> list[Issue]:
        """Run the rule against parsed AST."""
        pass

    def __init_subclass__(cls, **kwargs):
        """Auto-register rule on definition."""
        super().__init_subclass__(**kwargs)
        RuleRegistry.register(cls)
```

### 7.4.2 Rule Registry

```python
class RuleRegistry:
    _rules: dict[str, type[Rule]] = {}

    @classmethod
    def register(cls, rule_class: type[Rule]):
        cls._rules[rule_class.metadata.id] = rule_class

    @classmethod
    def get(cls, rule_id: str) -> Optional[type[Rule]]:
        return cls._rules.get(rule_id)

    @classmethod
    def all(cls) -> list[type[Rule]]:
        return list(cls._rules.values())

    @classmethod
    def by_category(cls, category: Category) -> list[type[Rule]]:
        return [r for r in cls._rules.values()
                if r.metadata.category == category]

    @classmethod
    def by_severity(cls, min_severity: Severity) -> list[type[Rule]]:
        severity_order = [Severity.CRITICAL, Severity.HIGH,
                         Severity.MEDIUM, Severity.LOW]
        min_idx = severity_order.index(min_severity)
        return [r for r in cls._rules.values()
                if severity_order.index(r.metadata.severity) <= min_idx]
```

---

# 8. API Specifications

## 8.1 CLI API

### Commands

```bash
# Scanning
qodacode scan [PATH]                    # Quick scan
qodacode scan --full                    # Full scan with all engines
qodacode scan --diff                    # Scan only changed files
qodacode scan --severity critical       # Filter by severity

# Watch Mode
qodacode watch [PATH]                   # Real-time watching
qodacode watch --debounce 200           # Custom debounce (ms)

# Configuration
qodacode init                           # Initialize .qodacode/
qodacode config set ai.provider openai  # Set config value
qodacode config get ai.provider         # Get config value

# Rules
qodacode rules                          # List all rules
qodacode rules --category security      # Filter by category
qodacode explain SEC-001                # Explain a rule

# Suppression
qodacode suppress <fingerprint>         # Suppress an issue
qodacode unsuppress <fingerprint>       # Unsuppress
qodacode suppressed                     # List suppressions

# CI/CD
qodacode ci                             # CI mode (JSON output, exit codes)
qodacode ci --fail-on critical          # Fail only on critical

# Utilities
qodacode doctor                         # Check engine availability
qodacode version                        # Show version
qodacode cache clear                    # Clear cache
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No issues found (or below threshold) |
| 1 | Issues found above threshold |
| 2 | Configuration error |
| 3 | Engine error (graceful degradation) |
| 4 | Fatal error |

## 8.2 MCP Server API

### Connection

```json
{
  "mcpServers": {
    "qodacode": {
      "command": "qodacode",
      "args": ["serve", "--mcp"],
      "env": {}
    }
  }
}
```

### Tools

| Tool | Input | Output |
|------|-------|--------|
| `scan_code` | `{path?, severity?}` | Issues array |
| `scan_diff` | `{base?}` | Issues array |
| `scan_file` | `{file}` | Issues array |
| `fix_issue` | `{file, line, rule_id}` | Fix suggestion |
| `explain_and_fix` | `{file, line, rule_id}` | Explanation + fix |
| `list_rules` | `{category?}` | Rules array |
| `get_project_health` | `{}` | Health score |
| `check_secrets` | `{path?}` | Secrets array |
| `check_dependencies` | `{}` | CVEs array |

## 8.3 Dashboard API (Future)

### REST Endpoints

```
Authentication:
  POST   /api/auth/github           # GitHub OAuth
  POST   /api/auth/logout           # Logout
  GET    /api/auth/me               # Current user

Projects:
  GET    /api/projects              # List projects
  POST   /api/projects              # Create project
  GET    /api/projects/:id          # Get project
  DELETE /api/projects/:id          # Delete project

Scans:
  GET    /api/projects/:id/scans    # List scans
  POST   /api/projects/:id/scans    # Create scan (upload)
  GET    /api/scans/:id             # Get scan details

Teams:
  GET    /api/teams                 # List teams
  POST   /api/teams                 # Create team
  POST   /api/teams/:id/invite      # Invite member
  DELETE /api/teams/:id/members/:uid # Remove member

Webhooks:
  GET    /api/webhooks              # List webhooks
  POST   /api/webhooks              # Create webhook
  DELETE /api/webhooks/:id          # Delete webhook
```

---

# 9. Data Models

## 9.1 Core Models

### Issue Model

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Location(BaseModel):
    file: str
    line: int
    column: int
    end_line: Optional[int] = None
    end_column: Optional[int] = None

class CodeContext(BaseModel):
    before: list[str]          # Lines before
    line: str                  # The problematic line
    after: list[str]           # Lines after

class Fix(BaseModel):
    description: str
    code: str
    diff: Optional[str] = None

class Issue(BaseModel):
    id: str                    # Unique fingerprint
    rule_id: str               # SEC-001
    rule_name: str             # hardcoded-secret
    severity: str              # critical, high, medium, low
    category: str              # security, robustness, etc.
    message: str               # Human-readable message
    location: Location
    context: Optional[CodeContext] = None
    fix: Optional[Fix] = None
    engine: str                # ast, gitleaks, semgrep
    metadata: dict = {}        # Engine-specific data

    @property
    def fingerprint(self) -> str:
        """Stable identifier for deduplication/suppression."""
        return hashlib.sha256(
            f"{self.rule_id}:{self.location.file}:{self.location.line}"
            .encode()
        ).hexdigest()[:16]
```

### Scan Result Model

```python
class ScanSummary(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int
    by_category: dict[str, int]
    by_engine: dict[str, int]

class Verdict(BaseModel):
    status: str               # READY, NOT_READY
    message: str
    blocking_issues: int

class ScanResult(BaseModel):
    id: str
    timestamp: datetime
    duration_ms: int
    files_scanned: int
    issues: list[Issue]
    summary: ScanSummary
    verdict: Verdict
    engines_used: list[str]
    cache_hits: int
    cache_misses: int
```

### Configuration Model

```python
class AIConfig(BaseModel):
    provider: str = "openai"           # openai, anthropic, ollama
    api_key: Optional[str] = None
    model: Optional[str] = None

class ScanConfig(BaseModel):
    severity_threshold: str = "high"
    categories: list[str] = ["security", "robustness"]
    exclude_patterns: list[str] = []
    include_patterns: list[str] = ["**/*"]

class CacheConfig(BaseModel):
    enabled: bool = True
    ttl_days: int = 7
    max_size_mb: int = 100

class Config(BaseModel):
    ai: AIConfig = AIConfig()
    scan: ScanConfig = ScanConfig()
    cache: CacheConfig = CacheConfig()
```

## 9.2 Database Models (Dashboard)

```sql
-- Users (managed by Supabase Auth)
-- Extending auth.users with profiles

CREATE TABLE profiles (
    id UUID REFERENCES auth.users PRIMARY KEY,
    github_username TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Teams
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    owner_id UUID REFERENCES profiles(id),
    plan TEXT DEFAULT 'free',  -- free, pro, team, business
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Team Members
CREATE TABLE team_members (
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member',  -- admin, member
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (team_id, user_id)
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    repository_url TEXT,
    default_branch TEXT DEFAULT 'main',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scans
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    commit_sha TEXT,
    branch TEXT,
    duration_ms INT,
    files_scanned INT,
    summary JSONB,
    verdict TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Issues (denormalized for query performance)
CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    fingerprint TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    category TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INT NOT NULL,
    message TEXT,
    status TEXT DEFAULT 'open',  -- open, suppressed, fixed
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indices
CREATE INDEX idx_scans_project ON scans(project_id, created_at DESC);
CREATE INDEX idx_issues_scan ON issues(scan_id);
CREATE INDEX idx_issues_fingerprint ON issues(fingerprint);
```

---

# 10. Infrastructure

## 10.1 Local Infrastructure

```
User Machine
├── qodacode CLI (Python)
│   └── .qodacode/
│       ├── config.json         # User configuration
│       ├── suppressions.json   # Suppressed issues
│       └── cache/
│           ├── index.json      # Cache index
│           └── results/        # Cached scan results
│
├── Gitleaks Binary
│   └── ~/.qodacode/bin/gitleaks
│
└── Semgrep (pip installed)
    └── ~/.local/bin/semgrep
```

## 10.2 Cloud Infrastructure (Dashboard)

```
┌─────────────────────────────────────────────────────────────────┐
│                         VERCEL                                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌─────────────────────┐              │
│  │    Next.js App      │  │    Edge Functions    │              │
│  │    (Dashboard)      │  │    (API Routes)      │              │
│  └──────────┬──────────┘  └──────────┬──────────┘              │
│             │                        │                          │
└─────────────┼────────────────────────┼──────────────────────────┘
              │                        │
              ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        SUPABASE                                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL    │  │   Auth          │  │   Realtime      │ │
│  │   (Database)    │  │   (GitHub OAuth)│  │   (Webhooks)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │   Storage       │  │   Edge Functions│                      │
│  │   (Reports)     │  │   (Background)  │                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │     Stripe      │  │     Resend      │  │     Slack       │ │
│  │   (Payments)    │  │    (Email)      │  │   (Webhooks)    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 10.3 CI/CD Infrastructure

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install build twine
      - run: python -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}

  build-npm:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          registry-url: 'https://registry.npmjs.org'
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}

  build-binaries:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install pyinstaller
      - run: pyinstaller --onefile qodacode/cli.py
      - uses: actions/upload-artifact@v4
        with:
          name: qodacode-${{ matrix.os }}
          path: dist/
```

## 10.4 Distribution Strategy

| Method | Command | Target Audience |
|--------|---------|-----------------|
| **PyPI** | `pip install qodacode` | Python developers |
| **pipx** | `pipx install qodacode` | CLI users (isolated) |
| **npm** | `npx qodacode` | JavaScript developers |
| **Homebrew** | `brew install qodacode` | macOS power users |
| **GitHub Releases** | Direct download | CI/CD, Windows |
| **Docker** | `docker run qodacode` | Container workflows |

---

# 11. Security & Compliance

## 11.1 Security Principles

1. **Local-First** — Code never leaves the machine unless user opts-in
2. **No Telemetry** — Zero usage tracking in CLI
3. **Secrets in Memory Only** — API keys never written to disk (except encrypted config)
4. **Minimal Permissions** — Only read access to source code

## 11.2 Threat Model

| Threat | Mitigation |
|--------|------------|
| API key exposure | Stored in OS keychain or encrypted config |
| Malicious rules | Rules are code-reviewed, signed |
| Supply chain attack | Dependencies pinned, Dependabot enabled |
| Man-in-the-middle | All API calls over HTTPS |
| Code exfiltration | Local-only by default, opt-in cloud sync |

## 11.3 Dashboard Security

| Control | Implementation |
|---------|----------------|
| Authentication | GitHub OAuth via Supabase Auth |
| Authorization | Row-level security (RLS) in Supabase |
| Data encryption | TLS in transit, AES-256 at rest |
| Session management | JWT with 7-day refresh tokens |
| Rate limiting | Vercel Edge + Supabase RLS |

## 11.4 Compliance Roadmap

| Standard | Status | Timeline |
|----------|--------|----------|
| GDPR | Compliant by design (local-first) | v1.0 |
| SOC2 Type I | Not required for current market | v2.0+ |
| SOC2 Type II | Future enterprise requirement | v3.0+ |
| HIPAA | Not applicable | N/A |

---

# 12. Roadmap & Milestones

## 12.1 Release Timeline

```
2026
│
├── Q1 (Jan-Mar)
│   ├── v0.2.0 - Solid Foundation ────────────── Week 2-3 ✅
│   ├── v0.3.0 - The Security MCP ────────────── Week 4-6 ✅
│   ├── v0.4.0 - Fastest Scanner ─────────────── Week 7-9 ✅
│   ├── v0.5.0 - Technical Moat (Typosquatting)─ Week 10 ✅
│   │   ├── Typosquatting detection ✅
│   │   ├── CLI: qodacode typosquat ✅
│   │   └── MCP: check_typosquatting ✅
│   │
│   └── v0.6.0 - Agentic Security ────────────── Week 11-12 ⬅️ CURRENT
│       ├── Enhanced fix_issue (smarter patches)
│       ├── Context awareness (test vs prod)
│       ├── AI code pattern detection
│       └── AGENT-002: Prompt injection detection
│
├── Q2 (Apr-Jun)
│   ├── v0.7.0 - License Compliance + Dashboard── Week 13-16
│   │   ├── License detection (GPL, AGPL, etc.)
│   │   ├── check_licenses MCP tool
│   │   └── Dashboard MVP (scan history)
│   └── v1.0.0 - Enterprise for Everyone ─────── Week 17-20
│
├── Q3 (Jul-Sep)
│   ├── v1.1.0 - GitHub App ──────────────────── Week 21-24
│   └── v1.2.0 - Custom Rules Marketplace ────── Week 25-28
│
└── Q4 (Oct-Dec)
    ├── v1.3.0 - More Languages (Go, Rust, Java)
    ├── v1.4.0 - AI Auto-Fix
    └── v2.0.0 - Enterprise Features

NOTE: v0.5.0 "Native Rules Engine" (50+ reglas) SKIPPED.
      Reason: 14 propias + 3400 de Gitleaks/Semgrep es suficiente.
      El moat real está en typosquatting/licenses, no en más reglas.
```

## 12.2 Milestone Details

### v0.2.0 — "Solid Foundation"

**Goal:** Everything that exists works perfectly.

| Deliverable | Description | Success Metric |
|-------------|-------------|----------------|
| Dead code removal | Remove Memory, LSP stub, login | 0 unused code |
| Watch mode stable | No crashes, proper debouncing | 24h run without crash |
| CI verification | Test in real GitHub Actions | Passing in 3 repos |
| Performance baseline | Document current benchmarks | Published numbers |
| Error handling | Graceful engine failures | Works without Semgrep |

### v0.3.0 — "The Security MCP"

**Goal:** Be THE MCP for security in Claude Code.

| Deliverable | Description | Success Metric |
|-------------|-------------|----------------|
| MCP bulletproof | All tools tested exhaustively | 100% test coverage |
| scan_diff tool | Scan changed files only | <100ms typical |
| fix_issue tool | Return fix suggestions | AI can apply |
| Claude Code docs | Step-by-step setup | 30-second onboarding |
| Cursor docs | Step-by-step setup | 30-second onboarding |

### v0.4.0 — "Fastest Scanner"

**Goal:** Be measurably faster than competition.

| Deliverable | Description | Success Metric |
|-------------|-------------|----------------|
| Diff-aware scanning | Git-based change detection | Only scan changes |
| Result caching | Hash-based cache | 90% cache hit rate |
| Parallel execution | Concurrent engines | 2x speedup |
| <100ms diff scans | Target performance | Verified in benchmarks |
| Public benchmarks | vs Snyk, Sonar, Semgrep | Published comparison |

### v0.5.0 — "Native Rules Engine"

**Goal:** Reduce dependency on external engines.

| Deliverable | Description | Success Metric |
|-------------|-------------|----------------|
| 50+ AST rules | Security, robustness, maintainability | All OWASP Top 10 |
| Basic taint tracking | Source-sink analysis | Detect SQL injection flows |
| Go support | Tree-sitter Go | All rules ported |
| Rust support | Tree-sitter Rust | All rules ported |
| Custom rules API | User-defined rules | YAML-based DSL |

### v1.0.0 — "Enterprise for Everyone"

**Goal:** Paid features that justify Team tier.

| Deliverable | Description | Success Metric |
|-------------|-------------|----------------|
| Dashboard web | Scan history, trends | Deployed on Vercel |
| GitHub OAuth | One-click signup | <5 seconds to logged in |
| Team management | Invite members | Teams of 50 work |
| Scan history | Last 30 days | Trend charts |
| Slack webhooks | Critical notifications | <1 minute delivery |
| Stripe integration | Pro/Team billing | First paying customer |

### v0.5.0 — "Technical Moat" (Typosquatting) ✅ COMPLETED

**Goal:** Create defensible IP that competitors can't easily replicate.

| Deliverable | Description | Status |
|-------------|-------------|--------|
| Typosquatting detection | Levenshtein + homoglyphs + keyboard proximity | ✅ Done |
| Package database | Top 150 PyPI + 150 NPM packages | ✅ Done |
| Known malicious DB | 30+ confirmed typosquats | ✅ Done |
| CLI: `qodacode typosquat` | Scan dependency files | ✅ Done |
| MCP: `check_typosquatting` | Claude Code integration | ✅ Done |
| Parsers | requirements.txt, package.json, Pipfile, pyproject.toml | ✅ Done |

### v0.6.0 — "Agentic Security"

**Goal:** Make Qodacode the auto-remediation layer for AI coding + detect AI-specific security issues.

| Deliverable | Description | Success Metric |
|-------------|-------------|----------------|
| Enhanced `fix_issue` | Smarter code patches with context | AI applies 80% of fixes |
| Context awareness | test vs production code | 50% less false positives |
| AI code pattern detection | Detect verbose/insecure AI patterns | Flag suspicious patterns |
| **AGENT-002** | Prompt injection detection | Detect user input → eval/exec flows |
| Typosquatting → `full_audit` | Integrate typosquatting into full audit | Unified security scan |

**AGENT-002: Prompt Injection Detection**
```
User Input → LLM Call → Code Execution = VULNERABILITY
                ↓
           Qodacode detects:
           - eval(user_input)
           - exec(llm_response)
           - os.system(prompt_output)
```

**Moved to v0.7.0:**
- License compliance
- `check_licenses` MCP tool

---

## 12.2.A IP & Commercialization Strategy

### Current IP Assessment (Architectural Evaluation)

| Component | IP Value | Defensibility |
|-----------|----------|---------------|
| MCP Server | ⭐⭐⭐ Medium | First-mover advantage, easy to copy |
| CLI + UX | ⭐⭐ Low | UX differentiator, not technical |
| Gitleaks/Semgrep Wrappers | ⭐ None | Anyone can do this |
| Native AST Rules | ⭐⭐ Low | 14 rules vs 3000+ from competition |
| Junior Mode AI | ⭐⭐⭐ Medium | Good UX, but LLMs can replicate |

**Cold reality**: Currently we're an aggregator with good UX, not a technical innovator.

### What Creates Real Moat

| Feature | Effort | Defensibility | Why It's Moat |
|---------|--------|---------------|---------------|
| Typosquatting Detection | 2-3 days | ⭐⭐⭐⭐ High | Few have it, requires own database |
| License Compliance | 1 week | ⭐⭐⭐ Medium | Enterprise wants this, not trivial |
| Taint Analysis (Own) | 1-2 months | ⭐⭐⭐⭐⭐ Very High | True technical moat, hard to replicate |
| Context Awareness | 1 week | ⭐⭐⭐ Medium | Reduces false positives dramatically |

### Open Core Model

```
┌─────────────────────────────────────────────────────────────┐
│                     OPEN SOURCE (FREE)                       │
├─────────────────────────────────────────────────────────────┤
│  • Complete CLI (scan, watch, init)                         │
│  • MCP Server (10+ tools)                                   │
│  • Gitleaks + Semgrep + OSV integration                     │
│  • 4000+ security rules                                     │
│  • Interactive TUI                                          │
│  • Pre-commit hooks                                         │
│  • GitHub Actions                                           │
│  • AI Junior Mode (explanations)                            │
│  • ✨ TYPOSQUATTING DETECTION ✨ ("Hallucination Corrector") │
│     → Catches fake packages suggested by AI                 │
│     → 300 curated packages + 30 known malicious             │
│     → CLI: qodacode typosquat                               │
│     → MCP: check_typosquatting                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      PREMIUM (PAID)                          │
├─────────────────────────────────────────────────────────────┤
│  TIER: Pro ($9/dev/month)                                   │
│  • Scan history (30 days)                                   │
│  • Priority support                                         │
│  • Enhanced fix_issue (smarter patches)                     │
├─────────────────────────────────────────────────────────────┤
│  TIER: Team ($19/dev/month)                                 │
│  • Web dashboard                                            │
│  • Team management                                          │
│  • Slack/Discord webhooks                                   │
│  • Unlimited history                                        │
│  • License compliance                                       │
│  • Prompt injection detection (AGENT-002)                   │
├─────────────────────────────────────────────────────────────┤
│  TIER: Business ($39/dev/month)                             │
│  • Advanced taint analysis                                  │
│  • Custom rules engine                                      │
│  • SSO/SAML                                                 │
│  • Guaranteed SLA                                           │
│  • Full Agentic Security Suite                              │
└─────────────────────────────────────────────────────────────┘
```

### v0.6.0 — Technical Moat Details

#### Typosquatting Detection (2-3 days)

| Task | Description |
|------|-------------|
| Legitimate package database | Top 10K PyPI, NPM, Go modules |
| Similarity algorithm | Levenshtein + homoglyph detection |
| CLI: `qodacode typosquat` | Scan requirements.txt, package.json |
| MCP Tool: `check_typosquatting` | Claude Code integration |

```python
# Detection examples
"requests" vs "reqeusts"     # Common typo
"numpy" vs "numpyy"          # Extra character
"flask" vs "fIask"           # Homoglyph (capital I vs lowercase l)
"tensorflow" vs "tenserflow" # Vowel confusion
```

**Why it's moat:** Requires maintaining updated database + similarity algorithms. Not trivial to copy.

#### License Compliance (1 week)

| Task | Description |
|------|-------------|
| License parser | SPDX identifiers, LICENSE files |
| Compatibility matrix | GPL vs MIT vs Apache vs proprietary |
| Configurable policies | "Block GPL in commercial code" |
| Compliance report | Exportable PDF for legal |

```yaml
# .qodacode.yml
license_policy:
  allowed: [MIT, Apache-2.0, BSD-3-Clause]
  blocked: [GPL-3.0, AGPL-3.0]
  warn: [LGPL-2.1]
```

**Why it's moat:** Enterprise pays for this. Snyk charges $50K+/year for compliance.

#### Context Awareness (1 week)

| Task | Description |
|------|-------------|
| .env vs code detection | Don't alert secrets in .env.example |
| Test vs production detection | Less strict in /tests/ |
| Framework detection | Specific rules for Django, FastAPI, etc. |
| Project type inference | API, CLI, Library, Web App |

**Why it's moat:** Dramatically reduces false positives. UX differentiator.

---

## 12.3 Dependencies & Blockers

```
v0.2.0 (Foundation)
    │
    └──▶ v0.3.0 (MCP) ──▶ v0.4.0 (Speed)
              │                │
              │                └──▶ v0.5.0 (Rules)
              │                         │
              └─────────────────────────┘
                         │
                         ▼
                    v1.0.0 (Enterprise)
```

| Dependency | Blocker For | Mitigation |
|------------|-------------|------------|
| Tree-sitter bindings | Go/Rust support | Use existing bindings |
| Supabase setup | Dashboard | Can use local-first until ready |
| Stripe approval | Payments | Apply early |
| Semgrep stability | Deep SAST | Graceful degradation |

---

# 13. Success Metrics

## 13.1 North Star Metric

> **Weekly Active Scans (WAS)** — Number of scans run per week

This captures both user adoption and engagement depth.

## 13.2 Key Performance Indicators (KPIs)

### Acquisition Metrics

| Metric | Target (v1.0) | Target (v2.0) |
|--------|---------------|---------------|
| GitHub Stars | 1,000 | 5,000 |
| PyPI Downloads/month | 5,000 | 25,000 |
| npm Downloads/month | 2,000 | 10,000 |
| MCP Server Installations | 500 | 2,500 |

### Activation Metrics

| Metric | Target |
|--------|--------|
| Time to first scan | <30 seconds |
| Scans in first session | 3+ |
| Return within 7 days | 40% |

### Engagement Metrics

| Metric | Target |
|--------|--------|
| Weekly Active Scans | 10,000 |
| Scans per user per week | 15+ |
| Watch mode usage | 30% of users |
| MCP tool calls per session | 5+ |

### Revenue Metrics (Post v1.0)

| Metric | Target Year 1 |
|--------|---------------|
| Free users | 10,000 |
| Pro conversions | 200 (2%) |
| Team conversions | 50 teams |
| Annual Recurring Revenue | $135,600 |
| Monthly Recurring Revenue | $11,300 |

### Quality Metrics

| Metric | Target |
|--------|--------|
| False positive rate | <5% |
| CLI crash rate | <0.1% |
| User-reported bugs/month | <10 |
| Median scan time (50 files) | <800ms |
| Median diff scan time | <100ms |

## 13.3 Milestone Success Criteria

| Milestone | Success Criteria |
|-----------|------------------|
| v0.2.0 | 0 known bugs, 100% test pass, benchmarks published |
| v0.3.0 | MCP documented, 10 beta users on Claude Code |
| v0.4.0 | <100ms diff scans verified, benchmarks show 10x vs Snyk |
| v0.5.0 | 50+ rules, OWASP Top 10 covered |
| v0.6.0 | Typosquatting DB 10K+, License compliance working |
| v1.0.0 | First 10 paying teams, $1,000 MRR |

---

# 14. Risk Analysis

## 14.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tree-sitter binding issues | Medium | High | Fallback to regex, multiple binding options |
| Semgrep breaking changes | Medium | Medium | Pin versions, graceful degradation |
| Performance doesn't meet targets | Low | High | Profiling early, caching aggressive |
| MCP protocol changes | Medium | High | Close Anthropic relationship, quick adaptation |
| Cross-platform issues (Windows) | High | Medium | WSL-first, test matrix |

## 14.2 Market Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Claude Code adds built-in security | Medium | Critical | Differentiate on speed, local-first |
| Cursor builds competing feature | Medium | High | MCP lock-in, community rules |
| Snyk releases free tier | Low | High | Speed moat, developer UX moat |
| AI coding adoption slows | Low | Critical | Expand to general dev tools |

## 14.3 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| No paying customers | Medium | Critical | Validate pricing early, iterate |
| Support burden too high | Medium | Medium | Self-service docs, community |
| Competitor copies features | High | Medium | Speed of execution, community moat |
| Founder burnout | Medium | Critical | Sustainable pace, automate ops |

## 14.4 Risk Monitoring

```
Weekly Risk Review:
├── Technical blockers
├── User feedback themes
├── Competitor movements
├── Performance metrics
└── Support volume
```

---

# 15. Appendix

## 15.1 Glossary

| Term | Definition |
|------|------------|
| **AST** | Abstract Syntax Tree — structured representation of code |
| **MCP** | Model Context Protocol — Anthropic's AI tool interface |
| **SAST** | Static Application Security Testing |
| **DAST** | Dynamic Application Security Testing |
| **SCA** | Software Composition Analysis |
| **CVE** | Common Vulnerabilities and Exposures |
| **OWASP** | Open Web Application Security Project |
| **Taint Tracking** | Data flow analysis from sources to sinks |
| **Tree-sitter** | Incremental parsing library |

## 15.2 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [MCP Protocol Spec](https://modelcontextprotocol.io/)
- [Tree-sitter Documentation](https://tree-sitter.github.io/)
- [Semgrep Rules](https://semgrep.dev/explore)
- [Gitleaks](https://github.com/gitleaks/gitleaks)

## 15.3 Competitive Analysis Links

- [Snyk Pricing](https://snyk.io/plans/)
- [SonarQube Editions](https://www.sonarsource.com/products/sonarqube/)
- [CodeRabbit Pricing](https://coderabbit.ai/pricing)
- [Semgrep Pricing](https://semgrep.dev/pricing)

## 15.4 Performance Benchmarks (Phase 3 Results)

**Benchmark Environment:** macOS Darwin 25.2.0, Python 3.12

### Scanner Performance (AST Only)

| Files | Cold Scan | Warm Scan (cached) | Cache Speedup |
|-------|-----------|-------------------|---------------|
| 10 | 82ms | 0.5ms | 164x |
| 50 | **369ms** | 6.5ms | 56x |
| 100 | 742ms | 12ms | 61x |

### PRD Targets vs Actual

| Target | PRD Requirement | Actual | Status |
|--------|-----------------|--------|--------|
| Full scan (50 files) | <1 second | **369ms** | ✅ MET |
| Diff scan (5 files) | <100ms | **12ms** | ✅ MET |
| Cache speedup | >10x | **56x** | ✅ EXCEEDED |

### Key Optimizations Applied

1. **SHA256 file hash caching** - Skip re-scanning unchanged files
2. **In-memory AST cache** - Avoid re-parsing unchanged files
3. **Parallel file scanning** - ThreadPoolExecutor for file processing
4. **Parallel engine execution** - Orchestrator runs AST + Gitleaks + Semgrep concurrently

---

## 15.5 Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-01-19 | Nelson | Initial vision |
| 1.0.0 | 2026-01-20 | Nelson + Claude | Complete PRD v2 |
| 1.1.0 | 2026-01-20 | Nelson + Claude | Added v0.6.0 Technical Moat, IP Strategy, Open Core Model |
| 1.2.0 | 2026-01-20 | Nelson + Claude | Phase 3 completed: Cache, Parallel Orchestrator, Benchmarks |
| 1.3.0 | 2026-01-20 | Nelson + Claude | Phase 4 completed: Typosquatting (CLI + MCP), Interface Strategy |
| 1.4.0 | 2026-01-20 | Nelson + Claude | v0.6.0 adjusted: Typosquatting FREE, License→v0.7.0, +AGENT-002 |

---

# Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Technical Lead | | | |
| Engineering | | | |

---

*This document is the source of truth for Qodacode Level 2 development. All implementation decisions should reference this PRD.*
