"""
=============================================================================
Helix Guard: Backend Security & Credential Management Module (Task 3)
=============================================================================
SECURITY POLICIES:
1. Never hardcode API keys, secrets, or bearer tokens in source code.
2. Never print, log, expose, or display credentials in plaintext.
3. Never expose local sensitive file paths or credentials in UI error messages.
4. Provide environment variable and .env local configuration support.
5. Provide masked status introspection for user transparency.
=============================================================================
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional, Tuple


def mask_secret(secret: Optional[str], visible_prefix: int = 4, visible_suffix: int = 3) -> str:
    """
    Returns a masked representation of a sensitive token (e.g., 'd1ID••••••••NHp').
    Never reveals the full secret.
    """
    if not secret or not isinstance(secret, str):
        return "Unconfigured"
    s = secret.strip()
    if len(s) == 0:
        return "Unconfigured"
    if len(s) <= (visible_prefix + visible_suffix + 2):
        return "••••••••"
    return f"{s[:visible_prefix]}••••••••{s[-visible_suffix:]}"


def sanitize_message(message: str) -> str:
    """
    Sanitizes log or error messages by redacting suspected API keys and personal paths.
    """
    if not isinstance(message, str):
        message = str(message)

    # Redact common Windows / Unix user paths
    sanitized = re.sub(r"[A-Za-z]:\\[Uu]sers\\[^\\]+", "<USER_HOME>", message)
    sanitized = re.sub(r"/home/[^/]+", "<USER_HOME>", sanitized)

    # Redact 32+ character alphanumeric tokens / API keys
    sanitized = re.sub(r"[A-Za-z0-9_\-]{32,}", "[REDACTED_SECRET]", sanitized)

    return sanitized


@dataclass
class IBMQuantumCredentials:
    """
    Encapsulates IBM Quantum credential status.
    Security guarantee: __repr__ and __str__ NEVER print the raw token.
    """
    is_configured: bool
    source: str
    masked_token: str
    masked_instance: str
    hardware_available: bool = False
    execution_mode: str = "Local Simulation (StatevectorEstimator)"
    _raw_token: Optional[str] = None
    _raw_instance: Optional[str] = None

    def __repr__(self) -> str:
        return (
            f"IBMQuantumCredentials(is_configured={self.is_configured}, "
            f"source='{self.source}', masked_token='{self.masked_token}', "
            f"hardware_available={self.hardware_available})"
        )

    def __str__(self) -> str:
        return self.__repr__()

    def get_token_for_client(self) -> Optional[str]:
        """Returns the in-memory token strictly for client initialization."""
        return self._raw_token

    def get_instance_for_client(self) -> Optional[str]:
        """Returns the in-memory instance strictly for client initialization."""
        return self._raw_instance


def _parse_env_file(filepath: str) -> dict[str, str]:
    """Lightweight, dependency-free parser for .env files."""
    env_vars = {}
    if not os.path.exists(filepath):
        return env_vars

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and val:
                        env_vars[key] = val
    except Exception:
        # Silently fail on file read errors to avoid leaking paths
        pass
    return env_vars


def _parse_legacy_credentials_file(filepath: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Safely inspects legacy local text file format without printing or echoing contents.
    Format:
        IBM id- ...
        instance- ...
        api key- ...
    """
    if not os.path.exists(filepath):
        return None, None

    token = None
    instance = None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                clean = line.strip()
                lower = clean.lower()
                if lower.startswith("api key-") or lower.startswith("api_key-") or lower.startswith("apikey-"):
                    parts = clean.split("-", 1)
                    if len(parts) > 1 and parts[1].strip():
                        token = parts[1].strip()
                elif lower.startswith("instance-"):
                    parts = clean.split("-", 1)
                    if len(parts) > 1 and parts[1].strip():
                        instance = parts[1].strip()
    except Exception:
        pass
    return token, instance


def load_ibm_credentials(base_dir: Optional[str] = None) -> IBMQuantumCredentials:
    """
    Securely loads IBM Quantum credentials following strict precedence:
    1. Environment variables (QISKIT_IBM_TOKEN / IBM_QUANTUM_API_KEY)
    2. Local .env file (excluded from git)
    3. Legacy local configuration file (read into memory, never printed)
    4. Unconfigured default (safe local simulation mode)
    """
    base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))

    # 1. Check Environment Variables
    env_token = os.getenv("QISKIT_IBM_TOKEN") or os.getenv("IBM_QUANTUM_API_KEY") or os.getenv("IBM_QUANTUM_TOKEN")
    env_instance = os.getenv("IBM_QUANTUM_INSTANCE") or os.getenv("QISKIT_IBM_INSTANCE")

    if env_token:
        return IBMQuantumCredentials(
            is_configured=True,
            source="Environment Variable",
            masked_token=mask_secret(env_token),
            masked_instance=mask_secret(env_instance) if env_instance else "Default Instance",
            hardware_available=False,  # Hardware execution not active; simulation used
            execution_mode="Local Simulation (StatevectorEstimator)",
            _raw_token=env_token,
            _raw_instance=env_instance,
        )

    # 2. Check local .env file
    env_file_paths = [
        os.path.join(base_dir, ".env"),
        os.path.join(os.path.dirname(base_dir), ".env"),
    ]
    for env_path in env_file_paths:
        if os.path.exists(env_path):
            parsed = _parse_env_file(env_path)
            f_token = parsed.get("IBM_QUANTUM_API_KEY") or parsed.get("QISKIT_IBM_TOKEN") or parsed.get("IBM_QUANTUM_TOKEN")
            f_instance = parsed.get("IBM_QUANTUM_INSTANCE") or parsed.get("QISKIT_IBM_INSTANCE")
            if f_token:
                return IBMQuantumCredentials(
                    is_configured=True,
                    source=".env File (Git Ignored)",
                    masked_token=mask_secret(f_token),
                    masked_instance=mask_secret(f_instance) if f_instance else "Default Instance",
                    hardware_available=False,
                    execution_mode="Local Simulation (StatevectorEstimator)",
                    _raw_token=f_token,
                    _raw_instance=f_instance,
                )

    # 3. Check legacy credentials file if present locally
    legacy_file_paths = [
        os.path.join(base_dir, "ibm credentials.txt"),
        os.path.join(os.path.dirname(base_dir), "ibm credentials.txt"),
    ]
    for leg_path in legacy_file_paths:
        if os.path.exists(leg_path):
            leg_token, leg_instance = _parse_legacy_credentials_file(leg_path)
            if leg_token:
                return IBMQuantumCredentials(
                    is_configured=True,
                    source="Local Credential File (Protected)",
                    masked_token=mask_secret(leg_token),
                    masked_instance=mask_secret(leg_instance) if leg_instance else "Default Instance",
                    hardware_available=False,
                    execution_mode="Local Simulation (StatevectorEstimator)",
                    _raw_token=leg_token,
                    _raw_instance=leg_instance,
                )

    # 4. Default: Unconfigured (Local simulation only)
    return IBMQuantumCredentials(
        is_configured=False,
        source="Unconfigured",
        masked_token="Unconfigured",
        masked_instance="Unconfigured",
        hardware_available=False,
        execution_mode="Local Simulation (StatevectorEstimator)",
        _raw_token=None,
        _raw_instance=None,
    )

