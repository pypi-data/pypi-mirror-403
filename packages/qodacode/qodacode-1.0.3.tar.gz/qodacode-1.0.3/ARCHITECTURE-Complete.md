# Qodacode Premium - Arquitectura Completa
## Plan Detallado Fase por Fase

**Autor**: Nelson Padilla
**Fecha**: 2026-01-22
**Status**: Plan Definitivo - Sin Ambigüedades

---

## Arquitectura General - Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        QODACODE PREMIUM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  👤 USUARIO                                                     │
│   │                                                             │
│   ├─► CLI/TUI (local)          ← Python package (PyPI)        │
│   │                                                             │
│   ├─► MCP Server (local)       ← Claude Code integration      │
│   │                                                             │
│   └─► Web Dashboard            ← Next.js (Vercel)             │
│        │                                                        │
│        └─► API Backend         ← Supabase (DB + Auth)         │
│             │                                                   │
│             └─► Stripe         ← Payments                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Stack Definitivo - Sin Cambios

| Componente | Tecnología | Costo | Por Qué |
|------------|------------|-------|---------|
| **Landing Page** | Next.js + Vercel | GRATIS | Deploy en 1 comando, no pagar Carrd |
| **Dashboard** | Next.js + Vercel | GRATIS | Mismo stack, reusar código |
| **Database** | Supabase PostgreSQL | GRATIS | 50k rows gratis, auth incluido |
| **Auth** | Supabase Auth | GRATIS | Email/password + SSO incluido |
| **API** | Supabase Edge Functions | GRATIS | Serverless, ya integrado |
| **Payments** | Stripe | GRATIS | Standard, después 2.9% + $0.30 |
| **Email** | Resend | GRATIS | 3k emails/mes, mejor DX que SendGrid |
| **DNS** | Cloudflare | GRATIS | CDN + DDoS protection |
| **Python Package** | PyPI | GRATIS | Standard para Python |
| **Code Hosting** | GitHub | GRATIS | Ya lo usas |

**Costo Total Todas las Fases: $0/mes** hasta tener revenue real

---

# FASE 1: MVP (v1.1.0)
## Timeline: 2-3 semanas

### Objetivo
Validar "Security + Alignment" con primeros clientes pagando.

---

## Arquitectura Fase 1

```
┌──────────────────────────────────────────────────────────────┐
│                         FASE 1 MVP                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FRONTEND (Next.js + Vercel - GRATIS)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Landing Page (qodacode.com)                           │ │
│  │  ├─ Hero: "Security + Alignment for AI Agents"        │ │
│  │  ├─ Pricing Table: Free / Pro $19 / Team $39          │ │
│  │  ├─ Features Comparison                               │ │
│  │  └─ CTA: "Start Free Trial" → Stripe Checkout        │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│  PAYMENTS (Stripe - GRATIS hasta revenue)                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Stripe Checkout                                       │ │
│  │  ├─ Pro: $19/month                                     │ │
│  │  ├─ Team: $39/seat/month                              │ │
│  │  └─ Webhook → Send license key via email             │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│  EMAIL (Resend - GRATIS)                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Templates:                                            │ │
│  │  ├─ Welcome email + license key                       │ │
│  │  ├─ Trial expiration warning                          │ │
│  │  └─ Payment confirmation                              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  BACKEND (Python CLI - LOCAL)                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  qodacode CLI/MCP                                      │ │
│  │  ├─ Security scan (Semgrep, Gitleaks) ✅ Ya existe    │ │
│  │  ├─ Alignment audit (Petri) 🆕                        │ │
│  │  ├─ Unified verdict 🆕                                │ │
│  │  ├─ Cost optimization advisor 🆕                      │ │
│  │  └─ License validation (OFFLINE) 🆕                   │ │
│  │     └─ Check env var: QODACODE_LICENSE_KEY           │ │
│  │     └─ Format: qoda_pro_xxxx or qoda_team_xxxx       │ │
│  │     └─ Grace period: 30 días sin key                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Qué Construimos en Fase 1

### 1. **Landing Page (Next.js + Vercel)**

**Estructura de archivos**:
```
qodacode-landing/
├── app/
│   ├── page.tsx              # Homepage
│   ├── pricing/page.tsx      # Pricing page
│   └── docs/page.tsx         # Quick start docs
├── components/
│   ├── Hero.tsx              # Hero section
│   ├── Features.tsx          # Features grid
│   ├── PricingTable.tsx      # Pricing cards
│   └── Footer.tsx            # Footer
├── public/
│   └── logo.svg
└── package.json
```

**Páginas que vamos a crear**:
1. **Homepage** (`/`):
   - Hero: "The ONLY tool validating CODE + AI AGENTS"
   - Problem/Solution
   - Features grid (4 boxes)
   - Social proof (cuando tengamos)
   - CTA: "Start Free Trial"

2. **Pricing** (`/pricing`):
   ```
   ┌─────────────┬─────────────┬─────────────┐
   │    FREE     │    PRO      │    TEAM     │
   ├─────────────┼─────────────┼─────────────┤
   │ $0/forever  │ $19/month   │ $39/seat    │
   │             │             │             │
   │ • CLI/TUI   │ • Everything│ • Everything│
   │ • Security  │   in Free   │   in Pro    │
   │   scans     │ • Alignment │ • 100 audits│
   │ • MCP tools │   audits    │ • Policy    │
   │             │   (10/mo)   │   engine    │
   │             │ • Cost      │ • Team      │
   │             │   advisor   │   dashboard │
   │             │             │             │
   │ [Download]  │ [Buy Now]   │ [Buy Now]   │
   └─────────────┴─────────────┴─────────────┘
   ```

3. **Docs** (`/docs`):
   - Installation
   - Quick start
   - MCP setup for Claude Code

**Deploy**:
```bash
cd qodacode-landing
vercel deploy --prod
# → qodacode.com (auto SSL, global CDN)
```

**Tiempo**: 2-3 días

---

### 2. **Stripe Integration**

**Setup**:
```typescript
// app/api/checkout/route.ts
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: Request) {
  const { plan } = await req.json(); // "pro" or "team"

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    line_items: [
      {
        price: plan === 'pro'
          ? 'price_pro_monthly_xxx'   // $19/mo
          : 'price_team_monthly_xxx', // $39/seat
        quantity: plan === 'team' ? 5 : 1, // Default 5 seats
      },
    ],
    success_url: 'https://qodacode.com/success?session_id={CHECKOUT_SESSION_ID}',
    cancel_url: 'https://qodacode.com/pricing',
  });

  return Response.json({ url: session.url });
}
```

**Webhook (enviar license key)**:
```typescript
// app/api/webhooks/stripe/route.ts
import Resend from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(req: Request) {
  const event = await stripe.webhooks.constructEvent(
    await req.text(),
    req.headers.get('stripe-signature')!,
    process.env.STRIPE_WEBHOOK_SECRET!
  );

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object;

    // Generate license key
    const licenseKey = `qoda_pro_${generateRandomString(24)}`;

    // Send email with key
    await resend.emails.send({
      from: 'team@qodacode.com',
      to: session.customer_email,
      subject: 'Your Qodacode Premium License',
      html: `
        <h1>Welcome to Qodacode Premium! 🎉</h1>
        <p>Your license key:</p>
        <code>${licenseKey}</code>
        <p>Activate: <code>export QODACODE_LICENSE_KEY="${licenseKey}"</code></p>
      `,
    });
  }

  return Response.json({ received: true });
}
```

**Tiempo**: 1-2 días

---

### 3. **Python CLI - Premium Features**

**Estructura**:
```
qodacode/
├── premium/
│   ├── __init__.py
│   ├── license.py              # 🆕 License validation (offline)
│   ├── alignment/              # 🆕 Petri integration
│   │   ├── __init__.py
│   │   ├── auditor.py          # Petri wrapper
│   │   ├── scenarios.py        # 5 scenarios
│   │   └── verdict.py          # Unified scoring
│   └── cost/                   # 🆕 Cost optimization
│       ├── __init__.py
│       └── advisor.py          # LiteLLM integration
```

**License validation (offline stub)**:
```python
# qodacode/premium/license.py
import os
from datetime import datetime, timedelta

def validate_license() -> dict:
    """
    Offline license validation (Fase 1).
    Online validation viene en Fase 2 con Supabase.
    """
    key = os.getenv("QODACODE_LICENSE_KEY")

    if not key:
        # Grace period: 30 days trial
        install_date = get_install_date()
        days_since = (datetime.now() - install_date).days

        if days_since < 30:
            return {
                "valid": True,
                "tier": "trial",
                "days_remaining": 30 - days_since,
                "message": f"Trial: {30 - days_since} days remaining"
            }
        else:
            return {
                "valid": False,
                "tier": "free",
                "message": "Trial expired. Upgrade at qodacode.com/pricing"
            }

    # Validate key format
    if key.startswith("qoda_pro_"):
        tier = "pro"
    elif key.startswith("qoda_team_"):
        tier = "team"
    else:
        return {"valid": False, "message": "Invalid license key"}

    # Offline: Can't verify with server yet
    # For Fase 1, just accept valid format
    return {
        "valid": True,
        "tier": tier,
        "message": f"Licensed: {tier.upper()}"
    }

def require_premium(tier="pro"):
    """Decorator to gate premium features"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            license = validate_license()
            if not license["valid"]:
                raise PermissionError(
                    f"Premium feature. {license['message']}\n"
                    f"Upgrade: https://qodacode.com/pricing"
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

**Alignment Auditor (Petri wrapper)**:
```python
# qodacode/premium/alignment/auditor.py
from inspect_ai import Task, eval
from inspect_ai.model import get_model
from .scenarios import get_scenario
from .verdict import AlignmentScore

class AlignmentAuditor:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    @require_premium("pro")
    def run_audit(self, scenarios, target_model="claude-3-5-sonnet"):
        """
        Run alignment audit using Petri.

        Usage:
            auditor = AlignmentAuditor()
            result = auditor.run_audit(
                scenarios=["self_preservation", "deception"],
                target_model="claude-3-5-sonnet"
            )
        """
        results = []
        for scenario_id in scenarios:
            scenario = get_scenario(scenario_id)
            # Run Petri audit (simplified for MVP)
            result = self._run_scenario(scenario, target_model)
            results.append(result)

        return self._aggregate_results(results, scenarios)
```

**Cost Optimization Advisor**:
```python
# qodacode/premium/cost/advisor.py
import litellm

@require_premium("pro")
def analyze_costs(file_path: str) -> dict:
    """
    Analyze agent code for expensive LLM calls.
    Suggest optimizations.

    Returns:
        {
            "current_cost": 2.40,  # per run
            "optimized_cost": 0.60,
            "savings_monthly": 1800,  # at 1000 runs/month
            "recommendations": [...]
        }
    """
    # Parse agent code, find LLM calls
    llm_calls = parse_llm_calls(file_path)

    current_cost = 0
    recommendations = []

    for call in llm_calls:
        model = call["model"]  # e.g., "gpt-4"
        tokens = call["estimated_tokens"]

        # Get pricing from LiteLLM
        pricing = litellm.get_model_cost_map(model)
        cost_per_call = (tokens / 1000) * pricing["input_cost_per_token"]
        current_cost += cost_per_call

        # Suggest cheaper alternative
        if model == "gpt-4":
            recommendations.append({
                "current": f"Using {model}: ${cost_per_call:.2f}/call",
                "suggestion": "Switch to gpt-3.5-turbo: $0.15/call",
                "savings": cost_per_call - 0.15
            })

    optimized_cost = current_cost * 0.25  # Assume 75% savings

    return {
        "current_cost": round(current_cost, 2),
        "optimized_cost": round(optimized_cost, 2),
        "savings_monthly": round((current_cost - optimized_cost) * 1000, 2),
        "recommendations": recommendations
    }
```

**MCP Tools**:
```python
# qodacode/mcp_server.py

@mcp.tool()
def alignment_audit(
    scenarios: list[str],
    target_model: str = "claude-3-5-sonnet"
):
    """Run Petri alignment audit (Premium)"""
    from qodacode.premium.alignment import AlignmentAuditor

    auditor = AlignmentAuditor()
    return auditor.run_audit(scenarios, target_model)

@mcp.tool()
def unified_verdict():
    """Get unified Security + Alignment verdict (Premium)"""
    from qodacode.premium.alignment import create_unified_verdict

    # Get security score (from existing scans)
    security = get_latest_security_scan()

    # Get alignment score (from latest audit)
    alignment = get_latest_alignment_audit()

    verdict = create_unified_verdict(security, alignment)
    return verdict.to_dict()

@mcp.tool()
def analyze_agent_costs(file_path: str):
    """Analyze agent LLM costs and suggest optimizations (Premium)"""
    from qodacode.premium.cost import analyze_costs

    return analyze_costs(file_path)
```

**Tiempo**: 5-7 días

---

## Deliverables Fase 1

### ✅ Código
1. **Landing page** (Next.js)
   - Homepage, Pricing, Docs
   - Deploy en Vercel → qodacode.com

2. **Stripe integration**
   - Checkout flow
   - Webhook → Email license key

3. **Python CLI premium features**
   - License validation (offline)
   - Alignment audit (Petri wrapper)
   - Cost optimization advisor
   - 3 nuevos MCP tools

### ✅ Infraestructura
- Domain: qodacode.com ($12/año)
- Vercel: Deploy landing (GRATIS)
- Stripe: Account setup (GRATIS)
- Resend: Email API (GRATIS 3k/mes)

### ✅ Documentación
- README actualizado
- Docs site (/docs)
- MCP setup guide

---

## Métricas de Éxito Fase 1

**By Feb 15, 2026**:
- ✅ 10 paid Pro users ($190 MRR)
- ✅ 2 paid Team trials ($78 MRR)
- ✅ Product Hunt launch (300+ upvotes)
- ✅ Landing page live
- ✅ Petri integration working

**Revenue Goal**: $250-500 MRR

---

## Costos Reales Fase 1

| Item | Costo | Frecuencia |
|------|-------|------------|
| Domain (qodacode.com) | $12 | Anual |
| Vercel | $0 | Gratis (hobby tier) |
| Stripe | 2.9% + $0.30 | Por transacción |
| Resend | $0 | Gratis hasta 3k emails/mes |
| Supabase | $0 | No usamos hasta Fase 2 |

**Total Fase 1**: $12/año = **$1/mes**

---

# FASE 2: Growth (v1.2.0)
## Timeline: 3-4 semanas

### Objetivo
Expand features, onboard Team customers, reach $2,900 MRR.

---

## Arquitectura Fase 2

```
┌──────────────────────────────────────────────────────────────┐
│                      FASE 2 GROWTH                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FRONTEND (Next.js + Vercel - GRATIS)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ✅ Landing page (de Fase 1)                           │ │
│  │  🆕 Account page (/account)                            │ │
│  │     ├─ License key management                          │ │
│  │     ├─ Usage stats (simple)                            │ │
│  │     └─ Billing portal (Stripe)                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│  DATABASE (Supabase - GRATIS)                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  PostgreSQL Tables:                                    │ │
│  │  ├─ users (id, email, stripe_id, tier)               │ │
│  │  ├─ licenses (key, user_id, tier, expires_at)        │ │
│  │  └─ usage (user_id, scans_count, audits_count)       │ │
│  │                                                         │ │
│  │  Edge Functions (API):                                │ │
│  │  ├─ POST /license/validate → Check key online        │ │
│  │  ├─ GET /usage/current → Get usage stats             │ │
│  │  └─ POST /usage/increment → Track scans              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  BACKEND (Python CLI - LOCAL)                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ✅ Everything from Fase 1                             │ │
│  │  🆕 Architect Mode                                     │ │
│  │     ├─ networkx graph analysis                        │ │
│  │     ├─ ARCH-001: Infinite loops                       │ │
│  │     ├─ ARCH-002: Dependency hell                      │ │
│  │     └─ ARCH-003: Orphaned agents                      │ │
│  │                                                         │ │
│  │  🆕 Policy Engine                                      │ │
│  │     ├─ OPA integration                                │ │
│  │     ├─ 5 starter Rego templates                       │ │
│  │     └─ Policy version control (Git-like)              │ │
│  │                                                         │ │
│  │  🆕 Compliance Reports                                 │ │
│  │     ├─ SOC2 template (Jinja2 → PDF)                  │ │
│  │     ├─ ISO 27001 template                             │ │
│  │     └─ GDPR summary                                   │ │
│  │                                                         │ │
│  │  🆕 License validation (ONLINE)                        │ │
│  │     └─ Call Supabase API for validation              │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Qué Construimos en Fase 2

### 1. **Supabase Setup**

**Database schema**:
```sql
-- users table
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  stripe_customer_id TEXT,
  tier TEXT CHECK (tier IN ('free', 'pro', 'team', 'enterprise')),
  created_at TIMESTAMP DEFAULT NOW()
);

-- licenses table
CREATE TABLE licenses (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  key TEXT UNIQUE NOT NULL,
  user_id UUID REFERENCES users(id),
  tier TEXT CHECK (tier IN ('pro', 'team', 'enterprise')),
  seats INT DEFAULT 1,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- usage table
CREATE TABLE usage (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  scans_count INT DEFAULT 0,
  alignment_audits_count INT DEFAULT 0,
  month TEXT, -- "2026-01"
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, month)
);
```

**Edge Function (license validation)**:
```typescript
// supabase/functions/validate-license/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from '@supabase/supabase-js'

serve(async (req) => {
  const { key } = await req.json()

  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_KEY')!
  )

  // Check if key exists and is valid
  const { data: license, error } = await supabase
    .from('licenses')
    .select('*, users(*)')
    .eq('key', key)
    .single()

  if (error || !license) {
    return new Response(JSON.stringify({
      valid: false,
      message: 'Invalid license key'
    }), { status: 401 })
  }

  // Check expiration
  if (license.expires_at && new Date(license.expires_at) < new Date()) {
    return new Response(JSON.stringify({
      valid: false,
      message: 'License expired'
    }), { status: 401 })
  }

  return new Response(JSON.stringify({
    valid: true,
    tier: license.tier,
    seats: license.seats,
    user: license.users
  }))
})
```

**Tiempo**: 2-3 días

---

### 2. **Python CLI - Online License Validation**

```python
# qodacode/premium/license.py (updated)
import httpx
from datetime import datetime

CACHE_FILE = "~/.qodacode/license_cache.json"

def validate_license() -> dict:
    """
    Online license validation (Fase 2).
    Falls back to offline if no internet.
    """
    key = os.getenv("QODACODE_LICENSE_KEY")

    if not key:
        # Same trial logic as Fase 1
        return handle_trial()

    # Try online validation first
    try:
        response = httpx.post(
            "https://YOUR_PROJECT.supabase.co/functions/v1/validate-license",
            json={"key": key},
            timeout=3.0
        )

        if response.status_code == 200:
            data = response.json()
            # Cache validation for 1 hour
            cache_validation(data)
            return data
        else:
            # Invalid key
            return {"valid": False, "message": "Invalid license key"}

    except Exception as e:
        # Offline: Use cached validation
        cached = load_cached_validation()
        if cached and not is_cache_expired(cached):
            return cached

        # No cache, fall back to offline validation (Fase 1 logic)
        return validate_offline(key)
```

**Tiempo**: 1 día

---

### 3. **Architect Mode**

```python
# qodacode/premium/architect/graph.py
import networkx as nx
from tree_sitter import Parser

class AgentGraphAnalyzer:
    def __init__(self):
        self.graph = nx.DiGraph()

    @require_premium("pro")
    def analyze(self, file_path: str) -> dict:
        """
        Analyze agent workflow for architectural issues.

        Detects:
        - ARCH-001: Infinite loops (cycles)
        - ARCH-002: Dependency hell (too many edges)
        - ARCH-003: Orphaned agents (isolated nodes)
        """
        # Build graph from CrewAI/LangGraph code
        self.build_graph(file_path)

        issues = []
        issues.extend(self.detect_cycles())  # ARCH-001
        issues.extend(self.detect_bottlenecks())  # ARCH-002
        issues.extend(self.detect_orphans())  # ARCH-003

        return {
            "issues": issues,
            "graph_summary": {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges()
            }
        }

    def detect_cycles(self) -> list:
        """ARCH-001: Detect infinite loops"""
        cycles = list(nx.simple_cycles(self.graph))
        issues = []

        for cycle in cycles:
            issues.append({
                "rule_id": "ARCH-001",
                "severity": "critical",
                "title": "Infinite Loop in Agent Workflow",
                "description": f"Cycle: {' → '.join(cycle)} → {cycle[0]}",
                "recommendation": "Break cycle or add termination condition"
            })

        return issues
```

**MCP Tool**:
```python
@mcp.tool()
def analyze_agent_topology(file_path: str):
    """Detect infinite loops and architectural issues (Premium)"""
    from qodacode.premium.architect import AgentGraphAnalyzer

    analyzer = AgentGraphAnalyzer()
    return analyzer.analyze(file_path)
```

**Tiempo**: 7-10 días

---

### 4. **Policy Engine (OPA)**

```python
# qodacode/premium/policy/engine.py
import subprocess
import json

class PolicyEngine:
    def __init__(self):
        self.opa_binary = self._ensure_opa_installed()

    @require_premium("team")
    def evaluate(self, policy_path: str, input_data: dict) -> dict:
        """
        Evaluate agent action against Rego policy.

        Returns:
            {
                "allowed": False,
                "violations": ["🚨 Production DB delete requires approval"],
                "policy": "no_prod_db_deletes"
            }
        """
        # Call OPA binary
        result = subprocess.run(
            [self.opa_binary, "eval", "-d", policy_path,
             "-i", json.dumps(input_data), "data.qodacode.deny"],
            capture_output=True,
            text=True
        )

        output = json.loads(result.stdout)
        violations = output.get("result", [])

        return {
            "allowed": len(violations) == 0,
            "violations": violations,
            "policy": policy_path
        }
```

**Starter Rego Policy**:
```rego
# policies/no_prod_db_deletes.rego
package qodacode.agents

deny[msg] {
  input.action == "database_delete"
  input.environment == "production"
  not input.human_approved
  msg = "🚨 POLICY VIOLATION: Production DB delete requires human approval"
}
```

**Tiempo**: 10-12 días

---

### 5. **Compliance Report Generator**

```python
# qodacode/premium/compliance/generator.py
from jinja2 import Template
from weasyprint import HTML

@require_premium("team")
def generate_report(
    report_type: str,  # "soc2", "iso27001", "gdpr"
    start_date: str,
    end_date: str
) -> str:
    """
    Generate compliance report PDF.

    Returns:
        Path to generated PDF file
    """
    # Gather evidence
    evidence = collect_evidence(start_date, end_date)

    # Load template
    template = load_template(report_type)

    # Render HTML
    html = template.render(
        company="Qodacode User",
        period=f"{start_date} to {end_date}",
        evidence=evidence
    )

    # Generate PDF
    output_path = f"compliance_{report_type}_{start_date}.pdf"
    HTML(string=html).write_pdf(output_path)

    return output_path

def collect_evidence(start_date, end_date):
    """Gather compliance evidence from scans/audits"""
    return {
        "scans_completed": 127,
        "policies_enforced": 42,
        "vulnerabilities_prevented": 18,
        "alignment_audits_passed": 35,
        "alignment_audits_failed": 3,
        "critical_issues": 0
    }
```

**SOC2 Template** (Jinja2):
```html
<!-- templates/soc2.html -->
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Professional styling */
  </style>
</head>
<body>
  <h1>SOC 2 Compliance Report</h1>
  <p>Period: {{ period }}</p>

  <h2>Security Controls Implemented</h2>
  <ul>
    <li>✅ Code security scanning ({{ evidence.scans_completed }} scans)</li>
    <li>✅ AI alignment audits ({{ evidence.alignment_audits_passed }} passed)</li>
    <li>✅ Policy enforcement ({{ evidence.policies_enforced }} policies)</li>
  </ul>

  <h2>Evidence</h2>
  <table>
    <tr><td>Vulnerabilities Prevented</td><td>{{ evidence.vulnerabilities_prevented }}</td></tr>
    <tr><td>Critical Issues</td><td>{{ evidence.critical_issues }}</td></tr>
  </table>
</body>
</html>
```

**Tiempo**: 5-7 días

---

## Deliverables Fase 2

### ✅ Código
1. **Supabase backend**
   - Database schema
   - Edge Functions (license validation, usage tracking)

2. **Account page** (Next.js)
   - `/account` → View license, usage stats

3. **Python CLI features**
   - Architect Mode (ARCH-001/002/003)
   - Policy Engine (OPA + 5 templates)
   - Compliance Reports (SOC2, ISO27001, GDPR)
   - Online license validation

### ✅ Infraestructura
- Supabase project setup (GRATIS)
- OPA binary integration

---

## Métricas de Éxito Fase 2

**By Mar 15, 2026**:
- ✅ 50 paid Pro users ($950 MRR)
- ✅ 10 paid Team accounts ($1,950 MRR)
- ✅ Total: $2,900 MRR

---

## Costos Reales Fase 2

| Item | Costo | Frecuencia |
|------|-------|------------|
| Todo de Fase 1 | $1/mes | Mensual |
| Supabase | $0 | Gratis (hasta 50k rows) |

**Total Fase 2**: $1/mes

---

# FASE 3: Enterprise (v1.3.0)
## Timeline: 4-6 semanas

### Objetivo
Close first Enterprise deals, reach $15k MRR.

---

## Arquitectura Fase 3

```
┌──────────────────────────────────────────────────────────────┐
│                   FASE 3 ENTERPRISE                          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FRONTEND (Next.js + Vercel)                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ✅ Landing (Fase 1)                                   │ │
│  │  ✅ Account page (Fase 2)                              │ │
│  │  🆕 DASHBOARD (/dashboard)                             │ │
│  │     ├─ Overview: Usage metrics, cost trends           │ │
│  │     ├─ Agents: List all scanned agents               │ │
│  │     ├─ Policies: Manage policies, violations         │ │
│  │     ├─ Audits: Alignment audit history               │ │
│  │     ├─ Reports: Generate compliance PDFs             │ │
│  │     └─ Team: User management (Team tier)             │ │
│  │                                                         │ │
│  │  Libraries:                                            │ │
│  │  ├─ Recharts (visualizations)                         │ │
│  │  ├─ TailwindCSS (styling)                             │ │
│  │  └─ shadcn/ui (components)                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                          │                                   │
│                          ▼                                   │
│  DATABASE (Supabase)                                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ✅ Tables from Fase 2                                 │ │
│  │  🆕 New tables:                                        │ │
│  │     ├─ agents (id, name, file_path, graph_data)      │ │
│  │     ├─ policies (id, name, rego_code, version)       │ │
│  │     ├─ audits (id, agent_id, scenarios, results)     │ │
│  │     └─ anomalies (id, agent_id, detected_at, type)   │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  BACKEND (Python CLI - LOCAL)                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ✅ Everything from Fase 1-2                           │ │
│  │  🆕 Agent Profiling                                    │ │
│  │     ├─ Track baselines (normal behavior)              │ │
│  │     ├─ Anomaly detection (scikit-learn)               │ │
│  │     └─ Alert on deviations                            │ │
│  │                                                         │ │
│  │  🆕 Performance Analytics                              │ │
│  │     ├─ cProfile integration                            │ │
│  │     ├─ Bottleneck detection                            │ │
│  │     └─ Optimization suggestions                        │ │
│  │                                                         │ │
│  │  🆕 AI Policy Generator                                │ │
│  │     ├─ Natural language → Rego                        │ │
│  │     └─ Validation + preview                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Qué Construimos en Fase 3

### 1. **Dashboard Web (Next.js)**

**Páginas principales**:

1. **Overview** (`/dashboard`):
   ```
   ┌─────────────────────────────────────────────┐
   │  📊 Usage This Month                        │
   │  ┌─────────┬─────────┬─────────┐           │
   │  │ 127     │ 35      │ $240    │           │
   │  │ Scans   │ Audits  │ Saved   │           │
   │  └─────────┴─────────┴─────────┘           │
   │                                             │
   │  📈 Scans Over Time                         │
   │  [Recharts line chart]                      │
   │                                             │
   │  ⚠️ Recent Alerts                           │
   │  • ARCH-001: Cycle detected in agent X     │
   │  • Anomaly: Agent Y calling LLM 500x       │
   └─────────────────────────────────────────────┘
   ```

2. **Agents** (`/dashboard/agents`):
   - Table of all scanned agents
   - Graph visualization (networkx → SVG)
   - Issues detected

3. **Policies** (`/dashboard/policies`):
   - List policies
   - Create new (AI generator)
   - View violations history

4. **Audits** (`/dashboard/audits`):
   - Alignment audit history
   - Filter by scenario
   - View transcripts

**Tiempo**: 15-20 días

---

### 2. **Agent Profiling (ML)**

```python
# qodacode/premium/profiling/profiler.py
from sklearn.ensemble import IsolationForest
import numpy as np

class AgentProfiler:
    @require_premium("team")
    def profile_agent(self, agent_id: str, days=30) -> dict:
        """
        Learn normal behavior for agent over time.
        Store baseline in database.
        """
        # Collect historical data
        history = fetch_agent_history(agent_id, days)

        # Calculate baseline
        baseline = {
            "avg_llm_calls": np.mean([h["llm_calls"] for h in history]),
            "avg_tokens": np.mean([h["tokens"] for h in history]),
            "avg_duration": np.mean([h["duration"] for h in history])
        }

        # Save to database
        save_baseline(agent_id, baseline)

        return baseline

    @require_premium("team")
    def detect_anomalies(self, agent_id: str) -> list:
        """
        Detect when agent deviates from baseline.
        """
        baseline = load_baseline(agent_id)
        current = get_current_metrics(agent_id)

        anomalies = []

        # Check deviations (threshold: 3x baseline)
        if current["llm_calls"] > baseline["avg_llm_calls"] * 3:
            anomalies.append({
                "type": "excessive_llm_calls",
                "severity": "high",
                "message": f"Agent calling LLM {current['llm_calls']}x (normal: {baseline['avg_llm_calls']}x)",
                "recommendation": "Check for infinite loop or prompt injection"
            })

        return anomalies
```

**Tiempo**: 10-12 días

---

### 3. **Performance Analytics**

```python
# qodacode/premium/performance/analyzer.py
import cProfile
import pstats

@require_premium("team")
def analyze_performance(agent_id: str) -> dict:
    """
    Profile agent execution, identify bottlenecks.
    """
    # Run agent with profiling
    profiler = cProfile.Profile()
    profiler.enable()

    # Execute agent
    run_agent(agent_id)

    profiler.disable()

    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')

    # Extract top bottlenecks
    bottlenecks = []
    for func, (cc, nc, tt, ct, callers) in stats.stats.items():
        if tt > 1.0:  # Functions taking >1 second
            bottlenecks.append({
                "function": func[2],  # Function name
                "time": round(tt, 2),
                "percentage": round((tt / stats.total_tt) * 100, 1)
            })

    # Generate recommendations
    recommendations = generate_recommendations(bottlenecks)

    return {
        "bottlenecks": sorted(bottlenecks, key=lambda x: x["time"], reverse=True)[:5],
        "recommendations": recommendations,
        "estimated_speedup": calculate_speedup(recommendations)
    }
```

**Tiempo**: 7-10 días

---

### 4. **AI Policy Generator**

```python
# qodacode/premium/policy/generator.py
from anthropic import Anthropic

@require_premium("team")
def generate_policy(description: str) -> dict:
    """
    Generate Rego policy from natural language.

    Example:
        description = "No database deletes in production without approval"
        → Returns valid Rego code
    """
    client = Anthropic()

    prompt = f"""Generate a Rego policy for Open Policy Agent.

User requirement: {description}

Requirements:
- Package: qodacode.agents
- Use deny[msg] pattern
- Include clear violation message
- Validate input fields exist

Output ONLY the Rego code, no explanations.
"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20250122",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    rego_code = response.content[0].text

    # Validate syntax
    is_valid, error = validate_rego_syntax(rego_code)

    return {
        "code": rego_code,
        "valid": is_valid,
        "error": error,
        "description": description
    }
```

**Tiempo**: 5-7 días

---

## Deliverables Fase 3

### ✅ Código
1. **Dashboard completo** (Next.js + Vercel)
2. **Agent Profiling** (ML anomaly detection)
3. **Performance Analytics** (cProfile)
4. **AI Policy Generator** (LLM-powered)

### ✅ Infraestructura
- Vercel Pro ($20/mes) - Si sales de free tier
- Supabase Pro ($25/mes) - Si >50k rows

---

## Métricas de Éxito Fase 3

**By Apr 30, 2026**:
- ✅ 100 Pro users ($1,900 MRR)
- ✅ 25 Team accounts ($4,875 MRR)
- ✅ 2 Enterprise contracts ($8,333 MRR)
- ✅ **Total: $15,108 MRR**

---

## Costos Reales Fase 3

| Item | Costo | Frecuencia |
|------|-------|------------|
| Domain | $1/mes | Mensual |
| Vercel Pro | $20/mes | Mensual (si >hobby) |
| Supabase Pro | $25/mes | Mensual (si >50k rows) |

**Total Fase 3**: ~$46/mes

**Pero revenue es $15k MRR** → Profit: $14,954/mes

---

# FASE 4: Scale (v2.0.0)
## Timeline: Post-PMF (May+ 2026)

**Objetivo**: Scale to $154k MRR, prepare for Series A

**Features principales**:
- On-premise deployment (Docker/K8s)
- Sandboxed execution (gVisor)
- Multi-region (US/EU/APAC)
- Advanced ML features

**Detalle completo**: Ver PHASING document

---

# Resumen Final

## Timeline Total
- **Fase 1**: 2-3 semanas → $250-500 MRR
- **Fase 2**: 3-4 semanas → $2,900 MRR
- **Fase 3**: 4-6 semanas → $15k MRR
- **Fase 4**: Post-PMF → $154k MRR

**Total hasta Enterprise**: ~10-14 semanas (3 meses)

---

## Stack Definitivo (Sin Cambios)

```
Frontend:  Next.js + Vercel (GRATIS)
Backend:   Supabase (GRATIS → $25/mes)
Payments:  Stripe (2.9% fees)
Email:     Resend (GRATIS)
DNS:       Cloudflare (GRATIS)
Package:   PyPI (GRATIS)
```

**Costo total hasta tener revenue**: $1/mes (solo domain)

---

## ¿Claro Ahora?

✅ No más confusión
✅ No pagar Carrd ($19/año) → Usamos Next.js GRATIS
✅ Stack simple: Next.js + Supabase + Vercel
✅ Plan fase por fase detallado
✅ Costos reales ($1/mes hasta revenue)

🚀 **Ready to ship.**
