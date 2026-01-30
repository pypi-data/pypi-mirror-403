# Fase 5: Agentic Security (v0.6.0)

## Estado: PENDIENTE

**Fecha inicio:** 2026-01-20
**Target:** Week 11-12

---

## Objetivo

Make Qodacode the auto-remediation layer for AI coding + detect AI-specific security issues.

**Diferenciador clave:** No solo encontramos problemas, los ARREGLAMOS automáticamente.

---

## Entregables

### 1. Enhanced `fix_issue`

**Objetivo:** AI aplica 80% de los fixes sin intervención humana.

**Mejoras:**
- [ ] Contexto expandido (±10 líneas en lugar de ±3)
- [ ] Detección de imports necesarios
- [ ] Validación de sintaxis del patch
- [ ] Múltiples opciones de fix cuando aplica

**Ejemplo:**
```python
# Antes (fix_issue actual)
"fix": "Use parameterized query"

# Después (enhanced)
"fix": {
  "code": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
  "imports_needed": [],
  "confidence": 0.95,
  "alternatives": [
    {"code": "...", "description": "Using SQLAlchemy ORM"}
  ]
}
```

---

### 2. Context Awareness

**Objetivo:** 50% menos false positives distinguiendo test vs production.

**Detecciones:**
- [ ] `/tests/`, `/test_*.py`, `*_test.py` → test code
- [ ] `/examples/`, `/demo/` → example code
- [ ] `.env.example` vs `.env` → ejemplo vs real
- [ ] `if __name__ == "__main__"` → script mode

**Configuración:**
```yaml
# .qodacode.yml
context:
  test_patterns:
    - "tests/**"
    - "test_*.py"
  example_patterns:
    - "examples/**"
  severity_override:
    test: -1  # Reduce severity by 1 level in tests
```

---

### 3. AI Code Pattern Detection

**Objetivo:** Detectar patrones de código inseguros generados por AI.

**Patrones a detectar:**
- [ ] Código excesivamente verbose (AI tiende a sobre-explicar)
- [ ] Try/except vacíos (AI los pone "por seguridad")
- [ ] Imports no usados (AI importa de más)
- [ ] Comentarios redundantes que explican lo obvio
- [ ] Hardcoded values que deberían ser config

**Rule IDs:**
- `AI-001`: Verbose exception handling
- `AI-002`: Unused imports block
- `AI-003`: Redundant comments
- `AI-004`: Hardcoded configuration

---

### 4. AGENT-002: Prompt Injection Detection

**Objetivo:** Detectar vulnerabilidades de prompt injection en código AI-assisted.

**Flujo de ataque:**
```
User Input → LLM Call → Code Execution = VULNERABILITY
```

**Patrones a detectar:**
- [ ] `eval(user_input)` - Ejecución directa de input
- [ ] `exec(llm_response)` - Ejecución de respuesta LLM
- [ ] `os.system(prompt_output)` - Shell injection vía LLM
- [ ] `subprocess.run(ai_generated)` - Command injection
- [ ] SQL construido con f-strings desde LLM response

**Ejemplo vulnerable:**
```python
# VULNERABLE - AGENT-002
response = openai.chat.completions.create(...)
code = response.choices[0].message.content
exec(code)  # PROMPT INJECTION RISK
```

**Fix sugerido:**
```python
# SEGURO
response = openai.chat.completions.create(...)
code = response.choices[0].message.content
# Validate and sandbox before execution
validated_code = validate_and_sanitize(code)
sandbox.execute(validated_code)
```

---

### 5. Typosquatting → full_audit Integration

**Objetivo:** Unified security scan que incluye typosquatting.

**Cambios:**
- [ ] `full_audit` MCP tool incluye typosquatting
- [ ] `qodacode check` incluye typosquatting por defecto
- [ ] Reporte unificado con todas las categorías

---

## Arquitectura

```
qodacode/
├── agentic/                    # NEW MODULE
│   ├── __init__.py
│   ├── context.py              # Test vs prod detection
│   ├── ai_patterns.py          # AI code pattern rules
│   └── prompt_injection.py     # AGENT-002 detector
├── rules/
│   └── agentic/                # NEW RULES
│       ├── ai_001_verbose.py
│       ├── ai_002_imports.py
│       ├── ai_003_comments.py
│       └── agent_002_injection.py
└── fix/
    └── enhanced_fixer.py       # Enhanced fix_issue
```

---

## Testing

```bash
# Context awareness
pytest tests/test_context.py

# AI patterns
pytest tests/test_ai_patterns.py

# AGENT-002
pytest tests/test_prompt_injection.py

# Enhanced fix_issue
pytest tests/test_enhanced_fix.py
```

---

## Métricas de Éxito

| Métrica | Target |
|---------|--------|
| fix_issue apply rate | 80% AI-applicable |
| False positive reduction | 50% less in test code |
| AGENT-002 detection | 100% for known patterns |
| AI pattern detection | 90% accuracy |

---

## Notas de Diseño

### Por qué AGENT-002 primero (antes de License)

1. **Diferenciador real**: License compliance lo tiene todo el mundo
2. **AI-native**: Solo herramientas diseñadas para AI detectan esto
3. **Urgencia de mercado**: AI code execution es riesgo real ahora
4. **Gemini lo sugirió**: Validación externa de la idea

### Typosquatting como "Hallucination Corrector"

El messaging es clave:
- **Antes**: "Detector de typosquatting"
- **Ahora**: "Hallucination Corrector - Catches fake packages AI suggests"

El AI a veces sugiere paquetes que no existen o son typos de paquetes reales.
Qodacode los detecta ANTES de `pip install`.

---

## Movido a v0.7.0

- License compliance
- `check_licenses` MCP tool

Razón: No es diferenciador. Snyk, Dependabot ya lo tienen.
Mejor invertir tiempo en features AI-native.

---

## Referencias

- Fase 4: [fase4.md](fase4.md) - Typosquatting (COMPLETADO)
- PRD: [PRD_LEVEL2.md](../../PRD_LEVEL2.md) - Section 12.1

---

## Commits

(Se actualizará conforme avance la fase)
