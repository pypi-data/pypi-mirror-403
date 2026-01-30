# LEGAL & COMMERCIAL SAFETY GUIDELINES

**Version:** 1.1
**Enforcement:** STRICT
**Last Updated:** January 2026
**Context:** QODACODE will be a commercial product with proprietary features.

---

## 1. The "Black Box" Architecture Rule (License Firewall)

To ensure we can commercialize QODACODE without violating LGPL/GPL licenses of underlying tools (Semgrep, etc.), we must strictly adhere to the **Separation of Concerns**:

- **DO NOT** copy-paste source code from external open-source projects into our codebase.
- **DO NOT** statically link internal libraries of tools like Semgrep or Gitleaks.
- **MUST** integrate via **`subprocess` (CLI execution)** or standard API calls only.

> **Explanation:** Treating external tools as separate processes (just like calling `ls` or `git`) prevents their license obligations from "infecting" our proprietary code.

- **MUST** treat engine outputs (JSON) as untrusted data until validated by our Pydantic layer.

---

## 2. Attribution & Transparency

We build on giants, we do not steal from them.

- **DO NOT** try to hide or obfuscate which engine found an issue.
- **MUST** explicitly label the source of every finding in the UI.

> **Example:** `[Source: Semgrep]` or `[Source: Gitleaks]`

- **MUST** maintain a "Credits" section in the CLI (`qodacode credits`) listing the open-source tools used.

---

## 3. Data Privacy (Local-First Promise)

Our biggest selling point is trust.

- **DO NOT** implement any code that sends user code to a cloud server without explicit, opt-in consent.
- **MUST** ensure all default scanners (Semgrep, Gitleaks, Tree-sitter) run completely **offline/local**.
- **MUST** clearly label any feature that requires internet access (e.g., "checking OSV database for updates").

---

## 4. The Proprietary Boundary (What we own)

To preserve the value of the "Pro/Enterprise" version, we must clearly define our IP:

### Open Source/Free Layer:
- The capability to run the scanners.
- The basic CLI interface.

### Proprietary Layer (Do not open-source this logic):
- The **Context Engine** logic (how we correlate cross-file issues).
- The **Memory/History** logic (decisions stored in ChromaDB).
- Any custom rules we write ourselves (not community rules).
- The "Fix Suggestion" logic driven by our specific prompts.

---

## 5. Development Constraints for Claude

When writing code for `engines/` or `cli/`:

1. **Dependency Check:** Never bundle binaries (like the `semgrep` executable) inside our git repo. Always check if the user has it installed, or guide them to install it via their package manager (`pip`, `brew`).

2. **Standard Configs:** Use standard configuration flags for external tools. Do not patch or modify their config files dynamically unless necessary for the specific scan.

3. **Clean Output:** Do not suppress copyright headers or license info from the external tool's raw `stderr` output if we display logs.

---

## 6. Versioning & Compatibility (Added by Claude)

External tools can change their output format at any time.

- **MUST** document minimum supported versions of each external tool:

| Tool | Minimum Version | License |
|------|-----------------|---------|
| Semgrep | >=1.0.0 | LGPL-2.1 |
| Gitleaks | >=8.0.0 | MIT |
| Tree-sitter | >=0.20.0 | MIT |
| ChromaDB | >=0.4.0 | Apache 2.0 |

- **MUST** handle gracefully if a tool changes its JSON output schema.
- **MUST** have integration tests that detect breaking changes in external APIs.
- **SHOULD** pin to known-working versions in documentation.

---

## 7. API Terms of Service (Added by Claude)

Some integrations have usage terms we must respect.

### OSV API
- **Rate Limits:** Be respectful, batch queries when possible.
- **Terms:** Public API, no authentication required for basic usage.
- **Our Implementation:** `qodacode/osv.py` uses batch queries.

### Semgrep Registry (--config=auto)
- When using `--config=auto`, we're using Semgrep's community rules.
- These rules are licensed under various open source licenses.
- **Our 12 AST rules** in `qodacode/rules/` are 100% our proprietary code.

### Gitleaks Patterns
- Default patterns are MIT licensed.
- We can use them freely via subprocess.

---

## 8. License Summary Table

| Component | License | Can Commercialize? | Notes |
|-----------|---------|-------------------|-------|
| **Our Code** (`qodacode/`) | Proprietary | ✅ Yes | We own this |
| **Semgrep** (binary) | LGPL-2.1 | ✅ Via subprocess | No linking |
| **Gitleaks** (binary) | MIT | ✅ Yes | Permissive |
| **Tree-sitter** (library) | MIT | ✅ Yes | Permissive |
| **ChromaDB** (library) | Apache 2.0 | ✅ Yes | Permissive |
| **Pydantic** (library) | MIT | ✅ Yes | Permissive |
| **Rich** (library) | MIT | ✅ Yes | Permissive |
| **Click** (library) | BSD-3 | ✅ Yes | Permissive |

---

## 9. Checklist Before Release

Before any public release:

- [ ] All findings show `[Source: engine_name]` attribution
- [ ] `qodacode credits` command exists and lists all OSS used
- [ ] No binary blobs bundled in repository
- [ ] All external tool calls use subprocess (not linking)
- [ ] Default mode is 100% offline
- [ ] Any internet features are opt-in and clearly labeled
- [ ] README includes attribution to Semgrep, Gitleaks, Tree-sitter
- [ ] LICENSE file is clear about proprietary vs OSS components

---

## 10. What Happens If We Violate These Rules

| Violation | Consequence |
|-----------|-------------|
| Copy-paste Semgrep source code | Must open-source our code (LGPL) |
| Send code to cloud without consent | Loss of trust, potential GDPR issues |
| Hide attribution | Ethical violation, community backlash |
| Bundle binaries | Distribution issues, license complications |

---

*Failure to follow these guidelines puts the commercial viability of the project at risk.*

*This document must be reviewed before any major feature implementation.*
