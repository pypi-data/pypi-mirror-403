"""
AI-powered code explanations for Qodacode.

Supports multiple LLM providers:
- Anthropic Claude (ANTHROPIC_API_KEY)
- OpenAI GPT (OPENAI_API_KEY)
- Ollama local (OLLAMA_HOST, free, no API key needed)

Configuration:
1. Environment variables: ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA_HOST
2. Config file: .qodacode/config.json with "ai_provider" and "ai_api_key"
3. CLI: qodacode config --ai-provider claude --ai-api-key sk-xxx
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("qodacode.ai")

# Supported providers
Provider = Literal["anthropic", "openai", "ollama", "none"]


@dataclass
class AIConfig:
    """AI provider configuration."""
    provider: Provider
    api_key: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None  # For Ollama or custom endpoints


@dataclass
class Explanation:
    """AI-generated explanation for an issue."""
    why_it_matters: str
    how_to_fix: str
    code_example: Optional[str] = None
    learn_more: Optional[str] = None
    is_ai_generated: bool = False
    provider: str = "static"


# Static explanations (fallback when no API key)
STATIC_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "SEC-001": {
        "why": "Hardcoded secrets in source code can be exposed through version control, logs, or decompilation. Attackers who gain access to your repository can use these credentials.",
        "fix": "Use environment variables or a secrets manager (AWS Secrets Manager, HashiCorp Vault). Never commit secrets to version control.",
    },
    "SEC-002": {
        "why": "SQL injection allows attackers to execute arbitrary SQL commands, potentially reading, modifying, or deleting data.",
        "fix": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
    },
    "SEC-003": {
        "why": "Command injection allows attackers to execute system commands, potentially taking control of your server.",
        "fix": "Use subprocess with shell=False and validate all inputs. Avoid os.system().",
    },
    "SEC-004": {
        "why": "XSS allows attackers to inject scripts that steal sessions, credentials, or personal data.",
        "fix": "Escape user input before rendering in HTML. Use templating engines with auto-escaping.",
    },
    "SEC-005": {
        "why": "Unprotected endpoints expose data or functionality to unauthorized users.",
        "fix": "Add authentication middleware. Use @login_required or similar decorators.",
    },
    "SEC-006": {
        "why": "Insecure deserialization can execute arbitrary code via malicious objects.",
        "fix": "Avoid pickle/yaml.load with untrusted data. Use JSON or validate before deserializing.",
    },
    "SEC-007": {
        "why": "Path traversal allows reading files outside intended directories (../../etc/passwd).",
        "fix": "Use os.path.basename() and verify paths are within allowed directories.",
    },
    "ROB-001": {
        "why": "Missing error handling causes crashes and data loss.",
        "fix": "Wrap risky operations in try/except. Handle specific exceptions.",
    },
    "ROB-002": {
        "why": "Operations without timeouts hang indefinitely, freezing your app.",
        "fix": "Set timeouts on network calls, DB queries, and API requests.",
    },
    "ROB-003": {
        "why": "Unvalidated input causes crashes or security issues.",
        "fix": "Validate types, ranges, formats at system boundaries.",
    },
    "ROB-004": {
        "why": "Without retries, transient failures cause immediate errors.",
        "fix": "Implement exponential backoff. Use tenacity library.",
    },
    "ROB-005": {
        "why": "One failing dependency shouldn't crash everything.",
        "fix": "Add fallbacks: cached data, defaults, or degraded mode.",
    },
    "MNT-001": {
        "why": "Long functions are hard to test and maintain.",
        "fix": "Extract into smaller functions that do one thing.",
    },
    "MNT-002": {
        "why": "Many parameters indicate poor abstraction.",
        "fix": "Group into data classes or config objects.",
    },
    "OPS-001": {
        "why": "Without logging, production debugging is impossible.",
        "fix": "Add structured logging with context (request_id, user_id).",
    },
    "OPS-002": {
        "why": "Hardcoded config can't change per environment.",
        "fix": "Use env vars or config files. Different configs per env.",
    },
    "DEP-001": {
        "why": "Vulnerable packages have known exploits.",
        "fix": "Update to patched version or find alternatives.",
    },
    "DEP-002": {
        "why": "Outdated deps lack patches and may conflict.",
        "fix": "Use dependabot/renovate for automated updates.",
    },
    "DEP-003": {
        "why": "Unused deps increase attack surface.",
        "fix": "Remove from package manifest.",
    },
    "DEP-004": {
        "why": "GPL/AGPL may conflict with proprietary code.",
        "fix": "Check license compatibility. Use alternatives if needed.",
    },
}


def load_config() -> AIConfig:
    """
    Load AI configuration from environment or config file.

    Priority:
    1. Environment variables (ANTHROPIC_API_KEY, OPENAI_API_KEY, OLLAMA_HOST)
    2. .qodacode/config.json
    3. Default: no AI (static explanations)
    """
    # Check environment variables first
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AIConfig(
            provider="anthropic",
            api_key=os.environ["ANTHROPIC_API_KEY"],
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
        )

    if os.environ.get("OPENAI_API_KEY"):
        return AIConfig(
            provider="openai",
            api_key=os.environ["OPENAI_API_KEY"],
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        )

    if os.environ.get("OLLAMA_HOST") or os.environ.get("OLLAMA_MODEL"):
        return AIConfig(
            provider="ollama",
            base_url=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            model=os.environ.get("OLLAMA_MODEL", "llama3.2"),
        )

    # Check config file
    config_paths = [
        Path.cwd() / ".qodacode" / "config.json",
        Path.home() / ".qodacode" / "config.json",
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)

                provider = data.get("ai_provider", "none")
                if provider == "anthropic":
                    return AIConfig(
                        provider="anthropic",
                        api_key=data.get("ai_api_key"),
                        model=data.get("ai_model", "claude-3-haiku-20240307"),
                    )
                elif provider == "openai":
                    return AIConfig(
                        provider="openai",
                        api_key=data.get("ai_api_key"),
                        model=data.get("ai_model", "gpt-4o-mini"),
                    )
                elif provider == "ollama":
                    return AIConfig(
                        provider="ollama",
                        base_url=data.get("ai_base_url", "http://localhost:11434"),
                        model=data.get("ai_model", "llama3.2"),
                    )
            except Exception as e:
                logger.debug(f"Could not load config from {config_path}: {e}")

    # No AI configured
    return AIConfig(provider="none")


def save_config(
    provider: Provider,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Path:
    """
    Save AI configuration to .qodacode/config.json

    Returns the path to the config file.
    """
    config_dir = Path.cwd() / ".qodacode"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "config.json"

    # Load existing config
    existing = {}
    if config_path.exists():
        try:
            with open(config_path) as f:
                existing = json.load(f)
        except Exception:
            pass

    # Update with new values
    existing["ai_provider"] = provider
    if api_key:
        existing["ai_api_key"] = api_key
    if model:
        existing["ai_model"] = model
    if base_url:
        existing["ai_base_url"] = base_url

    # Save
    with open(config_path, "w") as f:
        json.dump(existing, f, indent=2)

    return config_path


def is_ai_available() -> bool:
    """Check if AI explanations are available."""
    config = load_config()
    return config.provider != "none"


def get_provider_info() -> Dict[str, Any]:
    """Get information about configured AI provider."""
    config = load_config()
    return {
        "provider": config.provider,
        "model": config.model,
        "available": config.provider != "none",
    }


async def explain_with_anthropic(
    config: AIConfig,
    prompt: str,
) -> Optional[str]:
    """Generate explanation using Anthropic Claude."""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=config.api_key)
        message = client.messages.create(
            model=config.model or "claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except ImportError:
        logger.warning("anthropic package not installed: pip install anthropic")
        return None
    except Exception as e:
        logger.warning(f"Anthropic API error: {e}")
        return None


async def explain_with_openai(
    config: AIConfig,
    prompt: str,
) -> Optional[str]:
    """Generate explanation using OpenAI GPT."""
    try:
        import openai

        client = openai.OpenAI(api_key=config.api_key)
        response = client.chat.completions.create(
            model=config.model or "gpt-4o-mini",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except ImportError:
        logger.warning("openai package not installed: pip install openai")
        return None
    except Exception as e:
        logger.warning(f"OpenAI API error: {e}")
        return None


async def explain_with_ollama(
    config: AIConfig,
    prompt: str,
) -> Optional[str]:
    """Generate explanation using local Ollama."""
    try:
        import httpx

        base_url = config.base_url or "http://localhost:11434"
        model = config.model or "llama3.2"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                }
            )
            response.raise_for_status()
            return response.json().get("response")
    except ImportError:
        logger.warning("httpx package not installed: pip install httpx")
        return None
    except Exception as e:
        logger.warning(f"Ollama error: {e}")
        return None


def build_prompt(
    rule_id: str,
    issue_message: str,
    code_snippet: str,
    filepath: str,
    line: int,
) -> str:
    """Build the prompt for AI explanation."""
    static = STATIC_EXPLANATIONS.get(rule_id, {})

    return f"""You are a code security and quality expert teaching a junior developer.

**File:** {filepath}:{line}
**Rule:** {rule_id}
**Issue:** {issue_message}

**Code:**
```
{code_snippet}
```

**Context:** {static.get('why', 'Security/quality issue')}

Explain:
1. **Why it's a problem** (specific to THIS code)
2. **How to fix it** (corrected code)

Respond in JSON:
{{"why_it_matters": "...", "how_to_fix": "...", "code_example": "corrected code here"}}

Be concise but educational. The dev should UNDERSTAND, not just copy."""


async def explain_with_ai(
    rule_id: str,
    issue_message: str,
    code_snippet: str,
    filepath: str,
    line: int,
) -> Explanation:
    """Generate contextual explanation using configured AI provider."""
    config = load_config()

    if config.provider == "none":
        return get_static_explanation(rule_id)

    prompt = build_prompt(rule_id, issue_message, code_snippet, filepath, line)

    # Call appropriate provider
    response = None
    if config.provider == "anthropic":
        response = await explain_with_anthropic(config, prompt)
    elif config.provider == "openai":
        response = await explain_with_openai(config, prompt)
    elif config.provider == "ollama":
        response = await explain_with_ollama(config, prompt)

    if not response:
        return get_static_explanation(rule_id)

    # Parse JSON response
    try:
        import re
        json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return Explanation(
                why_it_matters=data.get("why_it_matters", ""),
                how_to_fix=data.get("how_to_fix", ""),
                code_example=data.get("code_example"),
                is_ai_generated=True,
                provider=config.provider,
            )
    except Exception:
        pass

    # Fallback: use raw response
    static = STATIC_EXPLANATIONS.get(rule_id, {})
    return Explanation(
        why_it_matters=response[:500],
        how_to_fix=static.get("fix", "Review the code."),
        is_ai_generated=True,
        provider=config.provider,
    )


def get_static_explanation(rule_id: str) -> Explanation:
    """Get static (pre-written) explanation for a rule."""
    static = STATIC_EXPLANATIONS.get(rule_id, {
        "why": "This issue may affect code quality or security.",
        "fix": "Review the code and apply best practices.",
    })

    return Explanation(
        why_it_matters=static["why"],
        how_to_fix=static["fix"],
        is_ai_generated=False,
        provider="static",
    )


def explain_sync(
    rule_id: str,
    issue_message: str = "",
    code_snippet: str = "",
    filepath: str = "",
    line: int = 0,
) -> Explanation:
    """Synchronous wrapper for explanations."""
    if not is_ai_available():
        return get_static_explanation(rule_id)

    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        explain_with_ai(rule_id, issue_message, code_snippet, filepath, line)
    )


def get_code_context(filepath: str, line: int, context_lines: int = 5) -> str:
    """Extract code context around a line."""
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()

        start = max(0, line - context_lines - 1)
        end = min(len(lines), line + context_lines)

        context = []
        for i in range(start, end):
            prefix = ">>> " if i == line - 1 else "    "
            context.append(f"{prefix}{i + 1}: {lines[i].rstrip()}")

        return "\n".join(context)
    except Exception:
        return ""


def explain_issue(
    rule_id: str,
    filepath: str = "",
    line: int = 0,
    message: str = "",
    use_ai: bool = True,
) -> Dict[str, Any]:
    """
    Get explanation for an issue (main API for MCP and CLI).

    Args:
        rule_id: The rule ID (e.g., SEC-001)
        filepath: Path to the file
        line: Line number
        message: Issue message
        use_ai: Whether to use AI if available

    Returns:
        Dictionary with explanation data
    """
    code_context = ""
    if filepath and line > 0:
        code_context = get_code_context(filepath, line)

    if use_ai and is_ai_available() and code_context:
        explanation = explain_sync(
            rule_id=rule_id,
            issue_message=message,
            code_snippet=code_context,
            filepath=filepath,
            line=line,
        )
    else:
        explanation = get_static_explanation(rule_id)

    provider_info = get_provider_info()

    return {
        "rule_id": rule_id,
        "why_it_matters": explanation.why_it_matters,
        "how_to_fix": explanation.how_to_fix,
        "code_example": explanation.code_example,
        "is_ai_generated": explanation.is_ai_generated,
        "provider": explanation.provider,
        "ai_available": provider_info["available"],
        "ai_provider": provider_info["provider"],
    }


def batch_learn_why(issues: list, ai_config: dict) -> Optional[str]:
    """
    Generate a "Learn Why" summary from top issues using ONE API call.

    Args:
        issues: List of Issue objects from scan
        ai_config: Dict with 'provider' and 'api_key'

    Returns:
        Formatted "Learn Why" text or None if failed
    """
    if not issues or not ai_config.get("api_key"):
        return None

    # Helper to detect test files
    def is_test_file(filepath: str) -> bool:
        import os
        name = os.path.basename(filepath).lower()
        path_lower = filepath.lower()
        return (name.startswith("test_") or name.endswith("_test.py") or
                "/tests/" in path_lower or "/__tests__/" in path_lower)

    # Filter: exclude test files, prioritize by severity
    prod_issues = [i for i in issues if not is_test_file(i.location.filepath)]

    # Sort by severity priority
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    prod_issues.sort(key=lambda x: severity_order.get(x.severity.value, 4))

    # Take top 5
    priority_issues = prod_issues[:5]

    if not priority_issues:
        # Fallback if all issues are in tests
        priority_issues = issues[:3]

    # Build batch prompt
    issues_text = "\n".join([
        f"- {i.location.filepath}:{i.location.line} [{i.severity.value}] {i.message}"
        for i in priority_issues
    ])

    # Build educational prompt (English only)
    prompt = f"""You are a code mentor teaching a junior developer. Explain each issue in an EDUCATIONAL way.

Issues found:
{issues_text}

For each issue, explain:
1. 📍 Location (file:line)
2. ❓ WHAT is wrong and WHY it's dangerous (in simple terms)
3. ✅ HOW to fix it with a code example if applicable

Use this format:
───
📍 file.py:123
❓ [Explanation of the problem in 2-3 educational sentences]
✅ [How to fix it with example if useful]
───

Be friendly but informative. The goal is for the junior to LEARN, not just fix."""

    # Call AI (sync for simplicity)
    provider = ai_config.get("provider", "anthropic")
    api_key = ai_config.get("api_key")

    # Use httpx for all providers (no SDK dependencies needed)
    import httpx

    try:
        if provider == "anthropic":
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            data = response.json()
            if "error" in data:
                raise RuntimeError(f"Anthropic API error: {data['error'].get('message', data['error'])}")
            return data["content"][0]["text"]

        elif provider == "openai":
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            data = response.json()
            if "error" in data:
                raise RuntimeError(f"OpenAI API error: {data['error'].get('message', data['error'])}")
            if "choices" not in data:
                raise RuntimeError(f"OpenAI unexpected response: {list(data.keys())}")
            return data["choices"][0]["message"]["content"]

        elif provider == "gemini":
            response = httpx.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30.0
            )
            data = response.json()
            if "error" in data:
                raise RuntimeError(f"Gemini API error: {data['error'].get('message', data['error'])}")
            return data["candidates"][0]["content"]["parts"][0]["text"]

        elif provider == "grok":
            response = httpx.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "grok-beta",
                    "max_tokens": 300,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )
            data = response.json()
            if "error" in data:
                raise RuntimeError(f"Grok API error: {data['error'].get('message', data['error'])}")
            if "choices" not in data:
                raise RuntimeError(f"Grok unexpected response: {list(data.keys())}")
            return data["choices"][0]["message"]["content"]

        else:
            raise ValueError(f"Unknown provider: {provider}")
    except RuntimeError:
        # Re-raise RuntimeError as-is (already formatted)
        raise
    except Exception as e:
        # Wrap other exceptions with context
        raise RuntimeError(f"AI call failed ({provider}): {e}")
