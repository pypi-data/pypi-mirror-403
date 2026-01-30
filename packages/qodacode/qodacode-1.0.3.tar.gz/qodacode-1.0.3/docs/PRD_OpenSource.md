# PRD: Qodacode Open Source Strategy

> **Objetivo**: Crear un proyecto open source tan complejo y valioso que nadie quiera replicarlo - preferirán integrarse con nosotros.

---

## 1. Filosofía: Complejidad como Moat

### 1.1 El Problema
```
❌ Open source típico:
   - Código simple → Fácil de forkear
   - Sin datos propietarios → Fácil de replicar
   - Documentación pobre → Fácil de "mejorar"

✅ Qodacode approach:
   - Arquitectura multi-capa → 6+ meses replicar
   - Datos propietarios → Investigación única
   - Docs excelentes → Ya somos el estándar
```

### 1.2 Ejemplos de Éxito

| Proyecto | Open Source | Por qué nadie lo replica |
|----------|-------------|--------------------------|
| **Semgrep** | Sí | 4 años de desarrollo, OCaml, 3000+ reglas |
| **Kubernetes** | Sí | Complejidad extrema, Google backing |
| **Linux** | Sí | 30+ años, millones de líneas |
| **Terraform** | Sí | Ecosystem de providers |

---

## 2. Arquitectura de Blindaje

### 2.1 Capas de Complejidad

```
┌─────────────────────────────────────────────────────────────┐
│  CAPA 1: Interfaces (Python - legible)                      │
│  CLI, TUI, MCP Server                                       │
│  → Fácil de entender, difícil de mejorar                   │
├─────────────────────────────────────────────────────────────┤
│  CAPA 2: Orquestación (Python - complejo)                  │
│  Multi-engine coordination, deduplication, context          │
│  → Lógica de negocio densa, muchos edge cases              │
├─────────────────────────────────────────────────────────────┤
│  CAPA 3: Detection Core (Rust - compilado)                 │
│  Fingerprinting, semantic analysis, pattern matching        │
│  → Binario opaco, algoritmos propietarios                  │
├─────────────────────────────────────────────────────────────┤
│  CAPA 4: Data Layer (Propietario)                          │
│  Typosquatting DB, Malware signatures, Rule configs        │
│  → Investigación única, no replicable                      │
├─────────────────────────────────────────────────────────────┤
│  CAPA 5: Cloud Services (Cerrado)                          │
│  Premium rules, LLM analysis, Dashboard, Licensing         │
│  → Server-side, imposible de piratear                      │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Distribución de Código

```
qodacode/
├── cli.py              # Open - 2000 líneas
├── interactive.py      # Open - 1200 líneas
├── mcp_server.py       # Open - 400 líneas
├── orchestrator.py     # Open - Complejo
├── scanner.py          # Open - Complejo
├── reporter.py         # Open - Complejo
│
├── _core/              # Rust compiled (.so/.pyd)
│   ├── fingerprint     # Algoritmo hash propietario
│   ├── semantic        # Pattern matching optimizado
│   ├── similarity      # Levenshtein + homoglyphs
│   └── dedup           # Deduplication logic
│
├── engines/            # Open - Wrappers
│   ├── treesitter/     # AST parsing
│   ├── semgrep/        # SAST integration
│   ├── gitleaks/       # Secret detection
│   └── osv/            # Vulnerability DB
│
├── rules/              # Open - 50 reglas básicas
│   ├── security.py
│   ├── robustness.py
│   └── ...
│
├── typosquatting/      # Open - Algoritmos
│   ├── database.py     # 🔒 Datos propietarios
│   ├── detector.py
│   └── similarity.py
│
└── context/            # Open - Lógica compleja
    ├── deduplicator.py
    └── semantic.py
```

### 2.3 Iron Core Strategy: Por qué Rust

**El Problema con Python Puro:**
```
Python puro = "Código blando"
- Claude Code lo replica en 30 segundos
- Un junior lo entiende y lo forkea
- Sin barrera técnica real
```

**La Solución: Híbrido Python + Rust**
```
┌─────────────────────────────────────────────────┐
│  LA CARA (Python)                                │
│  CLI, TUI, MCP Server                            │
│  → Fácil de distribuir: pip install qodacode    │
│  → Fácil de usar: qodacode check                │
├─────────────────────────────────────────────────┤
│  EL CEREBRO (Rust - PyO3/Maturin)               │
│  Algoritmos, Data Moats, Pattern Matching        │
│  → Compilado a binario .so/.pyd                  │
│  → Lifetimes, Borrow Checker, Unsafe blocks     │
│  → LLMs cometen errores graves en Rust          │
└─────────────────────────────────────────────────┘
```

**Por qué funciona:**

| Aspecto | Python | Rust |
|---------|--------|------|
| Barrera intelectual | Baja | Alta (memory management) |
| LLM Resistance | Muy baja | Media-Alta |
| Performance | Lenta | 10-100x más rápida |
| Replicación | Minutos | Semanas/Meses |

**Referentes de éxito:**
- **Ruff** (linter Python) → Core en Rust, nadie lo replica
- **Pydantic V2** → Core en Rust, 50x más rápido
- **Semgrep** → Core en OCaml, 4 años de desarrollo

---

## 3. Data Moats (Datos Propietarios)

### 3.1 Typosquatting Database

```python
# NO replicable - requiere investigación manual
KNOWN_MALICIOUS_PACKAGES = {
    # Python
    "reqeusts": {"target": "requests", "type": "typo", "confirmed": True},
    "colourama": {"target": "colorama", "type": "typo", "confirmed": True},
    "python-dateutil": {"target": "python-dateutil", "type": "official"},
    "python-dateutilz": {"target": "python-dateutil", "type": "typo", "malware": True},

    # npm
    "electorn": {"target": "electron", "type": "typo", "confirmed": True},
    "crossenv": {"target": "cross-env", "type": "typo", "malware": True},

    # ... 50+ paquetes investigados manualmente
}

# Homoglyph mappings - investigación Unicode
HOMOGLYPH_MAP = {
    'a': ['а', 'ɑ', 'α'],  # Cyrillic, Latin, Greek
    'e': ['е', 'ё', 'ε'],
    'o': ['о', 'ο', '0'],
    'i': ['і', 'ι', '1', 'l'],
    # ... 100+ mappings
}

# Keyboard proximity matrices por layout
QWERTY_ADJACENCY = {
    'q': ['w', 'a', '1', '2'],
    'w': ['q', 'e', 'a', 's', '2', '3'],
    # ... matriz completa
}
```

### 3.2 Security Rule Signatures

```python
# Patrones únicos desarrollados internamente
SECRET_PATTERNS = {
    "anthropic_api_key": {
        "pattern": r"sk-ant-api\d{2}-[A-Za-z0-9_-]{95}",
        "entropy_threshold": 4.5,
        "false_positive_hints": ["test", "example", "xxx"],
    },
    "stripe_restricted_key": {
        "pattern": r"rk_(live|test)_[A-Za-z0-9]{24}",
        "severity": "critical",
        "auto_revoke_url": "https://dashboard.stripe.com/apikeys",
    },
    # ... 50+ patrones custom
}
```

### 3.3 Semantic Safe Patterns

```python
# Base de conocimiento de patrones seguros
# Desarrollado por análisis de 1000+ repos reales
SAFE_PATTERNS = [
    # Decrypt functions - 15 variaciones
    r"decrypt[_\w]*\s*\(",
    r"\.decrypt\s*\(",
    r"cipher\.decrypt",
    r"Fernet\s*\([^)]*\)\.decrypt",

    # Env reads - 20 variaciones
    r"os\.environ\s*[\[\.]",
    r"os\.getenv\s*\(",
    r"process\.env\.",
    r"import\.meta\.env\.",
    r"dotenv\.get\(",

    # ... 100+ patrones documentados
]
```

---

## 4. Rust Core Module

### 4.1 Por qué Rust

| Aspecto | Python | Rust |
|---------|--------|------|
| Velocidad | 1x | 50-100x |
| Legibilidad | Alta | Media |
| Reverse engineering | Trivial | Muy difícil |
| Memory safety | GC | Zero-cost |
| Python bindings | N/A | PyO3 (excelente) |

### 4.2 Módulos a Migrar

```rust
// qodacode-core/src/lib.rs

/// Fingerprint computation - algoritmo propietario
/// No usar MD5/SHA simple - incluir normalización custom
pub fn compute_fingerprint(
    filepath: &str,
    rule_id: &str,
    snippet: &str,
    salt: &[u8],
) -> String {
    let normalized = normalize_code(snippet);
    let input = format!("{}:{}:{}", filepath, rule_id, normalized);

    // BLAKE3 con salt propietario
    let mut hasher = blake3::Hasher::new_keyed(salt);
    hasher.update(input.as_bytes());
    let hash = hasher.finalize();

    // Truncar a 12 chars hex
    hex::encode(&hash.as_bytes()[..6])
}

/// Semantic pattern matching - optimizado
pub fn is_safe_pattern(
    snippet: &str,
    filepath: &str,
    patterns: &CompiledPatterns,
) -> Option<SafeMatch> {
    // Aho-Corasick para multi-pattern matching
    // 100x más rápido que regex iterativo
    patterns.find_first(snippet, filepath)
}

/// Similarity computation para typosquatting
pub fn compute_similarity(
    pkg_name: &str,
    known_packages: &PackageIndex,
) -> Vec<SimilarityMatch> {
    // Levenshtein + Homoglyph + Keyboard proximity
    // Algoritmo custom con pesos ajustados
}
```

### 4.3 Build System

```toml
# Cargo.toml
[package]
name = "qodacode-core"
version = "0.1.0"

[lib]
crate-type = ["cdylib"]  # Compilar como shared library

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
blake3 = "1.5"
aho-corasick = "1.1"
regex = "1.10"
rayon = "1.8"  # Parallel processing

[profile.release]
lto = true          # Link-time optimization
codegen-units = 1   # Mejor optimización
strip = true        # Remove debug symbols
```

```python
# Python wrapper - qodacode/_core/__init__.py
try:
    from qodacode._core.qodacode_core import (
        compute_fingerprint,
        is_safe_pattern,
        compute_similarity,
    )
    RUST_CORE_AVAILABLE = True
except ImportError:
    # Fallback a Python puro (más lento, código visible)
    from qodacode._core._fallback import *
    RUST_CORE_AVAILABLE = False
```

---

## 5. Velocidad de Innovación

### 5.1 Release Cadence

```
Cuando alguien forkea v0.5.0...

Semana 1:  Fork creado
Semana 2:  Entienden el código
Semana 3:  Hacen cambios menores
Semana 4:  Nosotros lanzamos v0.6.0 con 4 features nuevos
Semana 6:  Su fork está 2 versiones atrás
Semana 8:  Abandonan el fork
```

### 5.2 Roadmap Agresivo

| Versión | Fecha | Features | Complejidad Añadida |
|---------|-------|----------|---------------------|
| v0.6.0 | Ene 2025 | Semantic context, baseline, inline ignore | +1500 LOC |
| v0.7.0 | Feb 2025 | Rust core, `qodacode diff` | +2000 LOC Rust |
| v0.8.0 | Mar 2025 | LLM-assisted FP, AGENT-002 | +1000 LOC |
| v0.9.0 | Abr 2025 | Dashboard MVP, Team features | +3000 LOC |
| v1.0.0 | May 2025 | VSCode extension, i18n | +2000 LOC |

**Total en 5 meses**: +9500 líneas de código nuevo

### 5.3 Feature Velocity vs Forks

```
                    Qodacode Main
                         │
    v0.5 ────────────────┼─────────────────────────────►
                         │
         Fork A ─────────┤
                         │ (muere en v0.5)
                         │
    v0.6 ────────────────┼─────────────────────────────►
                         │
              Fork B ────┤
                         │ (muere en v0.6)
                         │
    v0.7 ────────────────┼─────────────────────────────►
                         │
                   Fork C│
                         │ (se rinde, contribuye al main)
```

---

## 6. Documentación como Moat

### 6.1 Docs Exhaustivos

```
docs/
├── getting-started/
│   ├── installation.md
│   ├── first-scan.md
│   └── configuration.md
│
├── guides/
│   ├── ci-cd-integration.md
│   ├── custom-rules.md
│   ├── false-positive-handling.md
│   └── mcp-integration.md
│
├── reference/
│   ├── cli-commands.md
│   ├── tui-commands.md
│   ├── mcp-tools.md
│   └── api-reference.md
│
├── architecture/
│   ├── detection-engine.md
│   ├── deduplication.md
│   ├── semantic-analysis.md
│   └── typosquatting.md
│
└── contributing/
    ├── development-setup.md
    ├── testing.md
    ├── code-style.md
    └── release-process.md
```

### 6.2 Por qué Docs = Moat

1. **SEO**: "qodacode security scanner" → nuestros docs
2. **Tutoriales**: Todos apuntan a Qodacode
3. **Stack Overflow**: Respuestas referencian Qodacode
4. **Curva de aprendizaje**: Ya invertida en Qodacode

---

## 7. Licencia Estratégica

### 7.1 Opciones

| Licencia | Permite forks comerciales | Obliga contribuir back |
|----------|---------------------------|------------------------|
| MIT | ✅ Sí | ❌ No |
| Apache 2.0 | ✅ Sí | ❌ No |
| GPL v3 | ✅ Sí | ✅ Sí (copyleft) |
| AGPL v3 | ✅ Sí | ✅ Sí (incluso SaaS) |
| BSL 1.1 | ❌ No (3 años) | N/A |
| SSPL | ❌ No (SaaS) | N/A |

### 7.2 Recomendación: Apache 2.0 + CLA

```
Apache 2.0:
- Permite uso comercial
- Requiere attribution
- Protección de patentes
- Empresas lo aceptan

+ Contributor License Agreement (CLA):
- Nosotros podemos relicenciar
- Podemos usar contribuciones en versión comercial
- Control sobre el proyecto
```

---

## 8. Integración > Competencia

### 8.1 Hacer que nos integren

```yaml
# .github/workflows/security.yml (de OTROS proyectos)
- name: Security Scan
  uses: qodacode/action@v1  # Nos usan a nosotros
```

```json
// claude_desktop_config.json (de usuarios de Claude)
{
  "mcpServers": {
    "qodacode": {  // Nos usan a nosotros
      "command": "qodacode",
      "args": ["serve"]
    }
  }
}
```

### 8.2 Ecosystem Lock-in

```
┌─────────────────────────────────────────────┐
│  GitHub Actions      →  qodacode/action     │
│  GitLab CI           →  qodacode ci         │
│  VSCode              →  qodacode extension  │
│  Cursor              →  qodacode extension  │
│  Claude Code         →  qodacode MCP        │
│  Windsurf            →  qodacode MCP        │
│  Pre-commit          →  qodacode hook       │
└─────────────────────────────────────────────┘
          │
          ▼
    Qodacode es el ESTÁNDAR
    para security scanning
```

---

## 9. Métricas de Éxito

### 9.1 Adopción

| Métrica | 3 meses | 6 meses | 12 meses |
|---------|---------|---------|----------|
| GitHub stars | 500 | 2,000 | 10,000 |
| PyPI downloads/month | 1,000 | 10,000 | 50,000 |
| Forks activos | <5 | <10 | <20 |
| Contributors | 5 | 20 | 50 |

### 9.2 Complejidad

| Métrica | Actual | Target |
|---------|--------|--------|
| Total LOC | ~8,000 | 20,000 |
| Rust LOC | 0 | 5,000 |
| Test coverage | 42% | 80% |
| Docs pages | 10 | 50 |
| Engines integrados | 5 | 8 |

### 9.3 Moat Strength

```
Tiempo para replicar Qodacode desde cero:

Hoy (v0.5):     3 meses
v0.7 (Rust):    6 meses
v1.0:           12 meses
v2.0:           "No vale la pena, mejor integro"
```

---

## 10. Fases de Implementación

### FASE 1: Fundación (Semanas 1-2) ✅ COMPLETADA
**Objetivo**: Base sólida de código y tests

| Task | Status | Archivos |
|------|--------|----------|
| Semantic context analysis | ✅ | `context/semantic.py` |
| Inline ignore comments | ✅ | `context/deduplicator.py` |
| Baseline mode | ✅ | `context/deduplicator.py` |
| Test coverage 165 tests | ✅ | `tests/test_*.py` |
| Documentación CLI/TUI | ✅ | `CLI.md`, `TUI.md`, `README.md` |

---

### FASE 2: Rust Core Setup (Semanas 3-4) ✅ COMPLETADA
**Objetivo**: Infraestructura Rust + PyO3

| Task | Status | Archivos |
|------|--------|----------|
| Crear `rust/` directory | ✅ | `rust/Cargo.toml`, `rust/pyproject.toml` |
| Setup PyO3 bindings | ✅ | `rust/src/lib.rs` |
| Migrar `compute_fingerprint` | ✅ | `rust/src/fingerprint.rs` |
| Implementar similarity algorithms | ✅ | `rust/src/similarity.rs` |
| Implementar pattern matching | ✅ | `rust/src/patterns.rs` |
| Fallback Python | ✅ | `qodacode/_core/__init__.py`, `qodacode/_core/_fallback.py` |
| Benchmark suite | ✅ | `rust/benches/benchmarks.rs` |
| Tests de integración | ✅ | `tests/test_rust_core.py` |
| CI para Rust builds | ⬜ | `.github/workflows/rust.yml` |

**Complejidad añadida**: ~2000 LOC (Rust + Python)

---

### FASE 3: Algoritmos + MCP Proactivo (Semanas 5-6) ✅ COMPLETADA
**Objetivo**: Mover lógica crítica a Rust + MCP Proactivo

| Task | Status | Archivos |
|------|--------|----------|
| Levenshtein optimizado | ✅ | `rust/src/similarity.rs` |
| Homoglyph detection | ✅ | `rust/src/similarity.rs` (integrado) |
| Keyboard proximity | ✅ | `rust/src/similarity.rs` (integrado) |
| Semantic pattern matcher | ✅ | `rust/src/patterns.rs` |
| Aho-Corasick multi-pattern | ✅ | `rust/src/patterns.rs` (integrado) |
| Benchmark suite | ✅ | `rust/benches/benchmarks.rs` |
| **Proactive Daemon** | ✅ | `qodacode/daemon.py` |
| **MCP Proactive Tools (8)** | ✅ | `qodacode/mcp_server.py` |
| **Daemon Tests** | ✅ | `tests/test_daemon.py` |
| Compilar y publicar wheel | ⬜ | `maturin build --release` |
| Performance tests | ⬜ | `tests/test_performance.py` |

**Complejidad añadida**: ~2000 LOC Rust + ~1000 LOC Python (daemon + MCP tools)

---

### FASE 4: Data Moats (Semanas 7-8) ✅ COMPLETADA
**Objetivo**: Datos propietarios embebidos en binario Rust

| Task | Status | Archivos |
|------|--------|----------|
| Embed malicious packages DB | ✅ | `rust/src/data.rs` (150+ packages) |
| Embed homoglyph mappings | ✅ | `rust/src/similarity.rs` (integrado) |
| Embed keyboard matrices | ✅ | `rust/src/similarity.rs` (integrado) |
| Embed secret signatures | ✅ | `rust/src/data.rs` (45+ patterns) |
| PyPI/NPM top packages | ✅ | `rust/src/data.rs` (160+ packages) |
| Python bindings | ✅ | `rust/src/lib.rs` (8 functions) |
| Python fallback | ✅ | `qodacode/_core/_fallback.py` |
| Integrity verification | ✅ | `rust/src/data.rs` (checksums) |
| Data Moats tests | ✅ | `tests/test_rust_core.py` (80 tests) |
| **AI/ML Ecosystem** | ✅ | HuggingFace, LangChain, vLLM, etc. |
| **Multi-ecosystem typosquats** | ✅ | PyPI, NPM, Cargo, Go Modules |

**Complejidad añadida**: ~1500 LOC Rust + Python fallback
**Fuentes**: Gemini AI, Grok (xAI), Check Point, Socket.dev, GitGuardian

---

### FASE 5: CLI Enhancements (Semanas 9-10)
**Objetivo**: Nuevos comandos y features

| Task | Status | Archivos |
|------|--------|----------|
| `qodacode diff` command | ⬜ | `qodacode/cli.py` |
| `qodacode audit --deep` | ⬜ | `qodacode/cli.py` |
| `qodacode benchmark` | ⬜ | `qodacode/cli.py` |
| Progress bars mejoradas | ⬜ | `qodacode/reporter.py` |
| JSON streaming output | ⬜ | `qodacode/formatters/` |
| SARIF 2.1 compliance | ⬜ | `qodacode/formatters/sarif.py` |

**Complejidad añadida**: ~1500 LOC Python

---

### FASE 6: Integrations (Semanas 11-12)
**Objetivo**: Ecosystem lock-in

| Task | Status | Archivos |
|------|--------|----------|
| GitHub Action oficial | ⬜ | `.github/action.yml` |
| Pre-commit hook | ⬜ | `.pre-commit-hooks.yaml` |
| VSCode extension básica | ⬜ | `vscode-extension/` |
| GitLab CI template | ⬜ | `templates/gitlab-ci.yml` |
| Docker image | ⬜ | `Dockerfile` |
| Homebrew formula | ⬜ | `Formula/qodacode.rb` |

**Complejidad añadida**: ~2000 LOC mixto

---

### FASE 7: LLM Enhancement (Semanas 13-14)
**Objetivo**: AI-assisted analysis

| Task | Status | Archivos |
|------|--------|----------|
| LLM false positive filter | ⬜ | `qodacode/ai/fp_filter.py` |
| AGENT-002 orchestration | ⬜ | `qodacode/ai/agent.py` |
| Batch processing pipeline | ⬜ | `qodacode/ai/batch.py` |
| Cost optimization | ⬜ | `qodacode/ai/cost.py` |
| Ollama integration | ⬜ | `qodacode/ai/providers/ollama.py` |
| Caching layer | ⬜ | `qodacode/ai/cache.py` |

**Complejidad añadida**: ~1500 LOC Python

---

### FASE 8: Dashboard MVP (Semanas 15-18)
**Objetivo**: Interfaz web (Premium)

| Task | Status | Archivos |
|------|--------|----------|
| FastAPI backend | ⬜ | `qodacode-server/` |
| React dashboard | ⬜ | `qodacode-dashboard/` |
| Auth system | ⬜ | `qodacode-server/auth/` |
| Team management | ⬜ | `qodacode-server/teams/` |
| Trend analytics | ⬜ | `qodacode-server/analytics/` |
| Webhook integrations | ⬜ | `qodacode-server/webhooks/` |

**Complejidad añadida**: ~5000 LOC (closed source)

---

## 10.1 Resumen de Fases

```
FASE 1 ✅ Fundación          │ Sem 1-2   │ Python  │ +1500 LOC
FASE 2 ✅ Rust Setup         │ Sem 3-4   │ Rust    │ +2000 LOC
FASE 3 ✅ Algoritmos + MCP   │ Sem 5-6   │ Py+Rust │ +1000 LOC (daemon)
FASE 4 ✅ Data Moats         │ Sem 7-8   │ Rust    │ +1000 LOC
FASE 5    CLI Enhancements   │ Sem 9-10  │ Python  │ +1500 LOC
FASE 6    Integrations       │ Sem 11-12 │ Mixto   │ +2000 LOC
FASE 7    LLM Enhancement    │ Sem 13-14 │ Python  │ +1500 LOC
FASE 8    Dashboard MVP      │ Sem 15-18 │ TS/Py   │ +5000 LOC
─────────────────────────────┴───────────┴─────────┴───────────
TOTAL                        │ 18 semanas│         │ +17000 LOC
```

---

## 10.2 Archivos Clave por Fase

### Fase 2-4 (Rust Core)
```
rust/
├── Cargo.toml
├── src/
│   ├── lib.rs              # Entry point PyO3
│   ├── fingerprint.rs      # Hash algorithms
│   ├── similarity.rs       # Levenshtein + variants
│   ├── homoglyphs.rs       # Unicode detection
│   ├── keyboard.rs         # QWERTY proximity
│   ├── patterns.rs         # Regex compilation
│   ├── matcher.rs          # Aho-Corasick
│   ├── data.rs             # Embedded data loader
│   └── verify.rs           # Integrity checks
├── data/
│   ├── malicious.bin       # Typosquat DB
│   ├── homoglyphs.bin      # Unicode mappings
│   ├── keyboards.bin       # Layout matrices
│   └── patterns.bin        # Secret patterns
└── benches/
    └── benchmarks.rs
```

### Fase 3 (MCP Proactivo) ✅
```
qodacode/
├── daemon.py               # Proactive security guardian
│   ├── ProactivityLevel    # passive/reactive/proactive/guardian
│   ├── IssueCache          # Thread-safe issue storage
│   ├── EventQueue          # Push notifications
│   └── QodacodeDaemon      # File watcher + auto-scan
│
└── mcp_server.py           # +8 proactive tools
    ├── start_proactive_mode()
    ├── stop_proactive_mode()
    ├── get_daemon_status()
    ├── get_realtime_issues()
    ├── poll_events()
    ├── scan_staged()
    ├── register_file_hook()
    └── get_security_context()
```

### Fase 5-7 (Python Enhancements)
```
qodacode/
├── _core/
│   ├── __init__.py         # Rust bindings
│   └── _fallback.py        # Pure Python fallback
├── ai/
│   ├── __init__.py
│   ├── fp_filter.py        # LLM FP detection
│   ├── agent.py            # AGENT-002
│   ├── batch.py            # Batch processing
│   ├── cost.py             # Cost optimization
│   ├── cache.py            # Response caching
│   └── providers/
│       ├── anthropic.py
│       ├── openai.py
│       └── ollama.py
└── formatters/
    ├── __init__.py
    ├── sarif.py            # SARIF 2.1
    ├── json_stream.py      # Streaming JSON
    └── markdown.py         # PR comments
```

---

## 10.3 Dependencias Entre Fases

```
     ┌──────────┐
     │  FASE 1  │ ✅ Completada
     │Fundación │
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │  FASE 2  │ ✅ Completada
     │Rust Setup│
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │  FASE 3  │ ✅ Completada
     │Alg + MCP │
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │  FASE 4  │ ✅ Completada
     │Data Moats│
     └────┬─────┘
          │
          └───────┬────────┐
                  ▼        ▼
          ┌──────────────┐
          │   FASE 5-7   │ ◀── SIGUIENTE (paralelas)
          │CLI + AI + Int│
          └──────┬───────┘
                 │
                 ▼
          ┌──────────┐
          │  FASE 8  │
          │Dashboard │
          └──────────┘
```

---

## 11. Corte Open Source vs Premium

### 11.1 Matriz de Distribución

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         OPEN SOURCE (Apache 2.0)                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  INTERFACES                    DETECCIÓN                                   │
│  ├── CLI completo              ├── Semgrep integration                     │
│  ├── TUI completo              ├── Gitleaks integration                    │
│  ├── MCP Server                ├── Tree-sitter parsing                     │
│  └── LSP Server                ├── OSV vulnerability DB                    │
│                                └── Core rules (50+)                        │
│                                                                            │
│  RUST CORE (binario)           CONTEXT                                     │
│  ├── Fingerprinting            ├── Deduplication                           │
│  ├── Similarity algorithms     ├── Semantic analysis                       │
│  ├── Homoglyph detection       ├── Baseline mode                           │
│  └── Pattern matching          └── Inline ignores                          │
│                                                                            │
│  TYPOSQUATTING                 AI BÁSICO                                   │
│  ├── Detection engine          ├── Junior mode explanations                │
│  ├── Malicious DB (30+)        ├── Multi-provider (OpenAI/Anthropic)       │
│  └── Keyboard proximity        └── Ollama local support                    │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│  Complejidad: ~15,000 LOC Python + ~5,000 LOC Rust                        │
│  Valor: Herramienta completa y funcional para desarrolladores individuales │
└────────────────────────────────────────────────────────────────────────────┘

                                    │
                                    │ CORTE
                                    ▼

┌────────────────────────────────────────────────────────────────────────────┐
│                         PREMIUM (Closed Source)                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  CLOUD SERVICES                ENTERPRISE                                  │
│  ├── Dashboard web             ├── Team management                         │
│  ├── Trend analytics           ├── Role-based access (RBAC)                │
│  ├── Historical data           ├── SSO integration                         │
│  └── Real-time monitoring      └── Audit logs                              │
│                                                                            │
│  AI AVANZADO                   COMPLIANCE                                  │
│  ├── LLM false positive        ├── SOC2 reports                            │
│  │   elimination               ├── GDPR compliance                         │
│  ├── AGENT-002 orchestration   ├── Custom policies                         │
│  ├── Auto-fix suggestions      └── SLA guarantees                          │
│  └── Priority support                                                      │
│                                                                            │
│  DATA PREMIUM                  INTEGRATIONS                                │
│  ├── Malicious DB (500+)       ├── Jira integration                        │
│  ├── Zero-day patterns         ├── Slack/Teams alerts                      │
│  ├── Industry-specific rules   ├── PagerDuty                               │
│  └── Daily updates             └── Webhooks avanzados                      │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│  Ubicación: Server-side (imposible de piratear)                           │
│  Valor: Para equipos y empresas que necesitan escala                      │
└────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Funcionalidad por Tier

| Feature | Free (Open Source) | Pro ($29/mes) | Enterprise (Custom) |
|---------|-------------------|---------------|---------------------|
| **CLI/TUI/MCP** | ✅ Completo | ✅ Completo | ✅ Completo |
| **Escaneo local** | ✅ Ilimitado | ✅ Ilimitado | ✅ Ilimitado |
| **Reglas core** | ✅ 50+ | ✅ 200+ | ✅ 500+ |
| **Typosquatting DB** | ✅ 30 packages | ✅ 200+ | ✅ 500+ |
| **AI explanations** | ✅ Tu API key | ✅ Incluido | ✅ Incluido |
| **Dashboard** | ❌ | ✅ Individual | ✅ Team |
| **Historical trends** | ❌ | ✅ 30 días | ✅ 1 año |
| **Team features** | ❌ | ❌ | ✅ |
| **SSO/SAML** | ❌ | ❌ | ✅ |
| **Priority support** | ❌ | ✅ Email | ✅ Slack/Call |
| **SLA** | ❌ | ❌ | ✅ 99.9% |

### 11.3 Estrategia del Corte

```
PRINCIPIO: El usuario individual tiene TODO lo que necesita gratis.
           El equipo/empresa paga por escala y gestión.

┌─────────────────────────────────────────────────────────────────┐
│  DEVELOPER INDIVIDUAL                                           │
│  ─────────────────────                                          │
│  Usa: CLI, TUI, MCP                                             │
│  Valor: Escanea código, detecta secretos, typosquatting         │
│  Paga: $0 (usa su propia API key para AI)                       │
│                                                                 │
│  → FELIZ, recomienda Qodacode a su equipo                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  EQUIPO (5-20 devs)                                             │
│  ─────────────────                                              │
│  Necesita: Ver issues de todos, trends, asignar trabajo         │
│  Valor: Dashboard, histórico, reglas premium                    │
│  Paga: $29/usuario/mes                                          │
│                                                                 │
│  → Adopción porque YA conocen Qodacode                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ENTERPRISE (50+ devs)                                          │
│  ─────────────────────                                          │
│  Necesita: SSO, RBAC, compliance, SLA, support                  │
│  Valor: Seguridad enterprise, auditoría, integrations           │
│  Paga: Custom ($$$)                                             │
│                                                                 │
│  → Migración desde Pro, necesitan features enterprise           │
└─────────────────────────────────────────────────────────────────┘
```

### 11.4 Lo que NUNCA será Premium

| Feature | Por qué siempre Free |
|---------|---------------------|
| CLI completo | Es el hook de adopción |
| TUI completo | Experiencia diferenciadora |
| MCP Server | Integración con AI coding |
| Rust core | Complejidad = moat |
| Escaneo ilimitado | Sin límites artificiales |
| Typosquatting básico | Feature único |
| Baseline mode | Necesario para legacy |
| Inline ignores | Básico para DX |

### 11.5 Línea de Tiempo de Features

```
OPEN SOURCE                          PREMIUM
────────────────────────────────────────────────────────
v0.6.0 ✅ Semantic context
v0.7.0    Rust core
v0.8.0    LLM básico (tu API)        LLM avanzado (incluido)
v0.9.0    CLI diff command           Dashboard MVP
v1.0.0    VSCode extension           Team management
v1.1.0    GitHub Action              Trend analytics
v1.2.0    Pre-commit hook            Jira integration
v2.0.0    ---                        Enterprise SSO/RBAC
```

---

## 12. Conclusión

> **El mejor blindaje no es esconder el código - es hacerlo tan valioso y complejo que nadie quiera competir, sino contribuir.**

Qodacode será:
1. **Demasiado complejo** para replicar
2. **Demasiado rápido** para alcanzar
3. **Demasiado integrado** para reemplazar
4. **Demasiado documentado** para competir

---

*Última actualización: Enero 2025*
*Versión: 1.4 (FASE 4 expandida - Data Moats: 150+ typosquats, 45+ secrets, multi-ecosystem)*
