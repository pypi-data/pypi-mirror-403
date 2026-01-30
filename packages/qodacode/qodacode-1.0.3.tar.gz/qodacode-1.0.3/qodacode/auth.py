"""
Qodacode Authentication Module.

Handles authentication with Qodacode Cloud for premium features.

Flow:
1. User runs: qodacode login
2. Opens browser for OAuth or accepts token
3. Stores credentials in ~/.qodacode/credentials.json
4. CLI uses token for premium features and sync
"""

import json
import hashlib
import platform
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class AuthProvider(Enum):
    """Supported authentication providers."""
    QODACODE = "qodacode"  # Native Qodacode Cloud
    GITHUB = "github"      # GitHub OAuth
    GOOGLE = "google"      # Google OAuth


class SubscriptionTier(Enum):
    """Subscription tiers."""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    BUSINESS = "business"


@dataclass
class AuthCredentials:
    """Authentication credentials."""
    token: str
    provider: str
    email: Optional[str] = None
    user_id: Optional[str] = None
    expires_at: Optional[str] = None
    tier: str = "free"
    org_id: Optional[str] = None
    org_name: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if credentials are expired."""
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.now(expiry.tzinfo) > expiry
        except (ValueError, TypeError):
            return False

    def is_premium(self) -> bool:
        """Check if user has premium tier."""
        return self.tier in ("pro", "team", "business")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# CREDENTIAL STORAGE
# ─────────────────────────────────────────────────────────────────────────────

def get_credentials_path() -> Path:
    """Get path to credentials file.

    Stored in user home directory, not project directory.
    This is intentional for security (not committed to git).
    """
    config_dir = Path.home() / ".qodacode"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "credentials.json"


def load_credentials() -> Optional[AuthCredentials]:
    """Load stored credentials.

    Returns None if:
    - No credentials file exists
    - Credentials are expired
    - Credentials are invalid
    """
    creds_path = get_credentials_path()

    if not creds_path.exists():
        return None

    try:
        with open(creds_path, "r") as f:
            data = json.load(f)

        creds = AuthCredentials(
            token=data.get("token", ""),
            provider=data.get("provider", "qodacode"),
            email=data.get("email"),
            user_id=data.get("user_id"),
            expires_at=data.get("expires_at"),
            tier=data.get("tier", "free"),
            org_id=data.get("org_id"),
            org_name=data.get("org_name"),
        )

        if creds.is_expired():
            return None

        return creds
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save_credentials(creds: AuthCredentials) -> Path:
    """Save credentials to file.

    Returns path to credentials file.
    """
    creds_path = get_credentials_path()

    with open(creds_path, "w") as f:
        json.dump(creds.to_dict(), f, indent=2)

    # Set restrictive permissions (owner read/write only)
    creds_path.chmod(0o600)

    return creds_path


def delete_credentials() -> bool:
    """Delete stored credentials (logout).

    Returns True if credentials were deleted, False if none existed.
    """
    creds_path = get_credentials_path()

    if creds_path.exists():
        creds_path.unlink()
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# DEVICE FINGERPRINT
# ─────────────────────────────────────────────────────────────────────────────

def get_device_id() -> str:
    """Generate a unique device identifier.

    Used for license verification and device management.
    """
    # Combine machine identifiers
    machine_info = [
        platform.node(),           # hostname
        platform.machine(),        # CPU architecture
        platform.system(),         # OS
        str(Path.home()),          # Home directory path
    ]

    combined = ":".join(machine_info)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────────
# CLOUD API
# ─────────────────────────────────────────────────────────────────────────────

# Cloud API base URL (will be configurable for enterprise)
QODACODE_CLOUD_URL = "https://api.qodacode.com"

# For development/testing
QODACODE_CLOUD_URL_DEV = "http://localhost:3000/api"


def get_cloud_url() -> str:
    """Get the Cloud API URL.

    Checks environment variable for override (useful for dev/enterprise).
    """
    import os
    return os.environ.get("QODACODE_CLOUD_URL", QODACODE_CLOUD_URL)


async def verify_token_async(token: str) -> Optional[Dict[str, Any]]:
    """Verify token with cloud and get user info.

    Returns user info dict if valid, None if invalid.

    Response format:
    {
        "valid": true,
        "user_id": "usr_xxx",
        "email": "user@example.com",
        "tier": "pro",
        "org_id": "org_xxx",
        "org_name": "Acme Corp",
        "expires_at": "2026-02-20T00:00:00Z"
    }
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{get_cloud_url()}/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    return data
            return None
    except httpx.RequestError:
        return None


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Synchronous wrapper for verify_token_async."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(verify_token_async(token))


async def login_with_device_code_async() -> Optional[Dict[str, Any]]:
    """Start device code flow for login.

    Returns device code info for user to complete login in browser.

    Response format:
    {
        "device_code": "xxx",
        "user_code": "ABCD-1234",
        "verification_uri": "https://qodacode.com/activate",
        "expires_in": 900,
        "interval": 5
    }
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{get_cloud_url()}/auth/device",
                json={
                    "client_id": "qodacode-cli",
                    "device_id": get_device_id(),
                },
                timeout=10.0
            )

            if response.status_code == 200:
                return response.json()
            return None
    except httpx.RequestError:
        return None


async def poll_for_token_async(device_code: str, interval: int = 5, max_attempts: int = 60) -> Optional[str]:
    """Poll for access token after device code flow.

    Returns access token if login completed, None if expired/failed.
    """
    import httpx
    import asyncio

    for _ in range(max_attempts):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{get_cloud_url()}/auth/token",
                    json={
                        "grant_type": "device_code",
                        "device_code": device_code,
                        "client_id": "qodacode-cli",
                    },
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")

                if response.status_code == 400:
                    data = response.json()
                    error = data.get("error")
                    if error == "authorization_pending":
                        await asyncio.sleep(interval)
                        continue
                    elif error == "slow_down":
                        await asyncio.sleep(interval * 2)
                        continue
                    else:
                        # expired_token, access_denied
                        return None

        except httpx.RequestError:
            await asyncio.sleep(interval)
            continue

    return None


# ─────────────────────────────────────────────────────────────────────────────
# PREMIUM RULES DOWNLOAD
# ─────────────────────────────────────────────────────────────────────────────

def get_premium_rules_path() -> Path:
    """Get path to premium rules file."""
    config_dir = Path.home() / ".qodacode"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "premium_rules.enc"


async def download_premium_rules_async(token: str) -> bool:
    """Download premium rules if user has valid license.

    Rules are encrypted and signed, only valid with matching license.

    Returns True if download successful, False otherwise.
    """
    import httpx

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{get_cloud_url()}/premium/rules",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )

            if response.status_code == 200:
                rules_path = get_premium_rules_path()
                rules_path.write_bytes(response.content)
                rules_path.chmod(0o600)
                return True
            return False
    except httpx.RequestError:
        return False


def download_premium_rules(token: str) -> bool:
    """Synchronous wrapper for download_premium_rules_async."""
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(download_premium_rules_async(token))


def has_premium_rules() -> bool:
    """Check if premium rules are downloaded."""
    return get_premium_rules_path().exists()


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_auth_status() -> Dict[str, Any]:
    """Get current authentication status.

    Returns dict with:
    - authenticated: bool
    - email: str or None
    - tier: str
    - premium: bool
    - org: str or None
    """
    creds = load_credentials()

    if not creds:
        return {
            "authenticated": False,
            "email": None,
            "tier": "free",
            "premium": False,
            "org": None,
        }

    return {
        "authenticated": True,
        "email": creds.email,
        "tier": creds.tier,
        "premium": creds.is_premium(),
        "org": creds.org_name,
    }


def require_auth() -> AuthCredentials:
    """Require authentication, raise if not logged in.

    Raises:
        RuntimeError: If not authenticated
    """
    creds = load_credentials()

    if not creds:
        raise RuntimeError(
            "Not authenticated. Run 'qodacode login' first."
        )

    return creds


def require_premium() -> AuthCredentials:
    """Require premium subscription.

    Raises:
        RuntimeError: If not authenticated or not premium
    """
    creds = require_auth()

    if not creds.is_premium():
        raise RuntimeError(
            f"Premium subscription required. Current tier: {creds.tier}\n"
            "Upgrade at: https://qodacode.com/pricing"
        )

    return creds


def open_login_page():
    """Open the login page in browser."""
    webbrowser.open("https://qodacode.com/login")


def open_pricing_page():
    """Open the pricing page in browser."""
    webbrowser.open("https://qodacode.com/pricing")
