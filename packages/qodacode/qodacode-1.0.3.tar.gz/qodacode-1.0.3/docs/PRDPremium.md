# Qodacode Premium - Product Requirements Document

## Estado: PLANIFICACIÓN
**Versión:** 1.0.0
**Fecha:** 2026-01-20
**Autor:** Qodacode Team

---

## 1. Resumen Ejecutivo

Qodacode Premium es la capa cloud y de colaboración que complementa el CLI/TUI/MCP open source. Mientras el motor de análisis permanece 100% local y gratuito, Premium añade:

- **Dashboard web** para visualizar historial y tendencias
- **Colaboración de equipo** con roles y permisos
- **Integraciones** con Slack, Teams, Jira, Calendar, Email
- **Reglas AGENT exclusivas** para seguridad de código AI-generated
- **Alertas proactivas** y reportes automáticos

**Tesis central:** Enterprise tools were built for a world where humans write all the code. That world ended in 2023. Qodacode is the first security scanner built for AI-assisted development.

---

## 2. Modelo de Negocio

### 2.1 Open Core Model

```
┌─────────────────────────────────────────────────────────────┐
│                    OPEN SOURCE (MIT)                         │
│                   Gratis para siempre                        │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │
│  │   CLI   │  │   TUI   │  │   MCP   │                     │
│  │ qodacode│  │ textual │  │ server  │                     │
│  └─────────┘  └─────────┘  └─────────┘                     │
│                     │                                        │
│              Detection Engine                                │
│         (4000+ rules, typosquatting)                        │
└─────────────────────────────────────────────────────────────┘
                      │
                      │ (API sync opcional)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    PREMIUM (Propietario)                     │
│                      $9-39/dev/mes                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Cloud Dashboard + Team                   │  │
│  │   • Historial   • Trends   • Integraciones           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Pricing Tiers

| Tier | Precio | Target | Features |
|------|--------|--------|----------|
| **Free** | $0 | Developers individuales | CLI/TUI/MCP completo, GitHub Action |
| **Pro** | $9/dev/mes | Freelancers, side projects | + Dashboard, historial, trends, email |
| **Team** | $19/dev/mes | Startups, equipos pequeños | + Slack/Teams, Jira, Calendar, AGENT-002 |
| **Business** | $39/dev/mes | Enterprise | + SSO, audit logs, SLA, API |

### 2.3 Proyección de Ingresos

| Métrica | Year 1 (Conservador) | Year 1 (Optimista) |
|---------|---------------------|-------------------|
| Users free tier | 5,000 | 15,000 |
| Conversion rate | 0.5% | 2% |
| Paid users | 25 | 300 |
| ARPU | $15 | $20 |
| **ARR** | **$4,500** | **$72,000** |

---

## 3. Arquitectura Cloud

### 3.1 Stack Técnico

```
┌─────────────────────────────────────────────────────────────┐
│                         VERCEL                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Next.js 14 (App Router)                 │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  /app/api/scan/sync     ← CLI sube resultados       │   │
│  │  /app/api/webhooks      ← Stripe, Slack             │   │
│  │  /app/api/auth          ← Supabase Auth wrapper     │   │
│  │  /app/dashboard         ← UI principal              │   │
│  └─────────────────────────────────────────────────────┘   │
│              Edge Functions (serverless, 0 cold start)       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       SUPABASE                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │     Auth     │  │   Realtime   │      │
│  │              │  │              │  │              │      │
│  │  • scans     │  │  • email     │  │  • webhooks  │      │
│  │  • issues    │  │  • OAuth     │  │  • live      │      │
│  │  • teams     │  │  • SSO*      │  │    updates   │      │
│  │  • orgs      │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                              │
│  Row Level Security (RLS) = cada user solo ve sus datos      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     EXTERNAL SERVICES                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Stripe  │  │  Resend  │  │  Slack   │  │ Upstash  │   │
│  │(Payments)│  │ (Emails) │  │  (Alerts)│  │  Redis   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Costos Operativos

| Servicio | Tier | Costo/mes |
|----------|------|-----------|
| Vercel | Pro | $20 |
| Supabase | Pro | $25 |
| Resend | Free | $0 |
| Upstash | Free | $0 |
| Stripe | % per tx | ~3% |
| **Total** | | **~$45/mes** |

**Breakeven:** 5 usuarios Pro ($9) o 3 Team ($19)

### 3.3 Flujo de Datos

```
┌─────────────────┐
│  CLI local      │
│  qodacode scan  │
└────────┬────────┘
         │ (JSON resultado)
         ▼
┌─────────────────────────────────────┐
│  POST /api/scan/sync                │
│  Headers: Authorization: Bearer xxx │
│  Body: { issues: [...], verdict }   │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Supabase PostgreSQL                │
│  INSERT INTO scans (...)            │
│  INSERT INTO issues (...)           │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Dashboard /app/dashboard           │
│  SELECT * FROM scans WHERE org_id   │
│  (RLS filtra automáticamente)       │
└─────────────────────────────────────┘
```

---

## 4. Dashboard Features

### 4.1 Vista por Tier

#### Pro ($9/dev/mes)

| Feature | Descripción |
|---------|-------------|
| Scan History | Últimos 90 días de scans |
| Trend Charts | Issues over time, security score evolution |
| Project Cards | Vista rápida de todos los proyectos |
| PDF Export | Reportes para stakeholders |
| Email Alerts | Notificación cuando se detectan critical issues |
| Settings | Preferencias personales |

#### Team ($19/dev/mes)

| Feature | Descripción |
|---------|-------------|
| Todo de Pro | + |
| Team Management | Invitar miembros, roles (admin/member/viewer) |
| Issue Assignment | Asignar issues a miembros del equipo |
| Slack Integration | Alertas en canal #security |
| Teams Integration | Para empresas Microsoft |
| Jira Integration | Auto-crear tickets |
| Calendar Integration | Programar security reviews |
| AGENT-002 Alerts | Detección de prompt injection |
| Weekly Digest | Email resumen semanal |

#### Business ($39/dev/mes)

| Feature | Descripción |
|---------|-------------|
| Todo de Team | + |
| SSO/SAML | Okta, Azure AD, Google Workspace |
| Audit Logs | Historial de acciones para compliance |
| Custom Rules | Reglas específicas de la empresa |
| API Access | REST API para integraciones custom |
| SLA | 99.9% uptime, soporte prioritario |
| Webhooks Custom | Integrar con cualquier servicio |
| AGENT-003 | Tool call injection detection |
| Dedicated Support | Slack channel con el team |

### 4.2 Dashboard UI Reference

**Inspiración de diseño:**

| Tool | Qué copiar |
|------|------------|
| **Snyk** | Security score cards, issue trends, fix flow |
| **SonarCloud** | Quality gates, project cards, metrics grid |
| **Aikido** | Modern UI, AI-native, startup-fresh |
| **Linear** | Keyboard shortcuts, command palette, animations |
| **Vercel** | Deployments UI, logs, team management |

**Stack UI:**
- Next.js 14 (App Router)
- Tailwind CSS + shadcn/ui
- Tremor (charts/metrics)
- Framer Motion (animations)
- Geist font (Vercel's font)
- Dark mode first

---

## 5. Integraciones

### 5.1 Mapa Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                      QODACODE INTEGRATIONS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ COMUNICACIÓN│  │  PROYECTO   │  │   CI/CD     │             │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤             │
│  │ Slack       │  │ Jira        │  │ GitHub      │             │
│  │ Teams       │  │ Linear      │  │ GitLab      │             │
│  │ Discord     │  │ Notion      │  │ Bitbucket   │             │
│  │ Email       │  │ Asana       │  │ Jenkins     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ CALENDARIO  │  │  TICKETING  │  │  DOCS       │             │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤             │
│  │ Google Cal  │  │ PagerDuty   │  │ Confluence  │             │
│  │ Outlook     │  │ ServiceNow  │  │ Notion      │             │
│  │ Cal.com     │  │ Opsgenie    │  │ GitBook     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Por Tier

| Tier | Integraciones |
|------|---------------|
| **Free** | GitHub Actions, Email básico |
| **Pro** | + Slack, Discord, Linear |
| **Team** | + Teams, Jira, Google Calendar, PagerDuty |
| **Business** | + SSO, ServiceNow, Confluence, Webhooks custom |

### 5.3 Casos de Uso

#### Slack Alert
```
┌──────────────────────────────────────────────────────────────┐
│  #security-alerts                                             │
│                                                               │
│  🔴 CRITICAL: SQL Injection detected                         │
│  ├─ File: api/users.py:45                                    │
│  ├─ Rule: SEC-002                                            │
│  ├─ Assigned: @maria                                         │
│  │                                                            │
│  │  [View in Dashboard]  [Fix Now]  [Ignore]                 │
│  │                                                            │
│  └─ Created issue: JIRA-1234                                 │
└──────────────────────────────────────────────────────────────┘
```

#### Email Weekly Digest
```
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  QODACODE WEEKLY SECURITY REPORT                             │
│  Project: my-saas-app                                         │
│  Week: Jan 13-20, 2026                                       │
│                                                               │
│  ─────────────────────────────────────────────────────────   │
│                                                               │
│  Security Score: B+ ↑ (was B-)                               │
│                                                               │
│  This Week:                                                   │
│  • 🔴 2 critical issues found                                │
│  • 🟡 5 high issues found                                    │
│  • ✅ 12 issues fixed                                        │
│  • 📈 Score improved 8%                                      │
│                                                               │
│  Top Contributors:                                            │
│  1. @maria - fixed 5 issues                                  │
│  2. @carlos - fixed 4 issues                                 │
│                                                               │
│  [View Full Report]  [Schedule Review]                       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

#### Calendar Integration
```
┌──────────────────────────────────────────────────────────────┐
│  📅 Security Review - Sprint 23                               │
│                                                               │
│  Every Friday 10:00 AM                                        │
│                                                               │
│  Agenda (auto-generated):                                     │
│  • 3 new critical issues this week                           │
│  • 12 issues fixed                                           │
│  • Security score: B+ (improved from B-)                     │
│                                                               │
│  Participants: @team-leads                                    │
│  [Join Meet]  [View Report]                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 6. Reglas AGENT (Premium Exclusivas)

### 6.1 Overview

| Rule ID | Nombre | Detecta | Severity | Tier |
|---------|--------|---------|----------|------|
| **AGENT-001** | Unsafe LLM Output | Usar respuesta LLM sin validación | High | Business |
| **AGENT-002** | Prompt Injection | `eval(llm_response)`, `exec(ai_code)` | Critical | Team |
| **AGENT-003** | Tool Call Injection | AI llama tools/APIs sin sanitizar | Critical | Business |
| **AGENT-004** | Memory Poisoning | Contexto manipulado en AI agents | High | Business |
| **AGENT-005** | RAG Injection | Datos maliciosos en vector DB | High | Business |

### 6.2 AGENT-002: Prompt Injection Detection

**El killer feature. Detecta:**

```python
# VULNERABLE - AGENT-002
response = openai.chat.completions.create(...)
code = response.choices[0].message.content
exec(code)  # PROMPT INJECTION RISK
```

**Patrones detectados:**
- `eval(llm_response)`
- `exec(ai_code)`
- `os.system(prompt_output)`
- `subprocess.run(ai_generated)`
- SQL construido con f-strings desde LLM response

**Por qué es killer feature:**
1. Snyk/SonarQube NO detectan esto (fueron creados pre-LLM)
2. Es un problema real y creciente (AI code execution)
3. Solo herramientas AI-native pueden entenderlo
4. Diferenciador claro vs competencia

### 6.3 AGENT-003: Tool Call Injection

**Detecta cuando un AI Agent ejecuta tools sin validación:**

```python
# VULNERABLE - AGENT-003
response = openai.chat.completions.create(tools=available_tools, ...)
tool_call = response.choices[0].message.tool_calls[0]
function_name = tool_call.function.name
function_args = json.loads(tool_call.function.arguments)

# Ejecución directa sin validación
result = globals()[function_name](**function_args)
```

**Fix recomendado:**
```python
# SEGURO
ALLOWED_TOOLS = {"read_file", "list_files"}  # Whitelist
DANGEROUS_PATHS = {"/etc", "/root", "~/.ssh"}

if function_name not in ALLOWED_TOOLS:
    raise SecurityError(f"Tool {function_name} not allowed")

if any(dangerous in str(function_args) for dangerous in DANGEROUS_PATHS):
    raise SecurityError("Dangerous path detected")

result = sandbox.execute(ALLOWED_TOOLS[function_name], **function_args)
```

---

## 7. Propiedad Intelectual

### 7.1 Separación IP

| Componente | Licencia | Dónde vive |
|------------|----------|------------|
| **CLI/TUI/MCP** | MIT (Open Source) | GitHub público |
| **Detection Engine** | MIT | GitHub público |
| **Reglas base (4000+)** | MIT | GitHub público |
| **Dashboard Frontend** | Propietario | Repo privado |
| **Dashboard API** | Propietario | Repo privado |
| **Reglas AGENT** | Propietario | Cloud only |
| **Team/Org Management** | Propietario | Cloud only |

### 7.2 Principios

1. **CLI/TUI/MCP siempre gratis** - Nunca paywall features existentes
2. **Premium es adicional** - No restricción, sino expansión
3. **Motor local siempre** - Código nunca sale de la máquina
4. **Cloud solo para colaboración** - Historial, teams, integraciones

### 7.3 Reglas Premium: Ejecución Local (CRÍTICO)

**Problema:** Si AGENT-002 requiere subir código a la nube, rompemos la promesa de privacidad.

**Solución:** Las reglas premium se descargan y ejecutan localmente.

```
┌─────────────────────────────────────────────────────────────┐
│  1. qodacode login                                           │
│     └─> Verifica licencia con cloud                         │
│                                                              │
│  2. Descarga reglas premium (si tiene licencia)             │
│     └─> ~/.qodacode/premium_rules.enc (firmadas)            │
│                                                              │
│  3. qodacode scan (local)                                    │
│     └─> Carga reglas base + reglas premium                  │
│     └─> TODO el escaneo es LOCAL                            │
│                                                              │
│  4. (Opcional) Sync resultados a dashboard                  │
│     └─> Solo metadata, NO código                            │
└─────────────────────────────────────────────────────────────┘
```

**Flujo de licencia:**
```python
# En el CLI
def load_premium_rules():
    license = verify_license_with_cloud()  # Solo verifica token
    if license.valid:
        rules = load_encrypted_rules("~/.qodacode/premium_rules.enc")
        return decrypt_and_verify(rules, license.key)
    return []
```

**Beneficios:**
- Escaneo 100% local (privacidad)
- Cloud solo verifica licencia (ligero)
- Reglas se actualizan con `qodacode update-rules`

---

## 8. Consideraciones Legales y Éticas

### 8.1 Legal

| Área | Mitigación |
|------|------------|
| **GDPR** | No almacenamos código, solo metadata de issues |
| **Secretos en logs** | Redactar secretos antes de guardar |
| **Liability** | Disclaimer: "Not a replacement for security audits" |
| **Open source licenses** | Auditar dependencias (MIT, Apache OK) |
| **AI advice liability** | "Suggestions only, review before applying" |

### 8.2 Ética

| Principio | Compromiso |
|-----------|------------|
| **Data privacy** | Nunca vender datos, ni anónimos |
| **Telemetría** | Opt-in only, desactivable |
| **Dark patterns** | Nunca. Valor claro, decisión libre |
| **Transparencia** | Publicar qué datos recolectamos |

### 8.3 Documentos Necesarios

- [ ] Privacy Policy
- [ ] Terms of Service
- [ ] Data Processing Agreement (para enterprise)
- [ ] Security whitepaper
- [ ] SOC 2 readiness (Year 2)

---

## 9. Website de Marketing

### 9.1 Estructura

```
qodacode.com/
├── /                   # Landing page
├── /pricing            # Pricing tiers
├── /docs               # Documentación (redirect a GitHub)
├── /blog               # Content marketing
├── /changelog          # Release notes
├── /login              # Redirect a dashboard
└── /dashboard          # App (subdomain: app.qodacode.com)
```

### 9.2 Landing Page Sections

1. **Hero** - "The first security scanner built for AI-assisted development"
2. **Problem** - "Enterprise tools don't understand AI-generated code"
3. **Solution** - CLI + TUI + MCP + Dashboard
4. **Features** - AGENT-002, Typosquatting, Auto-fix
5. **Pricing** - Free / Pro / Team / Business
6. **Testimonials** - (después de launch)
7. **CTA** - "pip install qodacode" / "Start Free"

### 9.3 Stack Website

| Componente | Herramienta |
|------------|-------------|
| Framework | Next.js 14 |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| Hosting | Vercel |
| Analytics | Plausible (privacy-first) |
| Forms | Formspree o Resend |

---

## 10. Roadmap

### 10.1 Fases

| Fase | Versión | Features | Target |
|------|---------|----------|--------|
| **Phase 5** | v0.6.0 | Context Awareness, AGENT-002, Enhanced fix_issue | Week 11-12 |
| **Phase 6** | v0.7.0 | Dashboard MVP, Slack, Email, GitHub sync | Week 13-14 |
| **Phase 7** | v0.8.0 | Teams, Jira, Calendar, AGENT-003 | Week 15-16 |
| **Phase 8** | v0.9.0 | SSO, Audit logs, API | Week 17-18 |
| **Phase 9** | v1.0.0 | Public launch, ProductHunt | Week 19-20 |

### 10.2 Integraciones por Fase

| Fase | Integraciones |
|------|---------------|
| v0.7.0 | Slack, Email, GitHub |
| v0.8.0 | Teams, Jira, Linear |
| v0.9.0 | Calendar, PagerDuty |
| v1.0.0 | Webhooks custom, Zapier |

### 10.3 AGENT Rules por Fase

| Fase | Rules |
|------|-------|
| v0.6.0 | AGENT-002 (Prompt Injection) |
| v0.8.0 | AGENT-001 (Unsafe LLM Output), AGENT-003 (Tool Call) |
| v1.0.0 | AGENT-004 (Memory Poisoning), AGENT-005 (RAG Injection) |

---

## 11. Métricas de Éxito

### 11.1 KPIs

| Métrica | Target Month 1 | Target Month 6 |
|---------|----------------|----------------|
| GitHub stars | 500 | 3,000 |
| PyPI downloads | 1,000 | 10,000 |
| Free users | 200 | 2,000 |
| Paid users | 5 | 100 |
| MRR | $50 | $1,500 |
| Churn rate | - | <5% |

### 11.2 Feature Metrics

| Feature | Success Metric |
|---------|----------------|
| AGENT-002 | 100% detection for known patterns |
| Context Awareness | 50% less false positives in tests |
| Enhanced fix_issue | 80% AI-applicable fixes |
| Dashboard | 70% DAU/MAU |
| Slack integration | 50% of Team users connect |

---

## 12. Competencia

### 12.1 Landscape

| Competidor | Fortaleza | Debilidad vs Qodacode |
|------------|-----------|----------------------|
| **Snyk** | Enterprise trust, CVE database | No entiende AI code, caro |
| **SonarQube** | On-prem, muchos lenguajes | Legacy, no AI-native |
| **Semgrep** | Custom rules, fast | No dashboard, no team features |
| **CodeClimate** | Quality metrics | No security focus |
| **Aikido** | Modern UI, startup | Menos reglas, más caro |

### 12.2 Diferenciadores Qodacode

| Diferenciador | Por qué importa |
|---------------|-----------------|
| **AI-native** | Detectamos AGENT-002, ellos no |
| **CLI-first** | Developer experience > dashboard |
| **Open core real** | CLI/TUI/MCP gratis forever |
| **MCP integration** | Único con server MCP nativo |
| **Precio accesible** | $9-39 vs $50k+/año |

---

## 13. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Baja adopción | Media | Alto | Content marketing, ProductHunt |
| Competencia copia AGENT-002 | Alta | Medio | First-mover advantage, velocidad |
| Problemas de scaling | Baja | Alto | Serverless architecture |
| Security breach | Baja | Crítico | No almacenar código, solo metadata |
| Dependencia de Supabase | Media | Medio | Diseño portable, no vendor lock-in |

---

## 14. Anexos

### 14.1 Database Schema (Draft)

```sql
-- Organizations
CREATE TABLE organizations (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  plan TEXT DEFAULT 'free',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Teams
CREATE TABLE teams (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES organizations(id),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  org_id UUID REFERENCES organizations(id),
  role TEXT DEFAULT 'member',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES organizations(id),
  name TEXT NOT NULL,
  repo_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scans
CREATE TABLE scans (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id),
  user_id UUID REFERENCES users(id),
  verdict TEXT NOT NULL,
  security_score TEXT,
  total_issues INTEGER,
  critical INTEGER,
  high INTEGER,
  medium INTEGER,
  low INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Issues
CREATE TABLE issues (
  id UUID PRIMARY KEY,
  scan_id UUID REFERENCES scans(id),
  project_id UUID REFERENCES projects(id),
  rule_id TEXT NOT NULL,
  severity TEXT NOT NULL,
  file_path TEXT NOT NULL,
  line_number INTEGER,
  message TEXT,
  code_snippet TEXT,
  fix_suggestion TEXT,
  status TEXT DEFAULT 'open',
  assigned_to UUID REFERENCES users(id),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Integrations
CREATE TABLE integrations (
  id UUID PRIMARY KEY,
  org_id UUID REFERENCES organizations(id),
  type TEXT NOT NULL,
  config JSONB,
  enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 14.2 API Endpoints (Draft)

```
POST   /api/auth/login
POST   /api/auth/register
POST   /api/auth/logout

GET    /api/organizations/:id
PATCH  /api/organizations/:id

GET    /api/projects
POST   /api/projects
GET    /api/projects/:id
DELETE /api/projects/:id

POST   /api/scans/sync          # CLI sube resultados
GET    /api/scans               # Lista de scans
GET    /api/scans/:id           # Detalle de scan

GET    /api/issues              # Lista de issues
PATCH  /api/issues/:id          # Update status, assign
POST   /api/issues/:id/ignore   # Ignorar issue

GET    /api/integrations
POST   /api/integrations
DELETE /api/integrations/:id

POST   /api/webhooks/stripe
POST   /api/webhooks/slack
```

---

## 15. Camino a 10/10 (Feedback Grok)

### 15.1 Evaluación Actual: 8/10

**Fortalezas validadas:**
- Tesis central fuerte ("tools legacy no entienden AI code")
- Open core limpio, arquitectura scalable low-cost
- Moat real en AGENT rules
- Pricing agresivo vs Snyk/Sonar ($50k+ enterprise)
- Vercel + Supabase = "oro puro" para MVP

### 15.2 Gaps para 10/10

#### 1. Privacy & Security (Must-have #1 Enterprise)

| Nivel | Acción |
|-------|--------|
| Day 1 | Nunca subir código/metadata sensible. Redactar secrets auto antes sync |
| Eleva | SOC2 Type 1 en 6 meses (mandatory para >$100k deals) |
| 10/10 | Zero-knowledge proof license verify (no cloud call offline) |

**Implementación privacy redact:**
```python
def redact_for_sync(issue: Issue) -> dict:
    """Redacta información sensible antes de sync a cloud."""
    return {
        "fingerprint": issue.fingerprint,  # Hash, no código
        "rule_id": issue.rule_id,
        "severity": issue.severity,
        "file_path": issue.file_path,
        "line": issue.line,
        "message": issue.message,
        # NUNCA: code_snippet, context, secrets
    }
```

#### 2. Accuracy & Coverage (Moat Real)

| Nivel | Acción |
|-------|--------|
| Actual | 4000+ rules + AGENT = bueno |
| Eleva | Reduce FP <10% con context awareness. Autofix >90% accuracy |
| 10/10 | Custom rules marketplace (users suben/share) + AI fine-tune por org |

#### 3. Scalability & Performance

| Nivel | Acción |
|-------|--------|
| Actual | Vercel/Supabase ok MVP |
| Eleva | Rate limiting API, queue syncs (Upstash Redis). Multi-tenant isolation |
| 10/10 | Dedicated instances Business tier (AWS/GCP isolated) |

**Nota Supabase:** RLS potente pero performance issues >10k rows. Planear migración.

#### 4. UX & Integrations

| Nivel | Acción |
|-------|--------|
| Actual | Dashboard MVP + Slack/Jira ok |
| Eleva | SSO day 1 Business (Okta/Azure). RBAC granular |
| 10/10 | GitHub App nativa (PR comments auto). Zapier/Make. Mobile alerts |

**Corte de scope crítico:** Solo Slack/Jira/GitHub v0.7. El resto mata timeline.

#### 5. Compliance & Support

| Nivel | Acción |
|-------|--------|
| Eleva | GDPR/CCPA out-of-box (data deletion API). SLA 99.9% |
| 10/10 | Whitepaper security + pentest público. Onboarding concierge Business |

### 15.3 Offline Mode (Enterprise Critical)

**Problema:** Users enterprise odian "no internet = no premium rules".

**Solución:**
```python
# ~/.qodacode/license_cache.json
{
    "token": "xxx",
    "verified_at": "2026-01-20T12:00:00Z",
    "expires_at": "2026-02-20T12:00:00Z",
    "grace_period_days": 30,
    "tier": "pro"
}

def verify_license():
    cache = load_license_cache()

    if is_online():
        # Verificar con cloud y actualizar cache
        return verify_with_cloud_and_cache()

    # Offline: usar cache si dentro de grace period
    if cache and within_grace_period(cache, days=30):
        return cache

    raise LicenseError("License expired. Connect to verify.")
```

### 15.4 Dashboard MVP (Corte Scope)

**Fase 1 (v0.7):** Solo lo esencial
- ✅ History de scans
- ✅ Trends (gráficas)
- ✅ Lista de issues
- ❌ Assignment (v0.8)
- ❌ Alerts (v0.8)
- ❌ Calendar/PagerDuty (v0.9+)

### 15.5 Pricing Ajustes

| Cambio | Razón |
|--------|-------|
| Annual discount 20% | Enterprise love |
| Trial 14 días Pro/Team | Reduce friction |
| Usage-based overage | Extra scans >limit |

### 15.6 Timeline Quirúrgico

| Período | Foco |
|---------|------|
| Day 1-30 | Privacy redact, SSO stub, accuracy tests en 100 repos reales |
| Mes 2-3 | Feedback loop users pagando (early access Business discount) |
| Mes 4+ | Custom rules + marketplace (viral + revenue) |

### 15.7 Métricas 10/10

| Métrica | Target |
|---------|--------|
| NPS | >8 |
| Churn | <5% |
| FP Rate | <10% |
| Autofix Accuracy | >90% |

---

## 16. Marketing Copy (Validado por Claude Code)

> Las siguientes citas son de Claude Code evaluando Qodacode como MCP tool.
> Esta es validación real del producto por un AI coding assistant.

### 16.1 Posicionamiento

**Tagline principal:**
> "No compite con AI coding assistants, los **complementa**."

**Explicación del valor:**
> "Qodacode es una herramienta especializada con garantías de cobertura. Yo puedo razonar sobre código pero sin garantía de encontrar todo. Por eso qodacode como MCP es útil - él escanea sistemáticamente, yo interpreto y arreglo."

**El problema que resuelve:**
> "Los LLMs necesitamos supervisión sistemática porque somos probabilísticos, no determinísticos."

### 16.2 Tabla Comparativa (Para Landing Page)

| Capacidad | Qodacode | AI Assistants (Claude/GPT) |
|-----------|----------|---------------------------|
| Scan automático de proyecto | ✅ Milisegundos | ❌ Tendría que leer archivo por archivo |
| Reglas AST precisas | ✅ Patrones exactos | ⚠️ Puede perder cosas |
| Detección de secretos | ✅ 700+ patrones | ⚠️ Si lo leo, lo veo |
| CVEs en dependencias | ✅ Base de datos actualizada | ❌ No tengo acceso a DBs de CVEs |
| Consistencia | ✅ Siempre detecta lo mismo | ❌ Puedo variar entre sesiones |
| Velocidad | ✅ <50ms | ❌ Minutos leyendo archivos |

### 16.3 Workflow Diagram (Watch Mode)

```
┌─────────────────────────────────────────┐
│     Terminal 1: Claude Code / Cursor     │
│     (Genera código rápido)               │
├─────────────────────────────────────────┤
│  > Escribiendo código...                 │
│  > Edit: src/api/auth.py                 │
│  > password = "admin123"  ← AI escribe   │
└──────────────────┬──────────────────────┘
                   │ archivo guardado
                   ▼
┌─────────────────────────────────────────┐
│     Terminal 2: qodacode watch           │
│     (Revisa calidad en tiempo real)      │
├─────────────────────────────────────────┤
│  $ qodacode watch --path ./src           │
│  👀 Watching for changes...              │
│  📁 Change detected: src/api/auth.py     │
│  ⚠ [CRITICAL] SEC-001: Hardcoded password│
└──────────────────┬──────────────────────┘
                   │ feedback inmediato
                   ▼
┌─────────────────────────────────────────┐
│     Código de producción                 │
│     (Seguro, robusto, mantenible)        │
└─────────────────────────────────────────┘
```

### 16.4 Value Props (Por qué tiene sentido)

1. **LLMs generamos código rápido pero imperfecto** - podemos introducir SQL injection, hardcodear secrets, olvidar error handling

2. **El watch mode es un safety net** - atrapa errores antes de que lleguen a producción

3. **No duplica funcionalidad** - AI razono y creo, qodacode valida sistemáticamente

### 16.5 Tabla de Valor Real

| Problema | Sin Qodacode | Con Qodacode |
|----------|--------------|--------------|
| Hardcodeo un secret | Llega a git | Lo detecta al instante |
| Escribo SQL vulnerable | Pasa desapercibido | Alerta inmediata |
| Olvido try/catch | Bug en producción | Flag antes de commit |

### 16.6 El Veredicto (Quote Final)

> "Es una **capa de QA automatizada** para desarrollo con AI. El concepto es sólido - los LLMs necesitamos supervisión sistemática porque somos probabilísticos, no determinísticos."
>
> "¿Quién desarrolló la herramienta? El approach es pragmático."
>
> — Claude Code, evaluando Qodacode

---

## 17. User Feedback: Claude Code como Usuario

### 17.1 Score Actual: 7.5/10

> "Es una herramienta sólida que resuelve un problema real."

**Lo que le gusta:**
- ✅ MCP Integration - Usa sin salir del flujo
- ✅ Watch mode - Feedback en tiempo real
- ✅ Severidad clara - Sabe qué es urgente
- ✅ Rápido - <50ms para análisis básico
- ✅ Multi-engine - Combina SAST, secrets, dependencies

**Feedback constructivo:**
- ⚠️ Algunos falsos positivos (ej: `decrypt_api_key()` no es un leak)
- ⚠️ Falta modo "AI-assisted" con contexto semántico
- ⚠️ Documentación de cómo ignorar FPs (`# qodacode-ignore`?)

### 17.2 Lista de Mejoras Solicitadas

| # | Mejora | Por qué | Estado |
|---|--------|---------|--------|
| 1 | `# qodacode-ignore: SEC-001` | Suprimir FPs por línea | ✅ Done |
| 2 | `.qodacodeignore` | Ignorar archivos/patrones | ✅ Done |
| 3 | Contexto semántico | Entender código seguro automáticamente | ✅ Done |
| 4 | MCP fix_issue mejorado | Código exacto, no solo sugerencia | 🟡 Parcial |
| 5 | Baseline mode | Solo reportar issues nuevos | ✅ Done |
| 6 | Severity tuning | Bajar severidad por proyecto | 🔴 Pendiente |
| 7 | Output en español | Mercado LATAM | 🔴 Pendiente |
| 8 | VSCode extension | Inline warnings mientras escribo | 🔴 Futuro |
| 9 | `qodacode diff` | Solo escanear cambios del commit | 🔴 Pendiente |
| 10 | Dashboard web | Historial y tendencias | 🟡 PRD listo |

### 17.3 Path to 10/10

**Para 9/10** (implementar primero):
1. `# qodacode-ignore: RULE-ID` - Inline suppression
2. `.qodacodeignore` file - Como .gitignore
3. Baseline mode (`--baseline`) - Ignorar issues existentes
4. Contexto semántico básico - Patterns seguros

**Para 10/10:**
> "Que el contexto semántico use un LLM pequeño para eliminar falsos positivos automáticamente (sin configuración manual)."

### 17.4 Roadmap Técnico Actualizado

| Versión | Features | Score Target |
|---------|----------|--------------|
| v0.5.0 | MCP, Watch, Multi-engine | 7.5/10 |
| v0.6.0 | `# qodacode-ignore`, `.qodacodeignore`, `--baseline`, Semantic context | **9/10** ✅ |
| v0.7.0 | `qodacode diff`, Dashboard MVP | 9.5/10 |
| v0.8.0 | LLM-assisted FP elimination | 9.8/10 |
| v1.0.0 | VSCode extension, Full i18n | 10/10 |

---

## 18. Próximos Pasos

### ✅ Completado en v0.6.0 (Score: 9/10)
1. [x] **`# qodacode-ignore`** - Inline suppression comments
2. [x] **`.qodacodeignore`** - File/pattern exclusion
3. [x] **`--baseline` mode** - Solo issues nuevos
4. [x] **Contexto semántico** - Patterns seguros (decrypt_, hash_, os.environ, etc.)

### Inmediato (Pre-launch)
5. [ ] **GitHub launch** - README badges, CONTRIBUTING.md, Issues templates

### v0.7.0
6. [ ] **AGENT-002** - Prompt injection detection
7. [ ] **`qodacode diff`** - Solo cambios del commit
8. [ ] **Dashboard MVP** - History + trends

### Futuro
9. [ ] **LLM-assisted FP elimination** - Auto-context con modelo pequeño
10. [ ] **VSCode extension** - Inline warnings
11. [ ] **Output español** - i18n para LATAM

---

## 19. MCP Proactivo (Premium Feature)

### 19.1 Concepto

**Problema actual:** El MCP es pasivo - Claude Code tiene que llamarlo explícitamente.

**Visión:** Qodacode MCP se convierte en un "guardian proactivo" que:
- Intercepta cambios antes de que se guarden
- Fuerza validación antes de commits
- Sugiere mejoras mientras se escribe
- Bloquea acciones peligrosas en tiempo real

### 19.2 Modos de Proactividad

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP PROACTIVITY LEVELS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LEVEL 0: PASSIVE (Free)                                        │
│  └─ Claude Code llama a Qodacode cuando quiere                  │
│     "Hey qodacode, scan this file"                              │
│                                                                  │
│  LEVEL 1: REACTIVE (Pro)                                        │
│  └─ Qodacode sugiere después de cada cambio                     │
│     "I noticed you just wrote a password. Should I scan?"       │
│                                                                  │
│  LEVEL 2: PROACTIVE (Team)                                      │
│  └─ Qodacode escanea automáticamente cada cambio                │
│     "Auto-scanned: Found 2 issues in your last edit"            │
│                                                                  │
│  LEVEL 3: GUARDIAN (Business)                                   │
│  └─ Qodacode puede bloquear/rechazar cambios peligrosos         │
│     "BLOCKED: Cannot commit with critical security issues"       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 19.3 Implementación Técnica

#### Tool Hooks (MCP Enhanced)

```python
# Nuevos tools MCP para modo proactivo
@mcp_tool(name="register_file_hook")
def register_file_hook(
    pattern: str,  # "*.py", "src/**/*.ts"
    on_change: str,  # "scan", "alert", "block"
    severity_threshold: str = "critical"
) -> dict:
    """Register a hook to be called when matching files change."""
    pass

@mcp_tool(name="register_commit_hook")
def register_commit_hook(
    block_on: str = "critical",  # "critical", "high", "all"
    auto_fix: bool = False
) -> dict:
    """Register pre-commit validation hook."""
    pass

@mcp_tool(name="get_realtime_issues")
def get_realtime_issues() -> list:
    """Get issues from the background watcher."""
    pass
```

#### Background Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    QODACODE DAEMON                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │  File Watcher   │────▶│  Issue Cache    │                   │
│  │  (watchdog)     │     │  (in-memory)    │                   │
│  └─────────────────┘     └────────┬────────┘                   │
│                                   │                             │
│                                   ▼                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    MCP Server                            │   │
│  │                                                          │   │
│  │  /tools/scan           ← Escaneo bajo demanda           │   │
│  │  /tools/get_issues     ← Issues actuales                │   │
│  │  /tools/register_hook  ← Registrar hooks                │   │
│  │  /events/issue_found   → Push a Claude Code             │   │
│  │  /events/scan_complete → Push cuando termina scan       │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 19.4 Casos de Uso Premium

#### Caso 1: Auto-Scan on Save (Team)

```
Usuario escribe código en Cursor/VSCode con Claude
     │
     ▼
Claude genera: api_key = "sk-ant-api03-xxx"
     │
     ▼
Archivo guardado (Cmd+S)
     │
     ▼
Qodacode daemon detecta cambio
     │
     ▼
Auto-scan en background (<50ms)
     │
     ▼
Push evento a Claude Code:
"⚠️ CRITICAL: Hardcoded API key detected in config.py:42"
     │
     ▼
Claude Code automáticamente sugiere:
"I just detected a security issue. Let me fix that:
 api_key = os.environ.get('ANTHROPIC_API_KEY')"
```

#### Caso 2: Pre-Commit Block (Business)

```
Usuario: "Claude, commit this code"
     │
     ▼
Claude Code intenta ejecutar: git commit -m "Add auth"
     │
     ▼
Qodacode pre-commit hook intercepta
     │
     ▼
Full scan del staged content
     │
     ▼
Si encuentra critical issues:
     │
     ├─▶ BLOQUEA el commit
     │
     └─▶ Retorna a Claude Code:
         "Cannot commit: 2 critical security issues found.
          1. SQL injection in users.py:78
          2. Hardcoded secret in config.py:12

          Fix these issues first or use --force to override."
```

#### Caso 3: Context-Aware Suggestions (Business)

```
Claude Code está escribiendo código de autenticación
     │
     ▼
Qodacode detecta contexto: "auth module"
     │
     ▼
Proactivamente carga reglas relevantes:
- Password hashing requirements
- Session management
- Token validation
     │
     ▼
Push a Claude Code:
"📋 CONTEXT: You're working on authentication.
 Here are the security patterns you should follow:
 1. Always hash passwords with bcrypt
 2. Use secure session tokens
 3. Validate all input

 Should I scan for these patterns as you write?"
```

### 19.5 Integration con Claude Code

```python
# Ejemplo de prompt que Qodacode podría inyectar
SYSTEM_PROMPT_ADDITION = """
You have access to qodacode MCP server which provides real-time
security scanning. The following rules are enforced:

MANDATORY BEHAVIORS:
1. Before any git commit, ALWAYS call qodacode.scan_staged()
2. When writing security-sensitive code (auth, crypto, API),
   call qodacode.get_context_rules() first
3. If qodacode returns CRITICAL issues, DO NOT proceed until fixed

AUTOMATIC BEHAVIORS (handled by qodacode):
- File changes are auto-scanned in background
- You will receive push notifications for new issues
- Critical issues block git operations automatically

Current project security score: B+ (87/100)
Open issues: 3 critical, 12 high, 45 medium
"""
```

### 19.6 Pricing Impact

| Feature | Free | Pro | Team | Business |
|---------|------|-----|------|----------|
| Passive MCP | ✅ | ✅ | ✅ | ✅ |
| Reactive suggestions | ❌ | ✅ | ✅ | ✅ |
| Auto-scan on save | ❌ | ❌ | ✅ | ✅ |
| Pre-commit blocks | ❌ | ❌ | ❌ | ✅ |
| Context-aware rules | ❌ | ❌ | ❌ | ✅ |
| Custom hooks | ❌ | ❌ | ❌ | ✅ |

### 19.7 Diferenciador vs Competencia

| Aspecto | Qodacode Proactive | Snyk | SonarQube |
|---------|-------------------|------|-----------|
| MCP Integration | ✅ Native | ❌ | ❌ |
| Real-time push | ✅ | ❌ | ❌ |
| AI-aware hooks | ✅ | ❌ | ❌ |
| Context injection | ✅ | ❌ | ❌ |
| Works with Claude Code | ✅ Native | ❌ | ❌ |

### 19.8 Roadmap MCP Proactivo

| Versión | Feature |
|---------|---------|
| v0.8.0 | Reactive suggestions (Pro) |
| v0.9.0 | Auto-scan on save (Team) |
| v1.0.0 | Pre-commit blocks (Business) |
| v1.1.0 | Context-aware rules (Business) |
| v1.2.0 | Custom hooks API (Business) |

---

*Documento vivo. Última actualización: 2026-01-21*
