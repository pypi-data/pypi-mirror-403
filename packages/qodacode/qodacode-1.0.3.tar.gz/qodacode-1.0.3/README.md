# Qodacode

**Your Personal Security Senior for AI Coding Agents** - The guardrail that protects you when Claude, Cursor, or Copilot generate code.

[![PyPI version](https://badge.fury.io/py/qodacode.svg)](https://badge.fury.io/py/qodacode)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

## What is Qodacode?

Qodacode is a **security guardrail for the AI coding era**. When AI assistants (Claude Code, Cursor, GitHub Copilot) generate or execute code, Qodacode acts as your senior reviewer:

- **🛡️ PreToolUse Protection**: Blocks dangerous commands before AI agents execute them (rm -rf, encoded bypasses, privilege escalation)
- **🔍 Real-time Scanning**: 4000+ security rules with intelligent bypass detection (base64, hex encoding, obfuscation)
- **📊 Audit Trails**: SOC2/GDPR-ready logs with automatic secret redaction
- **⚡ Rate Limiting**: Protects your wallet from runaway AI costs
- **🎓 AI Explanations**: Learn why issues matter with multi-provider AI support

**Three interfaces, one mission**: CLI (quick scans), TUI (interactive), and MCP Server (AI assistant integration).

## Quick Start

```bash
# Install
pip install qodacode

# Quick security scan
qodacode check

# Interactive terminal interface
qodacode

# Full security audit
qodacode audit
```

### macOS (Homebrew Python)

If you get permission errors with `pip`:

```bash
# Use pipx instead
pipx install qodacode

# Or use pip with --user flag
pip install --user qodacode
```

### Troubleshooting

**"command not found" after install:**
```bash
# Check where qodacode is installed
which qodacode

# If conflicts with old version in /opt/homebrew/bin/
rm /opt/homebrew/bin/qodacode
pipx install qodacode --force
```

**Python version error:**
Qodacode requires Python 3.10+. Check your version:
```bash
python3 --version
```

## Features

### Security Analysis
- **Secret Detection**: API keys, passwords, tokens, credentials
- **SAST**: SQL injection, XSS, command injection, path traversal
- **Syntax Validation**: Catch errors before runtime
- **Custom Rules**: Project-specific patterns

### Supply Chain Security
- **Typosquatting Detection**: Catches malicious package impersonators
- **Known Malware Database**: 30+ confirmed attack packages
- **Homoglyph Detection**: Unicode lookalike attacks
- **Keyboard Proximity Analysis**: Adjacent key typos

### AI-Powered Learning
- **Junior Mode**: Get explanations for every issue found
- **Multi-Provider**: OpenAI, Anthropic, Google Gemini, Grok
- **Batch Processing**: Efficient API usage

### False Positive Reduction
- **Semantic Context Analysis**: Auto-filters safe patterns like `os.environ`, `decrypt()`, test fixtures
- **Inline Ignore**: `# qodacode-ignore: SEC-001` to suppress specific lines
- **`.qodacodeignore`**: Gitignore-style exclusion patterns
- **Baseline Mode**: For legacy projects - only show NEW issues

## Interfaces

### CLI Commands

```bash
qodacode check              # Quick scan (syntax + secrets)
qodacode check --baseline   # Only show NEW issues (not in baseline)
qodacode audit              # Full security audit
qodacode typosquat          # Check dependencies for attacks
qodacode baseline save      # Save current issues as baseline
qodacode baseline show      # View baseline info
qodacode doctor             # Verify installation
```

### TUI (Interactive Terminal)

Launch with `qodacode` (no arguments):

```
/check      Quick scan
/audit      Full audit
/typosquat  Supply chain check
/ready      Production ready?
/mode       Toggle Junior/Senior mode
/api        Configure AI provider
/export     Save results
/help       Show commands
```

### MCP Server (AI Integration)

11 tools for AI coding assistants:

| Tool | Description |
|------|-------------|
| `quick_check` | Fast syntax + secrets scan |
| `full_audit` | Complete security analysis |
| `analyze_file` | Single file deep analysis |
| `check_dependencies` | Typosquatting detection |
| `get_issues` | Retrieve current issues |
| `explain_issue` | AI explanation for issue |
| `fix_issue` | Get fix suggestion |
| `get_project_status` | Overall project health |
| `configure_mode` | Set Junior/Senior mode |
| `list_rules` | Available detection rules |
| `search_patterns` | Search for code patterns |

## Production Verdict

Qodacode gives a clear answer: **Can I deploy this code?**

```
if critical_issues > 0:
    NOT READY - Fix N critical issues
else:
    READY FOR PRODUCTION (N warnings)
```

**Philosophy**: Only critical issues block deployment. High/Medium/Low are technical debt to track, not security blockers.

## Detection Engine

| Engine | Coverage |
|--------|----------|
| **Core Engine** | Syntax errors, custom patterns |
| **Secret Detection** | 50+ secret patterns (API keys, tokens, passwords) |
| **Deep SAST** | 4000+ security rules across languages |
| **Supply Chain** | Typosquatting, malware, homoglyphs |

## Architecture

Qodacode uses a hybrid architecture for performance and security:

```
┌─────────────────────────────────────────────────┐
│  Interfaces (Python)                            │
│  CLI, TUI, MCP Server, LSP                      │
├─────────────────────────────────────────────────┤
│  Orchestration Layer (Python)                   │
│  Multi-engine coordination, deduplication       │
├─────────────────────────────────────────────────┤
│  Core Algorithms (Rust - compiled)              │
│  Fingerprinting, similarity, pattern matching   │
├─────────────────────────────────────────────────┤
│  Detection Engines                              │
│  Semgrep, Gitleaks, Tree-sitter, OSV           │
└─────────────────────────────────────────────────┘
```

The Rust core module (`qodacode_core`) provides optimized algorithms:
- **Fingerprinting**: Stable issue IDs using BLAKE3
- **Similarity**: Levenshtein distance for typosquatting
- **Homoglyphs**: Unicode lookalike detection
- **Pattern Matching**: Aho-Corasick for safe pattern recognition

Falls back to pure Python when Rust extension is not available.

## Configuration

Configuration is stored in `.qodacode/config.json`:

```json
{
  "mode": "junior",
  "language": "en",
  "ai": {
    "api_key": "sk-...",
    "provider": "openai"
  }
}
```

### AI Provider Detection

API keys are auto-detected by prefix:

| Prefix | Provider |
|--------|----------|
| `sk-ant-*` | Anthropic (Claude) |
| `sk-*` | OpenAI (GPT) |
| `xai-*` | Grok (xAI) |
| `AIza*` | Google Gemini |

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **Critical** | Security vulnerability | Must fix before deploy |
| **High** | Significant issue | Should fix, doesn't block |
| **Medium** | Code quality concern | Review when possible |
| **Low** | Minor suggestion | Nice to have |

## Languages Supported

- Python
- JavaScript/TypeScript
- Go
- Java
- More coming...

## Why Qodacode?

| Feature | Qodacode | Traditional Linters |
|---------|----------|---------------------|
| Hybrid Analysis | Deterministic + AI | Rules only |
| Supply Chain | Typosquatting detection | No |
| AI Explanations | Multi-provider | No |
| Interactive TUI | Modern terminal UI | No |
| MCP Integration | AI assistant ready | No |

## Requirements

- Python 3.10 or higher
- pip (Python package manager)

### External Dependencies

Qodacode automatically manages external binaries:

- **Gitleaks**: Downloaded on first use to `~/.qodacode/bin/` (or uses system-installed version if available)
- **Semgrep**: Installed via pip as a Python dependency

## Acknowledgments

Qodacode orchestrates best-in-class open source security tools:

- **[Semgrep](https://semgrep.dev/)** - Lightweight static analysis for many languages (LGPL-2.1)
- **[Gitleaks](https://gitleaks.io/)** - Secret detection and prevention (MIT)
- **[Tree-sitter](https://tree-sitter.github.io/)** - Incremental parsing system (MIT)
- **[OSV](https://osv.dev/)** - Open Source Vulnerabilities database (Apache-2.0)

These projects are the detection engines. Qodacode adds orchestration, deduplication, AI explanations, and unified interfaces (CLI, TUI, MCP).

## License

AGPL-3.0 License - see [LICENSE](LICENSE) for details.

## Links

- [CLI Documentation](CLI.md)
- [TUI Documentation](TUI.md)
- [MCP Server Documentation](mcp.md)
