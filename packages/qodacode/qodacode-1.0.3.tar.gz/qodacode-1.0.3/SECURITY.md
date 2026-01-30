# Security Policy

## Reporting a Vulnerability

**Do NOT open public issues for security vulnerabilities.**

To report a security vulnerability, please email:
- **Email**: (will be added when public repo is ready)
- **Response time**: We aim to respond within 48 hours
- **Disclosure**: Coordinated disclosure after fix is released

Please include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.2   | :white_check_mark: |
| 1.0.1   | :x:                |
| 1.0.0   | :x:                |
| < 1.0   | :x:                |

## Security Features

Qodacode is designed as a security tool and includes multiple layers of protection:

### 1. Secret Redaction (v1.0.2+)
- **Audit logs automatically mask secrets** before writing to disk
- Recursive sanitization of all logged data (commands, findings, details)
- Prevents credential leakage even if secrets slip through detection

### 2. Command Safety Analysis
- **PreToolUse hook integration** for AI coding assistants
- Detects dangerous patterns: file destruction, privilege escalation, code execution
- Encoding bypass detection: base64, hex, URL encoding, unicode
- Obfuscation detection: excessive quoting, string concatenation, variable manipulation

### 3. Rate Limiting
- **Protects users from runaway AI costs**
- Configurable limits per operation type
- Per-instance protection (see limitations in docs)

### 4. Dependency Integrity
- **Gitleaks downloaded with version pinning** (v8.18.4)
- Checksum validation (future enhancement)
- Semgrep installed via official PyPI package

## Known Limitations

### Rate Limiter (v1.0.2)
- **Per-instance only**: Multiple terminals or CI jobs each have separate limits
- Not distributed across a cluster
- For enterprise distributed limiting, external solutions (Redis) required

### Engine Installation (v1.0.2)
- **First-run downloads**: Gitleaks (~15MB) downloaded on first use
- May fail in air-gapped environments or restricted Docker containers
- Graceful degradation: tool continues with available engines

## Security Best Practices

### For Users
1. **Review audit logs regularly**: Check `.qodacode/audit.jsonl` for blocked operations
2. **Configure rate limits**: Adjust in `.qodacode/config.json` for your workflow
3. **Keep updated**: Run `pip install --upgrade qodacode` regularly
4. **Verify downloads**: Ensure Gitleaks downloads from official GitHub releases

### For Integrators (MCP/API)
1. **Use analyze_command_safety**: Always check commands before execution
2. **Respect BLOCK verdicts**: Never override security blocks automatically
3. **Log all operations**: Enable audit logging for compliance
4. **Test bypass detection**: Verify encoding/obfuscation detection works

## Security Roadmap

### v1.1.0 (Planned)
- [ ] Checksum validation for downloaded binaries
- [ ] Signature verification for Gitleaks releases
- [ ] Policy engine for custom security rules
- [ ] Enhanced audit log encryption option

### v1.2.0 (Planned)
- [ ] Distributed rate limiting (Redis support)
- [ ] Centralized audit log aggregation
- [ ] RBAC for team deployments
- [ ] Compliance report generation (SOC2, GDPR templates)

## Security Credits

We thank the following for responsible disclosure:
- (None yet - be the first!)

## License

Qodacode is licensed under AGPL-3.0-or-later. See [LICENSE](LICENSE) for details.

Security is our priority. If you have concerns or questions, please reach out.
