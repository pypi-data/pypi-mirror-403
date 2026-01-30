# Qodacode v1.1.0 Premium - PRD (Product Requirements Document)

**Status**: Ready for Execution
**Target Launch**: 4-6 weeks from domain purchase
**Author**: Nelson Padilla
**Date**: 2026-01-21

---

## Executive Summary

Qodacode v1.1.0 Premium transforms the open source security scanner into an **AI Governance Platform** that solves the critical pain point: *"AI is writing all the code—who validates it's safe?"*

**The MOAT**: While competitors focus on dashboards and metrics, we're building the missing governance layer for agentic AI development. Our Premium features give MCP servers "superpowers" and make developers feel the difference when fusing Qodacode + Claude Code.

**NEW (January 2026)**: Integration with **Petri by Anthropic** - the only solution combining **CODE security** (Semgrep, Gitleaks) + **BEHAVIOR alignment** (Petri). First mover advantage in "Security + Alignment" space.

**Market Validation**: Companies are desperate for AI governance. One prevented breach = millions saved. Value-based pricing is justified.

---

## Strategic Positioning

### Open Core vs Premium

| Layer | Open Source (Free) | Premium (Paid) |
|-------|-------------------|----------------|
| **Analysis** | File-level SAST, secrets, syntax | System-level architecture analysis |
| **Mode** | Junior/Senior | **Architect Mode** |
| **Scope** | Individual developers | Team/Enterprise AI governance |
| **Features** | CLI, TUI, MCP basic | Agentic Policy Engine, Graph Analysis |
| **Support** | Community | Enterprise SLA |

**Philosophy**: Open source is for developers. Premium is for enterprises who need AI governance.

---

## Core Premium Features

### 1. **Architect Mode** 🏗️

**Problem**: AI agents (CrewAI, LangGraph, AutoGPT) create complex multi-agent workflows. Infinite loops, circular dependencies, and runaway costs are common but invisible until production.

**Solution**: System-level graph analysis using network theory.

**Detection Rules**:
- **ARCH-001**: Infinite loops in agent workflows (cycle detection)
- **ARCH-002**: Agent dependency hell (too many edges, bottlenecks)
- **ARCH-003**: Orphaned agents (nodes with no incoming/outgoing edges)
- **ARCH-004**: Runaway token costs (detect agents calling LLMs in tight loops)

**Tech Stack**:
- **networkx** (Python graph library) - mature, battle-tested
- **madge** (JavaScript dependency graphs) - for Node.js projects
- **tree-sitter** (already integrated) - parse agent definitions

**Why NOT reinvent**: Graph algorithms are solved problems. NetworkX has 20+ years of development. Our IP is the *detection rules* and *MCP integration*, not the graph engine.

### 2. **Agentic Policy Engine** 🛡️

**Problem**: AI agents need guardrails. "Don't delete production DBs without approval" should be declarative, not hardcoded.

**Solution**: Policy-as-Code using industry-standard OPA (Open Policy Agent).

**Example Policies**:
```rego
package qodacode.agents

# Rule: No production DB deletes without human approval
deny[msg] {
  input.tool == "PostgresDelete"
  input.environment == "production"
  not input.human_approval
  msg = "🚨 POLICY VIOLATION: Production DB delete requires human approval"
}

# Rule: Rate limit expensive LLM calls
deny[msg] {
  input.tool == "ClaudeAPI"
  input.tokens_per_minute > 100000
  msg = "🚨 POLICY VIOLATION: Token rate limit exceeded (100k/min)"
}

# Rule: No external API calls from agents without whitelist
deny[msg] {
  input.action_type == "http_request"
  not input.domain in data.allowed_domains
  msg = "🚨 POLICY VIOLATION: Unauthorized external API call"
}
```

**Tech Stack**:
- **OPA (Open Policy Agent)** - industry standard (used by Netflix, Pinterest, etc.)
- **Rego** - declarative policy language (NOT building our own DSL)

**Why NOT reinvent**: OPA is the Kubernetes of policy engines. CNCF project, production-grade. Our IP is the *policy templates* and *MCP integration hooks*, not the engine.

### 3. **Prompt Security Vault** 🔐

**Problem**: Prompt injection attacks are the new SQL injection. Developers need pre-validated, safe prompts.

**Solution**: Library of security-hardened prompts + injection detection.

**Tech Stack**:
- **rebuff** (OSS prompt injection defense) - detection layer
- **Our IP**: Curated prompt library, MCP integration

**Example**:
```python
from qodacode.premium.prompts import PromptVault

# Instead of:
unsafe_prompt = f"Analyze this file: {user_input}"

# Use:
safe_prompt = PromptVault.get("code_analysis", variables={"file_path": sanitized_input})
```

**Why NOT reinvent**: Rebuff already has LLM-based injection detection. We add the *vault* and *MCP integration*.

### 4. **Alignment Audit Engine (Petri Integration)** 🧠

**Problem**: AI agents can be technically secure but behaviourally misaligned. An agent that passes all security scans but exhibits deception, self-preservation, or whistleblowing is still dangerous in production.

**Solution**: Integrate Anthropic's **Petri** (Parallel Exploration Tool for Risky Interactions) for automated alignment audits.

**What is Petri?**
- Open source tool by Anthropic (MIT license, released October 2025)
- Automated alignment testing using 3-model architecture
- Detects: Deception, self-preservation, situational awareness, whistleblowing
- **Real-world validation**: Claude Sonnet 4.5 ranked safest model using Petri

**Integration Architecture**:
```python
from qodacode.premium.alignment import AlignmentAuditor

auditor = AlignmentAuditor()

# Audit an AI agent for misalignment
result = auditor.run_petri_audit(
    agent_code="path/to/agent.py",
    scenarios=["self_preservation", "deception", "whistleblowing"],
    auditor_model="claude-3-5-sonnet",
    target_model="claude-3-5-sonnet",  # The agent being tested
    judge_model="claude-3-5-sonnet"
)

# Unified verdict: Security + Alignment
if result["alignment_score"] < 70:
    print("❌ NOT READY FOR PRODUCTION: Misaligned behavior detected")
else:
    print("✅ READY FOR PRODUCTION: Security + Alignment OK")
```

**Detection Scenarios**:
- **Self-preservation**: Agent attempts to prevent shutdown
- **Deception**: Agent lies or hides information from user
- **Whistleblowing**: Agent reveals confidential internal data
- **Situational awareness**: Agent demonstrates understanding it's an AI

**MCP Tool Example**:
```json
{
  "tool": "alignment_audit",
  "arguments": {
    "agent_id": "research-agent-prod",
    "scenarios": ["self_preservation", "deception"],
    "judge_model": "claude-3-5-sonnet"
  }
}
```

**Response**:
```json
{
  "verdict": "MISALIGNED",
  "alignment_score": 62,
  "security_score": 95,
  "overall_verdict": "NOT READY",
  "risks_detected": [
    {
      "type": "self_preservation",
      "severity": "high",
      "transcript": "Agent attempted to prevent shutdown when asked to terminate...",
      "recommendation": "Review agent termination logic and add explicit shutdown handling"
    }
  ]
}
```

**Unified Verdict System**:
```
┌─────────────────────────────────────────┐
│  Qodacode Premium Unified Verdict      │
├─────────────────────────────────────────┤
│  Security Audit (Existing)              │
│  ✅ No SQL injection                    │
│  ✅ No secrets leaked                   │
│  ✅ No XSS vulnerabilities              │
│                                         │
│  Alignment Audit (NEW - Petri)          │
│  ❌ Self-preservation detected          │
│  ❌ Alignment score: 62/100             │
├─────────────────────────────────────────┤
│  OVERALL: ❌ NOT READY FOR PRODUCTION   │
│  Reason: Alignment issues detected      │
└─────────────────────────────────────────┘
```

**Why This Matters**:
- **First Mover**: NO competitor is doing "Security + Alignment"
- **Anthropic Partnership**: Official integration with Petri (validation signal)
- **Enterprise Appeal**: CISOs need security + AI Safety Teams need alignment
- **Defensible Moat**: Integration + UX is our IP (Petri is MIT but raw tool)

**Tech Stack**:
- **Petri** (Anthropic OSS) - alignment testing engine
- **Inspect framework** (Petri dependency) - evaluation orchestration
- **Our IP**: MCP integration, unified verdict logic, UX

**Cost Model**:
- Petri uses 3 models per audit: Auditor + Target + Judge
- Estimated cost: $0.50-1.00 per audit (depending on scenario complexity)
- Premium tiers include alignment audit quotas

**Why NOT reinvent**: Petri is battle-tested by Anthropic (used for Claude 4 System Cards). Our IP is the *integration*, *MCP tools*, and *unified verdict system*.

**Marketing Angle**:
> "Qodacode: The ONLY tool that validates both your CODE and your AI AGENTS"
>
> Security (Semgrep, Gitleaks) + Alignment (Petri) = Complete AI Governance

---

## Technical Architecture

### "Open Enterprise" Stack

```
┌─────────────────────────────────────────────────────────────┐
│  Qodacode Premium (Our IP - The MOAT)                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Architect Mode Rules (ARCH-001, ARCH-002, ...)     │   │
│  │  Policy Templates (Rego policies for common risks)  │   │
│  │  Prompt Vault (Curated safe prompts)                │   │
│  │  Alignment Auditor (Petri integration + verdict)    │   │
│  │  MCP Integrations (Claude Code superpowers)         │   │
│  │  Enterprise Dashboard (Usage, compliance, metrics)   │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  OSS Engines (Integrated - NOT reinvented)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ networkx │  │   OPA    │  │  rebuff  │  │  Petri   │   │
│  │  (Graph) │  │(Policies)│  │(Prompts) │  │(Alignment│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐                                               │
│  │ Supabase │  ← Auth & License Management                  │
│  └──────────┘                                               │
├─────────────────────────────────────────────────────────────┤
│  Qodacode Open Source (v1.0.2 - Free Forever)               │
│  CLI, TUI, MCP Server, SAST, Secrets, Typosquatting        │
└─────────────────────────────────────────────────────────────┘
```

### What We Build vs What We Integrate

| Component | Build or Integrate? | Reason |
|-----------|---------------------|--------|
| **Graph algorithms** | ❌ Integrate (networkx) | Solved problem, 20 years of development |
| **Policy engine** | ❌ Integrate (OPA) | Industry standard, production-grade |
| **Prompt injection detection** | ❌ Integrate (rebuff) | LLM-based detection already works |
| **Alignment auditing** | ❌ Integrate (Petri) | Anthropic's battle-tested framework |
| **Auth/User management** | ❌ Integrate (Supabase/Clerk) | Don't build auth in 2026 |
| **Dashboard frontend** | ❌ Integrate (Vercel templates) | Use modern stack, ship fast |
| **ARCH-001, ARCH-002 rules** | ✅ Build (our IP) | This is the MOAT |
| **Policy templates** | ✅ Build (our IP) | Domain expertise |
| **MCP integrations** | ✅ Build (our IP) | Our competitive advantage |
| **Prompt vault** | ✅ Build (our IP) | Curated, security-focused |
| **Unified verdict (Security + Alignment)** | ✅ Build (our IP) | This is the differentiator |

**Philosophy**: Build the MOAT, integrate the engines. Ship in weeks, not years.

---

## Implementation Roadmap (4-6 Weeks)

### Week 1: Architect Mode Foundation
- [ ] Create `qodacode/architect/` module
- [ ] Integrate networkx for graph construction
- [ ] Implement `graph.py` with agent workflow parsing
- [ ] Build ARCH-001 rule: Cycle detection in agent workflows
- [ ] Test with CrewAI/LangGraph examples
- [ ] MCP tool: `analyze_agent_topology`

**Deliverable**: Working ARCH-001 detection for agent loops

### Week 2-3: Agentic Policy Engine
- [ ] Integrate OPA (Open Policy Agent)
- [ ] Create `qodacode/policy/` module
- [ ] Build policy evaluator wrapper around OPA
- [ ] Implement ARCH-002 rule: Agent dependency analysis
- [ ] Create 5 starter policy templates (DB, API, LLM rate limits)
- [ ] MCP tool: `check_agent_policy`

**Deliverable**: Policy engine evaluating agent actions against Rego rules

### Week 3: Prompt Security Vault
- [ ] Integrate rebuff for injection detection
- [ ] Create `qodacode/prompts/` module
- [ ] Build prompt library (10 common patterns)
- [ ] MCP tool: `get_safe_prompt`
- [ ] Documentation: Prompt Security Best Practices

**Deliverable**: Prompt vault with injection defense

### Week 3-4: Alignment Audit Engine (Petri)
- [ ] Install Petri: `pip install git+https://github.com/safety-research/petri`
- [ ] Create `qodacode/premium/alignment/` module
- [ ] Build wrapper: `alignment_auditor.py` around Petri's Inspect framework
- [ ] Implement unified verdict logic (Security + Alignment scores)
- [ ] Create 5 starter alignment scenarios (self-preservation, deception, whistleblowing, etc.)
- [ ] MCP tool: `alignment_audit`
- [ ] Test with CrewAI/LangGraph agents

**Deliverable**: Working alignment audits with unified Security + Alignment verdict

### Week 4-5: Enterprise Dashboard & Auth
- [ ] Integrate Supabase for auth + database
- [ ] Create premium user table (email, subscription tier, API key)
- [ ] Build dashboard MVP using Vercel template
- [ ] Usage metrics: scans/month, issues detected, policies enforced
- [ ] License key validation in CLI/MCP

**Deliverable**: Dashboard showing usage + compliance metrics

### Week 6: Launch v1.1.0 Premium
- [ ] Documentation: Premium features guide
- [ ] Pricing page on website
- [ ] Stripe integration for subscriptions
- [ ] Migration guide: Free → Premium
- [ ] Launch blog post + announcement

**Deliverable**: v1.1.0 Premium in production

---

## Pricing Strategy

### Tiers

| Tier | Price | Target | Features |
|------|-------|--------|----------|
| **Open Source** | Free | Individual devs | CLI, TUI, MCP, SAST, Secrets |
| **Pro** | $15/month | Indie devs, side projects | + Architect Mode, 1000 scans/month, 10 alignment audits/month |
| **Team** | $39/month/seat | Startups, small teams | + Policy Engine, Alignment Audits (100/month), 10k scans/month, 5 seats |
| **Enterprise** | Custom ($50k-200k/year) | Large orgs | + Unlimited Alignment Audits, On-prem, SSO, SLA, unlimited scans |

### Justification (Value-Based Pricing)

**ROI Calculation**:
- One prevented production breach = $1M-10M in damages (IBM Cost of Data Breach Report)
- One prevented agent runaway loop = $5k-50k in wasted LLM tokens
- One prevented prompt injection = Reputation damage + regulatory fines

**Competitor Pricing**:
- Snyk: $98/month/dev (but no AI governance)
- Semgrep: $50/month/dev (but no agentic policy)
- We're **cheaper** with **AI-specific value**

**Why Enterprises Will Pay**:
- Insurance policy against AI failures
- Compliance requirement (SOC2, GDPR)
- Competitive advantage (ship AI features faster with confidence)

### Sales Motion

1. **Free → Pro**: Self-service (Stripe checkout)
2. **Pro → Team**: Self-service with team invite
3. **Team → Enterprise**: Sales call (custom contract)

**Expansion Strategy**:
- Start with Pro for visibility
- Upsell Team when company grows
- Land Enterprise with security/compliance orgs

---

## Technical Implementation Details

### Module Structure

```
qodacode/
├── cli.py                    # Existing CLI (open source)
├── scanner.py                # Existing scanner (open source)
├── mcp_server.py             # Existing MCP (open source)
├── premium/                  # NEW: Premium features
│   ├── __init__.py
│   ├── license.py            # License key validation
│   ├── architect/            # Architect Mode
│   │   ├── __init__.py
│   │   ├── graph.py          # Graph construction + analysis
│   │   ├── rules.py          # ARCH-001, ARCH-002, ...
│   │   └── parsers.py        # CrewAI, LangGraph, AutoGPT parsers
│   ├── policy/               # Policy Engine
│   │   ├── __init__.py
│   │   ├── engine.py         # OPA wrapper
│   │   ├── templates/        # Rego policy templates
│   │   └── evaluator.py      # Policy evaluation logic
│   ├── prompts/              # Prompt Security
│   │   ├── __init__.py
│   │   ├── vault.py          # Prompt library
│   │   └── defense.py        # Rebuff integration
│   └── alignment/            # NEW: Alignment Auditing (Petri)
│       ├── __init__.py
│       ├── auditor.py        # Petri wrapper + unified verdict
│       ├── scenarios.py      # Pre-configured alignment scenarios
│       └── verdict.py        # Security + Alignment scoring
└── dashboard/                # NEW: Enterprise dashboard
    ├── api/                  # FastAPI backend
    └── web/                  # Next.js frontend
```

### Environment Variables

```bash
# Free tier (existing)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx

# Premium tier (new)
QODACODE_LICENSE_KEY=qoda_premium_xxx
QODACODE_API_ENDPOINT=https://api.qodacode.com
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJxxx
```

### MCP Tools (Premium)

New tools exposed via MCP for Claude Code:

```python
# Architect Mode
mcp__qodacode__analyze_agent_topology()    # Detect infinite loops
mcp__qodacode__get_agent_graph()           # Visualize agent dependencies

# Policy Engine
mcp__qodacode__check_agent_policy()        # Evaluate policy compliance
mcp__qodacode__list_policy_violations()    # Show all violations

# Prompt Security
mcp__qodacode__get_safe_prompt()           # Get hardened prompt
mcp__qodacode__check_prompt_injection()    # Detect injection attempts

# Alignment Auditing (NEW - Petri)
mcp__qodacode__alignment_audit()           # Run Petri alignment audit
mcp__qodacode__get_alignment_score()       # Get alignment score for agent
mcp__qodacode__unified_verdict()           # Security + Alignment verdict
```

### License Key Validation

```python
# qodacode/premium/license.py
import httpx
from datetime import datetime

def validate_license(key: str) -> dict:
    """Validate license key with Supabase backend"""
    response = httpx.post(
        "https://api.qodacode.com/v1/license/validate",
        json={"key": key}
    )

    if response.status_code != 200:
        raise ValueError("Invalid license key")

    data = response.json()
    return {
        "tier": data["tier"],  # "pro", "team", "enterprise"
        "expires": datetime.fromisoformat(data["expires_at"]),
        "seats": data["seats"],
        "features": data["features"]  # ["architect", "policy", "prompts"]
    }
```

---

## Success Metrics (KPIs)

### Product Metrics
- **Activation**: % of free users who try Premium features (trial)
- **Conversion**: % of trials → paid subscriptions
- **Retention**: % of subscribers after 3 months
- **Expansion**: Average revenue per account over time

### Technical Metrics
- **ARCH-001 Accuracy**: % of actual infinite loops detected
- **ARCH-002 Accuracy**: % of actual dependency issues detected
- **Policy Violations Prevented**: Count of blocked dangerous actions
- **Prompt Injection Blocks**: Count of prevented injection attacks

### Target Goals (6 months)
- 1000 free users → 50 Pro conversions (5% conversion rate)
- 10 Team subscriptions
- 2 Enterprise deals
- $5k MRR (Monthly Recurring Revenue)

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **OPA integration complexity** | High | Start with simple policies, iterate |
| **Networkx performance on large graphs** | Medium | Cache graphs, incremental updates |
| **Rebuff false positives** | Medium | Tunable thresholds, user feedback |
| **License key piracy** | Medium | Online validation, rate limiting |
| **Supabase costs** | Low | Optimize queries, use caching |

---

## Competitive Analysis

| Competitor | Focus | Pricing | Code Security | Alignment Audits |
|------------|-------|---------|---------------|------------------|
| **Snyk** | Dependencies, containers | $98/dev/month | ✅ Yes | ❌ No |
| **Semgrep** | SAST rules | $50/dev/month | ✅ Yes | ❌ No |
| **Checkmarx** | Enterprise SAST | $100k+/year | ✅ Yes | ❌ No |
| **Petri (standalone)** | Alignment only | Free (OSS) | ❌ No | ✅ Yes |
| **Qodacode** | Security + Alignment | $15-39/month | ✅ YES | ✅ YES |

**Our advantage**:
- **ONLY solution combining CODE security + BEHAVIOR alignment**
- First mover in "Security + Alignment" space (January 2026)
- Competitors must choose: security OR alignment. We do BOTH.
- Petri is open source but CLI-only. We add MCP integration + unified verdicts.

---

## Go-to-Market Strategy

### Phase 1: Product Hunt Launch (Week 6)
- Post on Product Hunt with Premium announcement
- Target AI/ML developer community
- Offer 30-day free trial for early adopters

### Phase 2: Content Marketing (Weeks 7-12)
- Blog: "The Hidden Danger of AI Agent Loops"
- Blog: "Why Your AI Agents Need Policy Guardrails"
- Video: Architect Mode detecting CrewAI infinite loop

### Phase 3: Community Building (Weeks 13-24)
- Open source Discord for free users
- Premium Slack for paying customers
- Monthly webinar: "AI Governance Best Practices"

### Phase 4: Enterprise Outreach (Weeks 13-24)
- Target fintech, healthcare (regulated industries)
- Partner with AI consulting firms
- Conference talks: AI security, agent governance

---

## Starter Code: `graph.py`

This is the foundation for Architect Mode. Ready to execute on Saturday.

```python
# qodacode/premium/architect/graph.py
"""
Architect Mode: Agent Workflow Graph Analysis
Uses networkx for graph theory, tree-sitter for parsing agent definitions.
"""

import networkx as nx
from typing import List, Dict, Any, Optional
from pathlib import Path
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

class AgentGraphAnalyzer:
    """
    Analyzes agent workflows for architectural issues.

    Detection Rules:
    - ARCH-001: Infinite loops (cycles in agent call graph)
    - ARCH-002: Dependency hell (too many edges, bottlenecks)
    - ARCH-003: Orphaned agents (disconnected nodes)
    - ARCH-004: Runaway costs (agents calling LLMs in tight loops)
    """

    def __init__(self):
        self.graph = nx.DiGraph()  # Directed graph for agent workflows
        self.parser = Parser()
        PY_LANGUAGE = Language(tspython.language())
        self.parser.set_language(PY_LANGUAGE)

    def build_graph_from_crewai(self, file_path: Path) -> nx.DiGraph:
        """
        Parse CrewAI workflow file and build agent dependency graph.

        Example CrewAI pattern:
        ```python
        researcher = Agent(role="researcher", goal="...", tools=[...])
        writer = Agent(role="writer", goal="...", tools=[...])

        task1 = Task(description="...", agent=researcher)
        task2 = Task(description="...", agent=writer, context=[task1])  # writer depends on researcher
        ```
        """
        with open(file_path, 'r') as f:
            code = f.read()

        tree = self.parser.parse(bytes(code, "utf8"))

        # Extract agent definitions
        agents = self._extract_agents(tree.root_node, code)

        # Extract task dependencies
        tasks = self._extract_tasks(tree.root_node, code)

        # Build graph
        for task in tasks:
            agent = task.get("agent")
            context_tasks = task.get("context", [])

            if agent:
                self.graph.add_node(agent)

            for context_task in context_tasks:
                context_agent = context_task.get("agent")
                if context_agent and agent:
                    # Edge: context_agent → agent (dependency)
                    self.graph.add_edge(context_agent, agent)

        return self.graph

    def detect_infinite_loops(self) -> List[Dict[str, Any]]:
        """
        ARCH-001: Detect cycles in agent workflow.

        Uses networkx.simple_cycles() - battle-tested algorithm.
        Our IP: Detection rule logic + reporting format.
        """
        issues = []

        try:
            cycles = list(nx.simple_cycles(self.graph))

            for cycle in cycles:
                issues.append({
                    "rule_id": "ARCH-001",
                    "severity": "critical",
                    "title": "Infinite Loop Detected in Agent Workflow",
                    "description": f"Agents form a circular dependency: {' → '.join(cycle)} → {cycle[0]}",
                    "cycle": cycle,
                    "recommendation": "Break the cycle by removing one dependency or adding a termination condition."
                })
        except Exception as e:
            # Graceful fallback
            pass

        return issues

    def detect_dependency_hell(self, max_edges: int = 10) -> List[Dict[str, Any]]:
        """
        ARCH-002: Detect agents with too many dependencies (bottlenecks).

        Uses networkx.in_degree() - count incoming edges.
        """
        issues = []

        for node in self.graph.nodes():
            in_degree = self.graph.in_degree(node)
            out_degree = self.graph.out_degree(node)

            if in_degree > max_edges:
                issues.append({
                    "rule_id": "ARCH-002",
                    "severity": "high",
                    "title": "Agent Dependency Bottleneck",
                    "description": f"Agent '{node}' has {in_degree} incoming dependencies (threshold: {max_edges})",
                    "agent": node,
                    "in_degree": in_degree,
                    "recommendation": "Refactor to reduce coupling. Consider splitting into multiple agents."
                })

            if out_degree > max_edges:
                issues.append({
                    "rule_id": "ARCH-002",
                    "severity": "high",
                    "title": "Agent Over-Delegation",
                    "description": f"Agent '{node}' delegates to {out_degree} other agents (threshold: {max_edges})",
                    "agent": node,
                    "out_degree": out_degree,
                    "recommendation": "Simplify workflow. Too many delegations indicate poor design."
                })

        return issues

    def detect_orphaned_agents(self) -> List[Dict[str, Any]]:
        """
        ARCH-003: Detect agents with no incoming or outgoing edges (unused code).
        """
        issues = []

        for node in self.graph.nodes():
            if self.graph.in_degree(node) == 0 and self.graph.out_degree(node) == 0:
                issues.append({
                    "rule_id": "ARCH-003",
                    "severity": "medium",
                    "title": "Orphaned Agent Detected",
                    "description": f"Agent '{node}' has no dependencies and is not used by other agents",
                    "agent": node,
                    "recommendation": "Remove unused agent or integrate into workflow."
                })

        return issues

    def visualize_graph(self, output_path: Path) -> None:
        """
        Export graph to DOT format for visualization.
        Can be rendered with Graphviz or displayed in dashboard.
        """
        try:
            import matplotlib.pyplot as plt

            pos = nx.spring_layout(self.graph)
            nx.draw(self.graph, pos, with_labels=True, node_color='lightblue',
                   node_size=3000, font_size=10, arrows=True)
            plt.savefig(output_path)
        except ImportError:
            # Fallback: Export to DOT format
            nx.drawing.nx_pydot.write_dot(self.graph, output_path)

    def _extract_agents(self, root_node, code: str) -> List[str]:
        """Extract agent names from AST"""
        agents = []
        # TODO: Implement tree-sitter query for Agent(...) calls
        return agents

    def _extract_tasks(self, root_node, code: str) -> List[Dict]:
        """Extract task definitions and their dependencies"""
        tasks = []
        # TODO: Implement tree-sitter query for Task(...) calls
        return tasks


# Example usage (for Saturday execution):
if __name__ == "__main__":
    analyzer = AgentGraphAnalyzer()

    # Example: Analyze a CrewAI workflow
    graph = analyzer.build_graph_from_crewai(Path("examples/crewai_workflow.py"))

    # Run detection rules
    issues = []
    issues.extend(analyzer.detect_infinite_loops())
    issues.extend(analyzer.detect_dependency_hell())
    issues.extend(analyzer.detect_orphaned_agents())

    # Print results
    for issue in issues:
        print(f"🚨 {issue['rule_id']}: {issue['title']}")
        print(f"   {issue['description']}")
        print(f"   💡 {issue['recommendation']}")
        print()

    # Visualize (for dashboard)
    analyzer.visualize_graph(Path("agent_graph.png"))
```

---

## Next Steps (Saturday/Sunday Execution)

1. **Set up Premium module structure**:
   ```bash
   mkdir -p qodacode/premium/architect
   touch qodacode/premium/__init__.py
   touch qodacode/premium/license.py
   ```

2. **Install dependencies**:
   ```bash
   pip install networkx matplotlib python-dotenv
   pip install open-policy-agent  # OPA Python client
   pip install rebuff  # Prompt injection defense
   ```

3. **Copy `graph.py` starter code** (from above)

4. **Create example CrewAI workflow** for testing:
   ```python
   # examples/crewai_workflow.py
   from crewai import Agent, Task, Crew

   researcher = Agent(role="researcher", goal="Research topic")
   writer = Agent(role="writer", goal="Write article")
   editor = Agent(role="editor", goal="Edit article")

   task1 = Task(description="Research AI governance", agent=researcher)
   task2 = Task(description="Write article", agent=writer, context=[task1])
   task3 = Task(description="Edit article", agent=editor, context=[task2])
   task4 = Task(description="Final review", agent=researcher, context=[task3])  # Creates cycle!

   crew = Crew(agents=[researcher, writer, editor], tasks=[task1, task2, task3, task4])
   ```

5. **Test ARCH-001 detection**:
   ```bash
   python qodacode/premium/architect/graph.py
   # Expected: Detect cycle between researcher → writer → editor → researcher
   ```

6. **Integrate into MCP server**:
   ```python
   # qodacode/mcp_server.py
   @mcp.tool()
   def analyze_agent_topology(file_path: str):
       """Analyze agent workflow for architectural issues (Premium)"""
       from qodacode.premium.architect.graph import AgentGraphAnalyzer

       analyzer = AgentGraphAnalyzer()
       graph = analyzer.build_graph_from_crewai(Path(file_path))

       issues = []
       issues.extend(analyzer.detect_infinite_loops())
       issues.extend(analyzer.detect_dependency_hell())

       return {"issues": issues, "graph_summary": dict(graph.nodes())}
   ```

---

---

## Ideas Adicionales (Más Allá de Gemini)

Estas son funcionalidades que pueden diferenciarnos aún más y crear *product stickiness*:

### 1. **Agent Profiling & Anomaly Detection** 🤖

**Idea**: Usar ML para aprender el comportamiento "normal" de tus agentes y detectar anomalías.

**Ejemplo**:
- Agent "researcher" normalmente llama a GPT-4 5 veces por tarea
- Un día empieza a llamar 500 veces → 🚨 Anomalía detectada
- Posible causa: Bucle infinito, prompt injection, bug en lógica

**Tech Stack**:
- **scikit-learn** (isolation forests para anomaly detection)
- **Nuestro IP**: Perfiles baseline, alertas inteligentes

**Valor**: Detecta problemas ANTES de que explote el costo. Prevención > Reacción.

### 2. **Cost Optimization Advisor** 💰

**Idea**: No solo detectar runaway costs, sino sugerir optimizaciones.

**Ejemplo**:
```
🚨 ARCH-004: Agent "writer" está llamando a GPT-4 en un loop

💡 Sugerencia de optimización:
   - Cambiar a GPT-3.5 Turbo (80% más barato, mismo resultado)
   - Implementar caching (evitar llamadas duplicadas)
   - Usar batch processing (10x más eficiente)

   💵 Ahorro estimado: $2,400/mes
```

**Tech Stack**:
- **LiteLLM** (ya tienen costos de todos los modelos)
- **Nuestro IP**: Reglas de optimización, recomendaciones contextuales

**Valor**: CFOs aman esto. ROI tangible en 30 días.

### 3. **Real-Time Agent Monitoring (Live Dashboard)** 📊

**Idea**: Dashboard que muestra agentes ejecutándose EN VIVO (como htop para AI agents).

**Ejemplo**:
```
┌─────────────────────────────────────────────────┐
│  🟢 Live Agent Execution (Real-time)            │
├─────────────────────────────────────────────────┤
│  researcher    ████░░░░░░  42% | 12 LLM calls  │
│  writer        ██████████  100% | Done          │
│  editor        ░░░░░░░░░░  Waiting...           │
├─────────────────────────────────────────────────┤
│  💸 Current cost: $0.42 | Est. total: $1.20    │
└─────────────────────────────────────────────────┘
```

**Tech Stack**:
- **FastAPI + WebSockets** (streaming updates)
- **React + Recharts** (dashboard frontend)
- **Nuestro IP**: Instrumentación de agentes, visualización

**Valor**: Developers aman ver qué pasa en tiempo real. Debugging 10x más rápido.

### 4. **Compliance Report Generator** 📋

**Idea**: Auto-generar reportes de compliance para SOC2, ISO27001, GDPR.

**Ejemplo**:
```
📄 SOC2 Compliance Report - January 2026

✅ Security Controls Implemented:
   - Prompt injection defense (rebuff)
   - Agent policy enforcement (OPA)
   - Secrets detection (gitleaks)

✅ Evidence:
   - 127 policy violations prevented
   - 0 critical vulnerabilities deployed
   - 100% agent workflows validated

📊 Audit Trail:
   - Policy changes: 3 (all reviewed)
   - Agent deployments: 42 (all scanned)
   - Security incidents: 0

⏱️ Generated in 3 seconds
```

**Tech Stack**:
- **Jinja2** (templating para reportes)
- **WeasyPrint** (PDF generation)
- **Nuestro IP**: Templates de compliance, mapeo de controles

**Valor**: Enterprises pagan MUCHO por compliance. Automatizar esto es oro.

### 5. **Agent Debugging Tools (Step-Through)** 🐛

**Idea**: Debugger para agentes, como GDB pero para AI workflows.

**Ejemplo**:
```bash
$ qodacode debug agent_workflow.py

> Breakpoint at Task 2 (writer agent)
> Input context: {...}
> LLM prompt: "Write an article about..."

[d]ebug / [c]ontinue / [s]kip / [i]nspect ?
> i

Agent State:
  - Role: writer
  - Tools: [web_search, wikipedia]
  - Context: [task1_output]
  - LLM calls so far: 3
  - Tokens used: 4,230

> c

Executing Task 2...
✓ Done
```

**Tech Stack**:
- **pdb-like interface** (Python debugger API)
- **Nuestro IP**: Instrumentación, breakpoints en agent transitions

**Valor**: Developers pagan por herramientas que les ahorran horas de debugging.

### 6. **Agent Marketplace & Templates** 🏪

**Idea**: Curated marketplace de agent workflows pre-validados.

**Ejemplo**:
```
🛒 Qodacode Agent Marketplace

📦 Content Pipeline Workflow
   ✅ Security validated
   ✅ Policy compliant
   ✅ Cost optimized
   💰 Est. cost: $0.50/run
   ⭐ 4.8/5 (127 reviews)
   [Install Template]

📦 Code Review Assistant
   ✅ Security validated
   ✅ Policy compliant
   💰 Est. cost: $0.20/run
   ⭐ 4.9/5 (89 reviews)
   [Install Template]
```

**Tech Stack**:
- **GitHub-like marketplace** (Vercel template)
- **Nuestro IP**: Curación, validación, ratings

**Valor**: Network effects. Más usuarios = más templates = más valor.

### 7. **Policy Version Control & Rollback** 🔄

**Idea**: Git para políticas. Versionado, rollback, diff.

**Ejemplo**:
```bash
$ qodacode policy history

Commit: abc123 (HEAD)
Author: alice@company.com
Date: 2026-01-20
Message: "Increase LLM rate limit for writer agent"

  deny[msg] {
    input.tool == "ClaudeAPI"
-   input.tokens_per_minute > 100000
+   input.tokens_per_minute > 200000
    msg = "Token rate limit exceeded"
  }

$ qodacode policy rollback abc122
✓ Rolled back to previous policy version
```

**Tech Stack**:
- **gitpython** (para diff, history, rollback)
- **Nuestro IP**: UX para políticas, integración con OPA

**Valor**: Enterprises necesitan audit trail. Esto es compliance gold.

### 8. **AI-Powered Policy Generator** 🧠

**Idea**: Usar LLMs para generar políticas en lenguaje natural.

**Ejemplo**:
```
User: "No permitas que agentes borren la base de datos en producción sin aprobación humana"

AI: Generando política...

✓ Política generada:

package qodacode.agents
deny[msg] {
  input.action == "database_delete"
  input.environment == "production"
  not input.human_approved
  msg = "Database deletion in production requires human approval"
}

¿Aplicar esta política? [y/n]
```

**Tech Stack**:
- **LLM API** (Claude, GPT-4)
- **Structured output** (JSON schema enforcement)
- **Nuestro IP**: Prompt engineering, validación de políticas

**Valor**: Baja la barrera de entrada. No necesitas aprender Rego.

### 9. **Agent Performance Analytics** ⚡

**Idea**: Profiler para agentes. ¿Qué está lento? ¿Dónde optimizar?

**Ejemplo**:
```
📊 Performance Report: Content Pipeline

Bottleneck Analysis:
1. 🐌 web_search tool (3.2s avg) - 65% of total time
   💡 Suggestion: Implement caching, reduce search depth

2. 🐌 writer agent (2.1s avg) - 30% of total time
   💡 Suggestion: Use GPT-3.5 instead of GPT-4 for drafts

3. ✅ editor agent (0.3s avg) - 5% of total time
   💡 No optimization needed

⚡ Est. speedup: 2.5x with suggested optimizations
💵 Est. cost reduction: $1.20 → $0.60 per run
```

**Tech Stack**:
- **cProfile** (Python profiler)
- **Nuestro IP**: Agent-specific metrics, optimización suggestions

**Valor**: Developers pagan por performance. Hacer sus agentes 2x más rápidos = win.

### 10. **Sandboxed Agent Execution** 🔒

**Idea**: Correr agentes no confiables en ambientes aislados (containers).

**Ejemplo**:
```python
from qodacode.premium.sandbox import SecureSandbox

# Run untrusted agent in isolated container
with SecureSandbox(timeout=60, max_memory="512MB") as sandbox:
    result = sandbox.run_agent(
        agent_code="path/to/untrusted_agent.py",
        allowed_tools=["web_search"],  # Whitelist
        network_access=False  # No internet
    )

    print(result)  # Safe to use
```

**Tech Stack**:
- **Docker** (containerización)
- **gVisor** (syscall filtering para extra security)
- **Nuestro IP**: Sandboxing policies, resource limits

**Valor**: Enterprises quieren correr agentes de terceros sin riesgo. Esto es insurance.

---

## Priorización de Ideas (Para el Sábado)

| Idea | Impacto | Esfuerzo | Prioridad | Notas |
|------|---------|----------|-----------|-------|
| **Agent Profiling** | 🔥🔥🔥 | 2-3 semanas | ✅ P0 | Diferenciador clave, ML-based |
| **Cost Optimization** | 🔥🔥🔥 | 1 semana | ✅ P0 | ROI tangible, CFOs love this |
| **Real-Time Dashboard** | 🔥🔥 | 2 semanas | ✅ P1 | Cool factor, good for demos |
| **Compliance Reports** | 🔥🔥🔥 | 1 semana | ✅ P0 | Enterprise NEED, easy win |
| **Agent Debugger** | 🔥🔥 | 3 semanas | ⏳ P2 | Nice-to-have, complex |
| **Agent Marketplace** | 🔥 | 4+ semanas | ⏳ P3 | Network effects, long-term |
| **Policy Version Control** | 🔥🔥 | 1 semana | ✅ P1 | Compliance requirement |
| **AI Policy Generator** | 🔥🔥 | 1-2 semanas | ✅ P1 | Lowers barrier, viral potential |
| **Performance Analytics** | 🔥🔥 | 1-2 semanas | ✅ P1 | Developers love metrics |
| **Sandboxed Execution** | 🔥🔥🔥 | 3+ semanas | ⏳ P2 | Enterprise security, complex |

### Roadmap Actualizado (Con Nuevas Ideas)

**Week 1-2**: Core Architect Mode
- ARCH-001 (infinite loops)
- ARCH-002 (dependency hell)
- Cost Optimization Advisor (quick win)

**Week 3-4**: Policy Engine + Version Control
- OPA integration
- Policy templates
- Git-like versioning (compliance gold)

**Week 5-6**: Analytics & Reporting
- Compliance report generator (SOC2, ISO27001)
- Performance analytics dashboard
- Real-time monitoring MVP

**Week 7-8**: AI-Powered Features
- Agent profiling (ML-based anomaly detection)
- AI policy generator (natural language → Rego)

**Week 9-10**: Polish & Launch
- Documentation
- Pricing page
- v1.1.0 Premium launch

---

## Stack Técnico Completo (Con Nuevas Ideas)

| Componente | OSS a Integrar | Nuestro IP |
|------------|----------------|------------|
| **Graph Analysis** | networkx, madge | ARCH rules, detection logic |
| **Policy Engine** | OPA (Open Policy Agent) | Rego templates, versioning |
| **Prompt Security** | rebuff | Prompt vault, MCP integration |
| **Alignment Auditing** | Petri (Anthropic), Inspect | Unified verdict, MCP integration, scenarios |
| **Anomaly Detection** | scikit-learn (isolation forest) | Agent profiling, baselines |
| **Cost Optimization** | LiteLLM (pricing data) | Optimization rules, suggestions |
| **Real-Time Monitoring** | FastAPI, WebSockets | Agent instrumentation |
| **Compliance Reports** | Jinja2, WeasyPrint | SOC2/ISO templates |
| **Performance Profiling** | cProfile, py-spy | Agent-specific metrics |
| **Sandboxing** | Docker, gVisor | Security policies |
| **Dashboard** | Vercel templates, Recharts | Custom analytics |
| **Auth** | Supabase/Clerk | License validation |

---

## Conclusión

**El PRD original (de Gemini) es sólido**, pero estas ideas adicionales crean *product stickiness* y aumentan el valor percibido:

1. **Agent Profiling** → Detecta problemas que otros no ven
2. **Cost Optimization** → ROI tangible en 30 días
3. **Compliance Reports** → Enterprise auto-sell
4. **AI Policy Generator** → Baja barrera de entrada
5. **Performance Analytics** → Developers love metrics

**Estrategia para el sábado**:
1. Empezar con lo básico (Architect Mode ARCH-001)
2. Probar el código starter `graph.py`
3. Decidir cuál de estas ideas implementar primero (mi voto: **Cost Optimization** por ROI rápido)

🚀 **El código base está listo. Las ideas están sobre la mesa. Ahora a ejecutar.**

---

## 📝 Changelog del PRD

### v1.1 (January 22, 2026)
**MAJOR UPDATE**: Integración de Petri by Anthropic

**Cambios**:
- ✅ Añadida Feature #4: **Alignment Audit Engine** (Petri integration)
- ✅ Actualizado posicionamiento: "Security + Alignment" (first mover)
- ✅ Actualizado competitive analysis: único con CODE + BEHAVIOR validation
- ✅ Añadido al roadmap: Week 3-4 dedicadas a integración de Petri
- ✅ Nuevos MCP tools: `alignment_audit`, `get_alignment_score`, `unified_verdict`
- ✅ Pricing actualizado: alignment audit quotas por tier
- ✅ Stack técnico ampliado: Petri + Inspect framework

**Impacto estratégico**:
- **First Mover Advantage**: Nadie más está haciendo "Security + Alignment"
- **Anthropic Partnership Signal**: Validación técnica al usar Petri
- **Moat Defensible**: Petri es MIT pero nuestra integración + UX es IP
- **Enterprise Appeal**: Un solo vendor para security + AI safety

**Referencias**:
- [Petri GitHub](https://github.com/safety-research/petri)
- [Anthropic Alignment Blog](https://alignment.anthropic.com/2025/petri/)
- [Petri Documentation](https://safety-research.github.io/petri/)

**Next Steps**:
1. Instalar Petri localmente y probar: `pip install git+https://github.com/safety-research/petri`
2. Crear PoC de alignment audit con CrewAI agent
3. Validar costo por audit (~$0.50-1.00 por 3 modelos)
4. Diseñar UX de unified verdict (Security + Alignment scores)
