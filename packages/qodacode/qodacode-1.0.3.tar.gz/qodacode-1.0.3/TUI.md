# Qodacode TUI - Interfaz de Terminal

## ¿Qué es Qodacode TUI?

Qodacode TUI es una **interfaz interactiva de terminal** para escanear y analizar tu código en busca de vulnerabilidades de seguridad, secretos expuestos y problemas de calidad. Construida con [Textual](https://textual.textualize.io/), ofrece una experiencia moderna de terminal con retroalimentación en tiempo real.

### Características Principales

- **Motor de Análisis Híbrido**: 4 engines especializados + reglas custom
- **Dos Modos**: Senior (solo resultados) y Junior (con explicaciones IA)
- **Soporte Multi-Proveedor IA**: OpenAI, Anthropic, Gemini y Grok
- **Veredicto de Producción**: Evaluación clara de si el código está listo para deploy
- **Exportación**: Guarda los resultados del escaneo
- **Bilingüe**: Interfaz en inglés y español

---

## Instalación

### Prerrequisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Instalar Qodacode

```bash
# Desde PyPI (recomendado)
pip install qodacode

# O desde el código fuente
git clone https://github.com/your-org/qodacode.git
cd qodacode
pip install -e .
```

### Verificar Instalación

```bash
qodacode --version
```

---

## Iniciar la TUI

Navega a tu directorio de proyecto y ejecuta:

```bash
qodacode
```

Esto abre la TUI interactiva en tu terminal.

---

## Flujo de Primera Vez

Cuando lanzas Qodacode por primera vez en un proyecto:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ██████╗  ██████╗ ██████╗  █████╗  ██████╗ ██████╗ ██████╗███████╗
│  ██╔═══██╗██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝
│  ██║   ██║██║   ██║██║  ██║███████║██║     ██║   ██║██║  ██║█████╗
│  ██║▄▄ ██║██║   ██║██║  ██║██╔══██║██║     ██║   ██║██║  ██║██╔══╝
│  ╚██████╔╝╚██████╔╝██████╔╝██║  ██║╚██████╗╚██████╔╝██████╔╝███████╗
│   ╚══▀▀═╝  ╚═════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝
│                                                                 │
│   Enterprise Code Intelligence Scanner v0.5.0                   │
│                                                                 │
│   Project: /ruta/a/tu/proyecto                                 │
│   Mode: senior                                                  │
│   API: ❌ Not configured                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Paso 1: Configurar API Key (Opcional pero Recomendado)

Para habilitar las explicaciones con IA (Modo Junior), configura tu API key:

```
> /api sk-tu-api-key-aqui
```

**Formatos de API Key Soportados:**
| Prefijo | Proveedor |
|---------|-----------|
| `sk-ant-*` | Anthropic (Claude) |
| `sk-*` | OpenAI (GPT) |
| `xai-*` | Grok (xAI) |
| `AIza*` | Google Gemini |

Después de configurar tu API key, el Modo Junior se activa automáticamente:

```
✅ API key configured (provider: openai)
Mode: junior (auto-activated)
```

### Paso 2: Ejecuta tu Primer Escaneo

```
> /check
```

Esto ejecuta un escaneo rápido buscando errores de sintaxis y secretos expuestos.

---

## Flujo de Usuario Recurrente

Cuando vuelves a un proyecto previamente configurado:

```
┌─────────────────────────────────────────────────────────────────┐
│   Project: /ruta/a/tu/proyecto                                 │
│   Mode: junior                                                  │
│   API: ✅ openai                                                │
└─────────────────────────────────────────────────────────────────┘
```

Tu configuración persiste en `.qodacode/config.json`. Solo escribe un comando para empezar:

```
> /ready
```

---

## Referencia de Comandos

### `/check` - Escaneo Rápido

Realiza un escaneo rápido enfocado en:
- Errores de sintaxis
- Secretos expuestos (API keys, contraseñas, tokens)
- Problemas críticos de seguridad

```
> /check

🔍 Scanning...

📊 PRODUCTION FILES (excluding tests)
┌──────────┬───────┐
│ Critical │     0 │
│ High     │     2 │
│ Medium   │     1 │
│ Low      │     0 │
└──────────┴───────┘

✅ READY FOR PRODUCTION (2 warnings)
```

---

### `/audit` - Auditoría Completa

Análisis exhaustivo usando todos los motores:
- Secret Detection (detección de secretos)
- Deep SAST (patrones de seguridad)
- Core Engine (reglas específicas del proyecto)

```
> /audit

🔍 Full audit in progress...
[████████████████████████████████████████] 100%

📊 PRODUCTION FILES (excluding tests)
┌──────────┬───────┐
│ Critical │     1 │
│ High     │     3 │
│ Medium   │     2 │
│ Low      │     1 │
└──────────┴───────┘

⛔ NOT READY — Fix 1 critical issues
```

---

### `/ready` - Verificación de Producción

Evaluación rápida: "¿Puedo desplegar este código?"

**Lógica del Veredicto:**
- `✅ READY FOR PRODUCTION` - 0 issues críticos (warnings son deuda técnica, no bloquean)
- `⛔ NOT READY` - 1+ issues críticos que deben arreglarse

```
> /ready

✅ READY FOR PRODUCTION
```

---

### `/mode` - Cambiar Modo Junior/Senior

**Modo Senior** (por defecto): Muestra solo resultados del escaneo
**Modo Junior**: Incluye explicaciones "Learn Why" con IA

```
# Alternar modo
> /mode

Mode: junior

# Establecer modo específico
> /mode junior
> /mode senior
```

**Nota:** El Modo Junior requiere API key. Si no está configurada:
```
⚠️ Junior Mode requires API key. Use /api <key> first.
```

---

### `/typosquat` - Detección de Supply Chain

Escanea las dependencias del proyecto buscando ataques de typosquatting:

```
> /typosquat

⟳ Checking dependencies... (typosquatting detection)

✓ SUPPLY CHAIN SAFE
No suspicious packages detected in dependencies.
```

**Si detecta paquetes sospechosos:**
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

**Detecta:**
- Typos: `reqeusts` vs `requests`
- Homoglyphs: `fIask` (I mayúscula) vs `flask`
- Keyboard proximity: teclas adyacentes
- Paquetes maliciosos conocidos (30+ ataques confirmados)

---

### `/api` - Configurar/Eliminar Proveedor de IA

Gestiona tu API key para las explicaciones del Modo Junior:

**Establecer API key:**
```
> /api sk-ant-abc123...

✅ API key configured (provider: anthropic)
Mode: junior (auto-activated)
```

**Cambiar de proveedor** (simplemente sobrescribe):
```
> /api sk-nuevo-key...

✅ API key configured (provider: openai)
```

**Eliminar API key:**
```
> /api clear

✓ API key removed
Mode: senior (AI features disabled)
```

También funciona: `/api remove`, `/api none`, `/api delete`

**Auto-Detección de Proveedor:**
- `sk-ant-*` → Anthropic Claude
- `sk-*` → OpenAI GPT
- `xai-*` → Grok
- `AIza*` → Google Gemini

---

### `/export` - Guardar Resultados

Exporta los resultados del último escaneo a un archivo:

```
> /export

📁 Exported to: qodacode-report-20240115-143052.txt
```

**La exportación incluye:**
- Todos los issues detectados con severidad
- Ubicaciones de archivos y números de línea
- Explicaciones "Learn Why" (si el Modo Junior estaba activo)

---

### `/clean` - Limpiar Pantalla

Limpia el área de salida:

```
> /clean
```

---

### `/help` - Mostrar Comandos

Muestra todos los comandos disponibles:

```
> /help

Available commands:
  /check      Quick scan (syntax + secrets)
  /audit      Full audit (all engines)
  /typosquat  Check dependencies for typosquatting
  /ready      Production ready?
  /mode       Junior/Senior mode
  /api        Set/remove API key
  /export     Save last scan to file
  /clean      Clear screen
  /help       Show commands
  /exit       Exit
```

---

### `/exit` - Salir de la TUI

Cierra la TUI y vuelve a la terminal:

```
> /exit
```

O usa: `Ctrl+C` o `Ctrl+Q`

---

## Modo Junior: Learn Why

Cuando el Modo Junior está activo, los escaneos incluyen explicaciones educativas con IA:

```
📚 Learn Why
────────────────────────────────────────

1. 📍 Ubicación: src/config.py:42
   ❓ QUÉ Y POR QUÉ: API key hardcodeada detectada. Esto es peligroso porque
      si este código se sube a un repositorio público, los atacantes pueden
      usar tu API key para acceder a tus servicios y generar cargos.
   ✅ CÓMO ARREGLARLO:
      # En lugar de:
      API_KEY = "sk-abc123..."

      # Usa variables de entorno:
      import os
      API_KEY = os.environ.get("API_KEY")

2. 📍 Ubicación: src/db.py:18
   ❓ QUÉ Y POR QUÉ: Query SQL construida con concatenación de strings. Esto
      permite ataques de inyección SQL donde usuarios maliciosos pueden
      manipular las consultas a tu base de datos.
   ✅ CÓMO ARREGLARLO:
      # En lugar de:
      query = f"SELECT * FROM users WHERE id = {user_id}"

      # Usa queries parametrizadas:
      query = "SELECT * FROM users WHERE id = ?"
      cursor.execute(query, (user_id,))
```

### Batching Inteligente

Learn Why usa batching inteligente para minimizar costos de API:
- Una sola llamada API por escaneo
- Se enfoca en los 5 issues de mayor prioridad
- Excluye archivos de test del análisis
- Issues ordenados por severidad (critical → high → medium → low)

---

## Configuración

La configuración se almacena en `.qodacode/config.json`:

```json
{
  "mode": "junior",
  "language": "es",
  "ai": {
    "api_key": "sk-...",
    "provider": "openai"
  },
  "exclusions": [
    "node_modules",
    ".git",
    "__pycache__"
  ]
}
```

### Configuración de Idioma

Cambiar idioma de la interfaz:

```json
{
  "language": "es"
}
```

Soportados: `en` (Inglés), `es` (Español)

---

## Niveles de Severidad

| Nivel | Significado | Acción |
|-------|-------------|--------|
| **Critical** | Vulnerabilidad de seguridad que bloquea deploy | Debe arreglarse antes de desplegar |
| **High** | Issue significativo (deuda técnica) | Debería arreglarse, no bloquea |
| **Medium** | Preocupación de calidad de código | Revisar cuando sea posible |
| **Low** | Sugerencia menor | Deseable pero no urgente |

### Lógica del Veredicto de Producción

```
if critical_issues > 0:
    ⛔ NOT READY — Fix N critical issues
else:
    ✅ READY FOR PRODUCTION (N warnings)
```

**Filosofía:** Los warnings (high/medium/low) son deuda técnica a rastrear, no bloqueadores de seguridad. Solo los issues críticos impiden el despliegue.

---

## Exclusiones de Archivos

Los archivos de test se excluyen automáticamente de:
1. **Cálculo del veredicto de producción**
2. **Explicaciones de IA**

Patrones de archivos de test:
- `test_*.py`
- `*_test.py`
- Archivos en directorios `/tests/` o `/__tests__/`

---

## Atajos de Teclado

| Tecla | Acción |
|-------|--------|
| `Enter` | Ejecutar comando |
| `Ctrl+C` | Salir de TUI |
| `Ctrl+Q` | Salir de TUI |
| `↑` / `↓` | Navegar historial |
| `Tab` | Autocompletar comando |

---

## Solución de Problemas

### "API key required for Junior Mode"

Configura tu API key primero:
```
> /api tu-api-key
```

### Las explicaciones de IA no aparecen

1. Verifica que la API key esté configurada: revisa que el welcome box muestre `API: ✅`
2. Asegúrate de estar en Modo Junior: revisa que muestre `Mode: junior`
3. Ejecuta un escaneo que encuentre issues (sin issues = sin explicaciones)

### Errores "No module found"

Reinstala con todas las dependencias:
```bash
pip install --upgrade qodacode
```

### El escaneo tarda mucho

Usa `/check` para escaneos rápidos. `/audit` es exhaustivo pero más lento.

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                    Qodacode TUI                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Welcome Box                         │   │
│  │    Proyecto | Modo | Estado API                     │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Área de Salida                     │   │
│  │    (RichLog scrolleable con resultados)             │   │
│  │                                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  > Input de Comandos                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Motor de Escaneo                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Secret  │  │Deep SAST │  │  Core    │                 │
│  │Detection │  │  Engine  │  │  Engine  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
└─────────────────────────────────────────────────────────────┘
            │
            ▼ (Solo Modo Junior)
┌─────────────────────────────────────────────────────────────┐
│                    Explicador IA                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ OpenAI   │  │Anthropic │  │  Gemini  │  │   Grok   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🆕 Nuevas Features v1.0.2 (Security Release)

### 1. 🛡️ Rate Limiting

La TUI ahora incluye protección contra uso excesivo:

- **Límites por defecto**: 60 escaneos/minuto, 30 llamadas IA/minuto
- **Protección automática**: Si excedes el límite, recibes un mensaje claro

**Ejemplo de mensaje cuando excedes límite:**
```
⚠️  Rate limit: 60 scans/minute. Wait 23s
```

**Configurar límites personalizados** en `.qodacode/config.json`:
```json
{
  "rate_limit": {
    "max_scans_per_minute": 100,
    "max_ai_calls_per_minute": 50,
    "enabled": true
  }
}
```

**Deshabilitar rate limiting** (no recomendado):
```json
{
  "rate_limit": {
    "enabled": false
  }
}
```

**Nota importante**: El rate limiting es por-instancia. Si abres múltiples terminales, cada una tiene sus propios límites independientes.

---

### 2. 📝 Audit Logging

Todas las operaciones de la TUI ahora se registran en `.qodacode/audit.jsonl`:

**Qué se registra:**
- Cada escaneo (`/check`, `/audit`, `/typosquat`) con duración y resultados
- Cambios de configuración (API key, modo junior/senior)
- Operaciones bloqueadas por rate limiting
- Errores durante escaneos

**Formato JSON Lines** (una línea por evento):
```json
{"timestamp":"2026-01-22T10:30:45.123Z","event":"scan","details":{"path":".","scan_type":"check","findings_count":3,"verdict":"READY","duration_ms":1243}}
{"timestamp":"2026-01-22T10:31:12.456Z","event":"config_change","details":{"field":"mode","old_value":"senior","new_value":"junior"}}
{"timestamp":"2026-01-22T10:31:30.789Z","event":"rate_limit","details":{"operation":"scan","limit":"60/min","wait_time_s":15}}
```

**Seguridad crítica**: Los logs automáticamente enmascaran secretos (API keys, contraseñas, tokens) antes de escribir a disco. Nunca verás credenciales en texto plano en los logs.

**Ver logs**:
```bash
cat .qodacode/audit.jsonl | jq .  # Con pretty print
tail -f .qodacode/audit.jsonl     # Seguimiento en tiempo real
```

**Compliance**: Los audit logs están diseñados para SOC2, GDPR y auditorías empresariales.

---

### 3. ⚡ Primera Ejecución Mejorada

La primera vez que ejecutes `/audit` (escaneo completo), verás:

```
⟳ First-time setup: Installing security engines...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✓ Gitleaks installed (~30 seconds)

✓ Setup complete! Future scans will be instant.
```

**Qué pasa:**
- Descarga automática de Gitleaks (15MB)
- Instalación de Semgrep vía pip (100MB)
- Barras de progreso visuales con Rich
- Solo ocurre una vez por sistema

**Después de la primera vez**: Todos los escaneos son instantáneos.

**Entornos restringidos** (Docker read-only, CI sin permisos): Si falla la instalación, la TUI continúa con los engines disponibles y muestra un mensaje claro.

---

### 4. 🔒 Security Hooks (Interno)

Aunque no es visible directamente en la TUI, v1.0.2 incluye detección avanzada de comandos peligrosos:

- **Patrones detectados**: `rm -rf`, `sudo`, `curl | bash`, `eval()`, etc.
- **Bypass detection**: Comandos codificados en base64, hex, URL encoding
- **Obfuscation detection**: Exceso de comillas, concatenación sospechosa
- **Integración MCP**: Los comandos que ejecuta un AI coding assistant son analizados antes de ejecutarse

Esta capa protege contra AI agents que intenten ejecutar comandos destructivos.

---

### 5. 📊 FAQ v1.0.2

**P: ¿El rate limiting me bloqueará si hago muchos escaneos seguidos?**
R: Solo si excedes 60 escaneos por minuto (1 escaneo por segundo). Para desarrollo normal, nunca lo notarás. Si lo necesitas más alto, configura `max_scans_per_minute` en `.qodacode/config.json`.

**P: ¿Los audit logs consumen mucho espacio?**
R: No. Cada entrada es ~200 bytes. 10,000 operaciones = ~2MB. El archivo crece lentamente y es fácil rotar con herramientas estándar.

**P: ¿Puedo ver el audit log desde la TUI?**
R: No directamente en v1.0.2. Usa `cat .qodacode/audit.jsonl | jq .` en otra terminal o añádelo a tu dashboard de compliance.

**P: ¿Qué pasa si cancelo la primera instalación de engines?**
R: La TUI continúa con los engines ya disponibles. Puedes reintentar más tarde ejecutando `/audit` de nuevo.

**P: ¿El rate limiting funciona entre múltiples terminales?**
R: No. Cada terminal tiene sus propios límites. Para rate limiting distribuido (cluster, CI con múltiples jobs), necesitarás una solución externa como Redis (roadmap v1.2.0).

---

## Historial de Versiones

| Versión | Cambios |
|---------|---------|
| 1.0.2 | **Security Release**: Rate limiting, audit logging (JSON Lines), first-run UX mejorada, security hooks avanzados |
| 0.5.0 | **`/typosquat`**: Detección de ataques supply chain. **`/api clear`**: Eliminar API key. Welcome box actualizado |
| 0.1.2 | Modo Junior, Learn Why IA, comando `/clean`, activación automática de modo |
| 0.1.1 | Layout de dos columnas, comando `/audit`, estado API en welcome box |
| 0.1.0 | Lanzamiento inicial de TUI |

---

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guías de contribución.

## Licencia

AGPL-3.0 License - ver [LICENSE](LICENSE) para detalles.
