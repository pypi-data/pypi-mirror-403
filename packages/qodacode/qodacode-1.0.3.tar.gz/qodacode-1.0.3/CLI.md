# Qodacode CLI - Documentación Completa

## Descripción

El CLI (Command Line Interface) de Qodacode permite ejecutar análisis de seguridad directamente desde la terminal. Diseñado para ser simple, rápido y profesional.

---

## Instalación

```bash
pip install qodacode
```

Verificar instalación:
```bash
qodacode --version
```

---

## ¿Qué comando usar?

| Situación | Comando |
|-----------|---------|
| Escaneo rápido del día a día | `qodacode scan` |
| Solo archivos cambiados (rápido) | `qodacode scan --diff` |
| Guardar reporte | `qodacode scan --save` |
| Análisis completo | `qodacode scan --full` |
| Necesito más opciones/filtros | `qodacode check` |
| CI/CD pipeline | `qodacode ci` |
| Monitoreo en tiempo real | `qodacode watch` |
| Interfaz interactiva | `qodacode` (sin args) |
| Detectar typosquatting | `qodacode typosquat` |

---

## Comandos Principales

### `qodacode scan` - Escaneo Rápido (Recomendado)

El comando más simple para escanear código. **Usa este comando para el día a día.**

> **Nota:** `scan` es el comando simplificado, `check` es el avanzado con más opciones.
> Para la mayoría de casos, `qodacode scan` es suficiente.

```bash
# Escanear directorio actual
qodacode scan

# Escanear ruta específica
qodacode scan ./src

# Solo archivos cambiados (git-aware, más rápido)
qodacode scan --diff

# Suite de seguridad completa
qodacode scan --full

# Guardar reporte en texto
qodacode scan --save

# Guardar reporte en markdown
qodacode scan --save --format md
```

**Opciones:**
| Opción | Descripción |
|--------|-------------|
| `--diff` | Solo escanea archivos cambiados (git-aware, ~5x más rápido) |
| `--full` | Ejecuta todos los engines de seguridad |
| `--save` | Guarda el reporte en archivo |
| `--format [txt\|md]` | Formato de exportación (default: txt) |

**Ejemplo de salida:**
```
🔍 Quick scan...

Files scanned: 45

🔴 Critical: 2
🟠 High: 5
🟡 Medium: 12

⛔ NOT READY — Fix 2 critical issues
```

---

### `qodacode check` - Escaneo Avanzado

Comando completo con todas las opciones de configuración.

```bash
# Escaneo básico
qodacode check

# Suite completa de seguridad
qodacode check --all

# Solo análisis SAST profundo
qodacode check --deep

# Solo detección de secretos
qodacode check --secrets

# Solo vulnerabilidades en dependencias
qodacode check --deps

# Modo CI/CD (sin prompts interactivos)
qodacode check --all --skip-missing

# Exportar a JSON
qodacode check --format json

# Exportar a SARIF (GitHub Security)
qodacode check --format sarif

# Modo educativo (explicaciones detalladas)
qodacode check --mode junior

# Guardar reporte
qodacode check --export
```

**Opciones completas:**

| Opción | Descripción |
|--------|-------------|
| `-p, --path` | Ruta a escanear (default: `.`) |
| `-s, --severity` | Filtro: critical, high, medium, low, all |
| `-c, --category` | Filtro: security, robustness, maintainability, operability, dependencies |
| `-f, --format` | Salida: terminal, json, sarif, markdown |
| `--fix` | Mostrar sugerencias de corrección |
| `-m, --mode` | junior (explicaciones) / senior (conciso) |
| `--deep` | Análisis SAST avanzado |
| `--secrets` | Detección de credenciales |
| `--deps` | Escaneo de dependencias |
| `--all` | Suite completa (todos los engines) |
| `--skip-missing` | Modo CI - no prompts si falta engine |
| `-e, --export` | Exportar a archivo .txt |

---

### `qodacode` - Modo Interactivo (TUI)

Sin argumentos, inicia la interfaz interactiva.

```bash
# Iniciar TUI
qodacode

# Modo clásico (sin TUI)
qodacode --classic
```

> **TUI vs CLI:** En la TUI el comando es `/check`. En el CLI usa `qodacode scan` o `qodacode check`.

---

## Comandos de Configuración

### `qodacode init` - Inicializar Proyecto

Crea la carpeta `.qodacode/` con configuración e índices.

```bash
qodacode init
qodacode init --path ./mi-proyecto
qodacode init --force  # Re-indexar
```

---

### `qodacode config` - Configurar AI

Configura el proveedor de IA para explicaciones contextuales.

```bash
# Ver configuración actual
qodacode config --show

# Configurar Anthropic (Claude)
qodacode config --ai-provider anthropic --ai-key sk-ant-xxx

# Configurar OpenAI
qodacode config --ai-provider openai --ai-key sk-xxx

# Configurar Ollama (local, gratis)
qodacode config --ai-provider ollama --ai-model llama3.2

# Desactivar AI
qodacode config --ai-provider none
```

---

### `qodacode doctor` - Verificar Sistema

Verifica que todos los engines estén disponibles.

```bash
qodacode doctor
```

**Salida ejemplo:**
```
QODACODE Doctor - System health check

┌─────────────────────────────────────────┐
│           Engine Status                 │
├───────────────────┬──────────┬──────────┤
│ Engine            │ Status   │ Info     │
├───────────────────┼──────────┼──────────┤
│ Core Engine       │ ✓ Ready  │ <50ms    │
│ Deep SAST         │ ✓ Ready  │ Advanced │
│ Secret Detection  │ ✓ Ready  │ Creds    │
│ Dependency Scanner│ ✓ Ready  │ Vulns    │
└───────────────────┴──────────┴──────────┘

✓ All engines ready!
```

---

## Comandos de Monitoreo

### `qodacode status` - Estado del Proyecto

Muestra resumen de salud del proyecto.

```bash
qodacode status
qodacode status --path ./mi-proyecto
```

---

### `qodacode watch` - Monitoreo en Tiempo Real

Observa cambios en archivos y escanea automáticamente.

```bash
# Monitorear directorio actual
qodacode watch

# Monitorear ruta específica
qodacode watch --path ./src

# Solo reportar issues críticos
qodacode watch --severity critical

# Modo educativo
qodacode watch --mode junior
```

**Opciones:**
| Opción | Descripción |
|--------|-------------|
| `-p, --path` | Directorio a monitorear |
| `-s, --severity` | Severidad mínima a reportar |
| `-m, --mode` | junior / senior |

Presiona `Ctrl+C` para detener.

---

## Detección de Supply Chain

### `qodacode typosquat` - Detectar Typosquatting

Detecta ataques de supply chain en dependencias (paquetes maliciosos con nombres similares a paquetes legítimos).

```bash
# Escanear directorio (auto-detecta requirements.txt, package.json, etc.)
qodacode typosquat

# Escanear directorio específico
qodacode typosquat ./mi-proyecto

# Escanear archivo específico
qodacode typosquat requirements.txt
qodacode typosquat package.json

# Salida JSON (para CI/CD)
qodacode typosquat --json
```

**Detecta:**
- **Typos**: `reqeusts` vs `requests`
- **Homoglyphs**: `fIask` (I mayúscula) vs `flask`
- **Keyboard proximity**: teclas adyacentes en QWERTY
- **Paquetes maliciosos conocidos**: 30+ ataques confirmados

**Ejemplo de salida (seguro):**
```
⟳ Checking dependencies... (typosquatting detection)

✓ SUPPLY CHAIN SAFE
No suspicious packages detected in dependencies.
```

**Ejemplo de salida (ataque detectado):**
```
🚨 SUPPLY CHAIN ATTACK DETECTED
──────────────────────────────────────────────────

requirements.txt
└─ 🔴 reqeusts → requests
      Known malicious package impersonating 'requests'

──────────────────────────────────────────────────
🔴 1 critical

⛔ CRITICAL: Remove malicious packages immediately!
These are known attack packages that steal credentials.
```

**Opciones:**
| Opción | Descripción |
|--------|-------------|
| `--json` | Salida JSON para integración con CI/CD |

---

## Comandos de Git

### `qodacode git-history` - Escanear Historial

Busca secretos en el historial de git (commits anteriores).

```bash
# Escanear últimos 50 commits
qodacode git-history

# Escanear más commits
qodacode git-history --max-commits 100

# Desde fecha específica
qodacode git-history --since 2024-01-01

# Salida JSON
qodacode git-history --format json
```

---

## Comandos de Supresión

### `qodacode suppress` - Suprimir Issue

Marca un issue como falso positivo o riesgo aceptado.

```bash
# Suprimir permanentemente
qodacode suppress abc123def456

# Con razón
qodacode suppress abc123def456 --reason "false positive"

# Con expiración (30 días)
qodacode suppress abc123def456 --expires 30
```

---

### `qodacode unsuppress` - Remover Supresión

```bash
qodacode unsuppress abc123def456
```

---

### `qodacode suppressions` - Listar Supresiones

```bash
qodacode suppressions
```

---

## Baseline Mode (Proyectos Legacy)

Para proyectos con deuda técnica existente, usa el modo baseline para enfocarte solo en issues NUEVOS.

### `qodacode baseline save` - Guardar Baseline

```bash
# Guardar issues actuales como baseline
qodacode baseline save
```

### `qodacode baseline show` - Ver Info

```bash
# Ver información del baseline
qodacode baseline show
```

### `qodacode baseline clear` - Limpiar Baseline

```bash
# Eliminar baseline
qodacode baseline clear
```

### Usar Baseline en Escaneo

```bash
# Solo mostrar issues NUEVOS (no en baseline)
qodacode check --baseline
```

---

## Supresión Inline (Comentarios)

Suprime issues específicos directamente en el código:

```python
# Misma línea
password = "safe_test"  # qodacode-ignore: SEC-001

# Línea anterior
# qodacode-ignore: SEC-001
password = "safe_test"

# Múltiples reglas
secret = "test"  # qodacode-ignore: SEC-001, SEC-002

# Todas las reglas
data = "..."  # qodacode-ignore
```

También funciona con comentarios JS:
```javascript
const secret = "test";  // qodacode-ignore: SEC-001
```

---

## Archivo `.qodacodeignore`

Crea un archivo `.qodacodeignore` para excluir archivos/carpetas:

```
# Ignorar tests
tests/
*_test.py
test_*.py

# Ignorar fixtures
fixtures/
mocks/

# Ignorar archivos específicos
config.example.py
```

---

## Filtrado Semántico Automático

Qodacode automáticamente filtra falsos positivos reconociendo patrones seguros:

- `os.environ["KEY"]` - Lectura de env vars
- `os.getenv("KEY")` - Lectura de env vars
- `decrypt(secret)` - Funciones de descifrado
- `bcrypt.hash(pwd)` - Funciones de hash
- `settings.SECRET_KEY` - Referencias a config
- `"sqlite:///:memory:"` - DBs de test
- `mock_password = "..."` - Datos de test
- `"<YOUR_API_KEY>"` - Placeholders

Salida:
```
[Semantic] Filtered 3 likely false positive(s)
```

---

## Comandos CI/CD

### `qodacode ci` - Modo Pipeline

Diseñado para GitHub Actions, GitLab CI, etc.

```bash
# Básico - falla solo en critical
qodacode ci

# Falla en high o superior
qodacode ci --fail-on high

# Generar comentario de PR
qodacode ci --comment

# Generar SARIF para GitHub Security
qodacode ci --sarif

# Salida JSON
qodacode ci --json-output

# Modo educativo en PR comments
qodacode ci --mode junior --comment
```

**Opciones:**
| Opción | Descripción |
|--------|-------------|
| `--fail-on` | Severidad que bloquea: critical, high, medium, low, none |
| `--comment` | Genera archivo markdown para PR |
| `--sarif` | Genera SARIF para GitHub Security Tab |
| `--sarif-file` | Ruta del archivo SARIF |
| `--json-output` | Salida JSON para integración |
| `--output-file` | Archivo para GITHUB_OUTPUT |

---

## Comandos de Integración

### `qodacode rules` - Listar Reglas

Muestra todas las reglas de análisis disponibles.

```bash
qodacode rules
```

---

### `qodacode login` - Autenticar GitHub (Opcional)

```bash
qodacode login
```

> **Nota:** El login **NO es necesario** para escaneo local. Solo es requerido para:
> - Integración con MCP/Claude Code
> - Escanear repositorios remotos
>
> Requiere GitHub CLI (`gh`) instalado: `brew install gh`

---

### `qodacode setup-mcp` - Configurar Claude Code

Configura Qodacode como servidor MCP para Claude Code.

```bash
qodacode setup-mcp
```

---

### `qodacode serve` - Iniciar Servidor MCP

```bash
qodacode serve
```

---

### `qodacode lsp` - Iniciar Servidor LSP

Para integración con VSCode/Cursor.

```bash
qodacode lsp
```

---

## Modos de Salida

### Modo Senior (default)
Conciso, solo los hechos.

```bash
qodacode check --mode senior
```

### Modo Junior
Explicaciones detalladas, ideal para aprender.

```bash
qodacode check --mode junior
```

---

## Formatos de Exportación

### Terminal (default)
```bash
qodacode check
```

### JSON
```bash
qodacode check --format json
```

### SARIF (GitHub Security)
```bash
qodacode check --format sarif
```

### Markdown (PR Comments)
```bash
qodacode check --format markdown
```

### Archivo de Reporte
```bash
# Texto plano
qodacode scan --save

# Markdown
qodacode scan --save --format md
```

---

## Códigos de Salida

| Código | Significado |
|--------|-------------|
| `0` | Sin issues críticos (READY FOR PRODUCTION) |
| `1` | Issues críticos encontrados (NOT READY) |

---

## Variables de Entorno

| Variable | Descripción |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key para Claude AI |
| `OPENAI_API_KEY` | API key para OpenAI |
| `OLLAMA_HOST` | Host de Ollama (default: localhost:11434) |

---

## Ejemplos de Uso Común

### Desarrollo Local
```bash
# Escaneo rápido mientras desarrollas
qodacode scan

# Antes de commit
qodacode scan --full
```

### Pre-commit Hook
```bash
#!/bin/bash
qodacode scan --full
if [ $? -ne 0 ]; then
    echo "Fix critical issues before committing"
    exit 1
fi
```

### GitHub Actions
```yaml
- name: Security Scan
  run: |
    pip install qodacode
    qodacode ci --fail-on critical --sarif

- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: qodacode-results.sarif
```

### GitLab CI
```yaml
security_scan:
  script:
    - pip install qodacode
    - qodacode ci --fail-on high --json-output > scan-results.json
  artifacts:
    paths:
      - scan-results.json
```

---

## Veredicto de Producción

La lógica de veredicto es consistente en TUI, CLI y MCP:

- **✅ READY FOR PRODUCTION**: 0 issues críticos
- **⛔ NOT READY**: 1+ issues críticos

Los issues HIGH, MEDIUM y LOW son advertencias, no bloquean el veredicto.

---

## Ayuda

```bash
# Ayuda general
qodacode --help

# Ayuda de comando específico
qodacode check --help
qodacode scan --help
qodacode ci --help
```

---

## Versión

```bash
qodacode --version
```

---

## 🆕 Nuevas Features v1.0.2 (Security Release)

### Rate Limiting - Protección contra Runaway Costs

Qodacode protege automáticamente tu billetera limitando operaciones:

**Límites por defecto:**
- 60 scans por minuto
- 30 llamadas AI por minuto

**Configuración** (`.qodacode/config.json`):
```json
{
  "rate_limit": {
    "max_scans_per_minute": 60,
    "max_ai_calls_per_minute": 30,
    "enabled": true
  }
}
```

**Cuando alcanzas el límite:**
```
⚠️  Rate limit: 60 scans/minute. Wait 12s
To disable rate limiting, edit .qodacode/config.json
```

**Nota:** Rate limits son per-instance. Si corres múltiples terminales, cada una tiene su propio límite.

---

### Audit Logging - Compliance Ready

Todos los scans se registran automáticamente en `.qodacode/audit.jsonl`:

**Qué se registra:**
- Scans ejecutados (path, tipo, findings, duración)
- Operaciones bloqueadas (comandos peligrosos)
- Llamadas AI (provider, tokens, costo estimado)
- Cambios de configuración

**Formato:** JSON Lines (cada línea es un JSON válido)

**Ejemplo de entrada:**
```json
{
  "timestamp": 1737576845.123,
  "timestamp_iso": "2026-01-22T15:47:25",
  "action": "scan",
  "user": "developer",
  "severity": "info",
  "result": "completed",
  "details": {
    "path": ".",
    "scan_type": "full",
    "findings_count": 3,
    "critical_count": 0,
    "duration_ms": 1234.56
  }
}
```

**Privacidad:** Todos los secretos son automáticamente enmascarados antes de escribir al log.

**Leer logs:**
```bash
# Ver últimos 10 scans
cat .qodacode/audit.jsonl | tail -10 | jq

# Filtrar solo operaciones bloqueadas
cat .qodacode/audit.jsonl | jq 'select(.action == "block_tool")'

# Resumen diario
cat .qodacode/audit.jsonl | jq 'select(.timestamp > 1737504000)'
```

---

### Primera Instalación - Auto-Setup

**Primera ejecución con `--deep` o `--secrets`:**

```bash
qodacode check --all

🚀 First run detected - Installing security engines...
This happens once and takes ~30 seconds

⠋ Downloading Gitleaks v8.18.4... ████████-- 80% 12.5MB 2.1MB/s 2s
✓ Gitleaks installed
Installing Semgrep via pip...
✓ Semgrep installed

✅ All engines installed successfully!
Future scans will be instant
```

**Después:** Todos los scans son instantáneos.

**En entornos restringidos (Docker readonly, CI sin permisos):**
```
✗ Permission denied: Cannot write to ~/.qodacode/bin/
Run with appropriate permissions or install Gitleaks manually
```
El tool continúa funcionando con engines disponibles (no crashea).

---

### Security Hooks - PreToolUse Protection

**Nota:** Esta feature es para integraciones MCP (Claude Code, Cursor).
Ver [mcp.md](mcp.md) para detalles completos.

El CLI hereda la protección:

```bash
# Ejemplo: comando peligroso detectado
$ qodacode check

During scan, detected attempt to execute:
  rm -rf /

⛔ BLOCKED: Dangerous pattern detected: rm -rf /
```

**Detección inteligente:**
- Comandos peligrosos: `rm -rf`, `sudo`, `chmod 777`
- Encoding bypasses: base64, hex, URL encoding
- Obfuscación: exceso de quotes, concatenación
- Environment variable manipulation

---

## FAQ v1.0.2

**P: ¿Por qué me dice "Rate limit exceeded"?**
R: Alcanzaste el límite de scans por minuto (default: 60). Espera unos segundos o aumenta el límite en `.qodacode/config.json`.

**P: ¿Los audit logs son seguros?**
R: Sí. Todos los secretos (API keys, passwords) son automáticamente enmascarados antes de escribir al disco.

**P: ¿Puedo deshabilitar el rate limiting?**
R: Sí, pero no recomendado. Edita `.qodacode/config.json` y pon `"enabled": false`.

**P: ¿La primera instalación siempre descarga engines?**
R: Solo si usas `--deep`, `--secrets` o `--all`. El scan básico (`qodacode scan`) no requiere downloads.

**P: ¿Qué pasa si falla la instalación de engines en CI?**
R: El tool continúa con engines disponibles. Usa `--skip-missing` para evitar prompts interactivos.
