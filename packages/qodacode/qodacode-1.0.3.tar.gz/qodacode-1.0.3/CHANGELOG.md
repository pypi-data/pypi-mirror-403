# Changelog

All notable changes to Qodacode will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-01-22

### Added
- **Rate Limiting** (`qodacode/rate_limiter.py`)
  - Protects users from runaway AI agent costs
  - Configurable limits: 60 scans/min, 30 AI calls/min (default)
  - Token bucket algorithm with graceful error messages
  - Configuration via `.qodacode/config.json`

- **Structured Audit Logging** (`qodacode/audit_log.py`)
  - JSON Lines format (`.qodacode/audit.jsonl`)
  - Automatic secret redaction before logging (CRITICAL security fix)
  - Tracks: scans, blocks, AI calls, config changes, errors
  - Enterprise compliance ready (SOC2, GDPR)

- **Progressive Engine Installation** (`qodacode/engine_installer.py`)
  - Beautiful first-run UX with Rich progress bars
  - One-time setup (~30 seconds)
  - Auto-detection and installation of Semgrep/Gitleaks
  - Clear messaging: "Future scans will be instant"

- **Intelligent Security Hooks** (`qodacode/security_hooks.py`)
  - Advanced bypass detection (base64, hex, URL encoding)
  - Command obfuscation detection
  - Environment variable manipulation detection
  - Safe alternative suggestions for dangerous commands
  - PreToolUse integration ready for Claude Code hooks

- **MCP Integration**
  - New tool: `analyze_command_safety` for PreToolUse hooks
  - Rate limiting integrated in `full_audit`
  - Audit logging for all MCP operations

### Changed
- **Obfuscation detection**: Changed from BLOCK to WARNING to reduce false positives
- **Pipe chain threshold**: Increased from 3 to 4 pipes before warning
- **CLI**: Auto-install engines on first `--deep/--secrets/--all` usage
- **README**: Updated headline to emphasize AI coding assistant protection

### Fixed
- **CRITICAL**: Audit logs no longer leak secrets - automatic masking applied recursively
- **Engine installer**: Added PermissionError handling for restricted environments (Docker, CI)
- **Rate limiter**: Documented per-instance limitation (not distributed)

### Security
- All audit log entries now pass through `mask_secrets()` before disk write
- Prevents AWS keys, API tokens, passwords from appearing in logs
- Defense-in-depth: logs are safe even if secrets bypass detection

## [1.0.1] - 2026-01-22

### Changed
- Updated PyPI metadata:
  - Development Status: Alpha → Beta
  - Added Topic classifiers: Security, Testing
- README improvements:
  - Added Acknowledgments section (Semgrep, Gitleaks, Tree-sitter, OSV)
  - Documented external dependencies clearly
- License clarification: Consistent AGPL-3.0 across all files

### Fixed
- README badge: MIT → AGPL-3.0 (corrected licensing display)

## [1.0.0] - 2026-01-21

### Added
- Initial public release
- Multi-engine security orchestration:
  - Tree-sitter for structural analysis
  - Semgrep for deep SAST
  - Gitleaks for secret detection
  - OSV for dependency vulnerabilities
- Three interfaces: CLI, TUI, MCP Server
- AI-powered explanations (multi-provider: OpenAI, Anthropic, Grok)
- Typosquatting detection with 3-metric analysis
- Production verdict system: READY / NOT READY
- Baseline mode for incremental scanning
- 4000+ security rules from multiple sources

### Security
- AGPL-3.0 license for copyleft protection
- Local-first architecture (no data leaves your machine)
- Binary download with version pinning (Gitleaks v8.18.4)

---

## Upcoming

### v1.1.0 (Planned - February 2026)
- License key system for premium features
- Premium teaser messages
- Policy engine with YAML custom rules
- Auto-fix mode implementation
- Compliance report templates (SOC2, HIPAA)

### v1.2.0 (Planned - March 2026)
- Distributed rate limiting (Redis support)
- Centralized dashboard (self-hosted)
- RBAC for team deployments
- Enhanced integration tests
- Java/Go/Rust tree-sitter parsers

---

[1.0.2]: https://github.com/yourusername/qodacode/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/yourusername/qodacode/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/yourusername/qodacode/releases/tag/v1.0.0
