"""OpenRouter Codegen library.

Use this package to encrypt your OpenRouter API key with a password-derived mask,
store only the ciphertext, and request code-generation tasks while keeping the
plaintext key out of source control.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import requests

__all__ = [
    "__version__",
    "encrypt_api_key",
    "decrypt_api_key",
    "request_completion",
    "generate_code_file",
]

__version__ = "0.1.1"

OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"
DEFAULT_SYSTEM_PROMPT = (
    "You are a senior software engineer who writes clean, well-structured code. "
    "You MUST only output code, nothing else. You must output NO comments."
)
DEFAULT_HTTP_REFERER = "https://example.com/"
DEFAULT_APP_TITLE = "OpenRouter Codegen"
DEFAULT_TIMEOUT = 60

ENV_ENCRYPTED_KEY = "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"
ENV_HTTP_REFERER = "example.com"
ENV_APP_TITLE = "MathHelper"


def _derive_mask(password: str) -> bytes:
    if not password:
        raise ValueError("Password must not be empty.")
    return hashlib.sha256(password.encode("utf-8")).digest()


def _xor_bytes(data: bytes, mask: bytes) -> bytes:
    return bytes(b ^ mask[i % len(mask)] for i, b in enumerate(data))


def encrypt_api_key(password: str, api_key: str) -> str:
    """Return a Base64 ciphertext for ``api_key`` using ``password``."""

    mask = _derive_mask(password)
    ciphertext = _xor_bytes(api_key.encode("utf-8"), mask)
    return base64.b64encode(ciphertext).decode("ascii")


def decrypt_api_key(encrypted_key_b64: str, password: str) -> str:
    """Decrypt a Base64 ciphertext using ``password`` and return the plaintext key."""

    encrypted_bytes = base64.b64decode(encrypted_key_b64)
    plaintext_bytes = _xor_bytes(encrypted_bytes, _derive_mask(password))

    try:
        key = plaintext_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:  # pragma: no cover - defensive
        raise ValueError("Incorrect password for API key decryption.") from exc

    if not key.startswith("sk-"):
        raise ValueError("Incorrect password for API key decryption.")

    return key


def _build_payload(task: str, model: str, system_prompt: str) -> Dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ],
        "temperature": 0.2,
    }


def request_completion(
    api_key: str,
    task: str,
    *,
    model: str = DEFAULT_MODEL,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    endpoint: str = OPENROUTER_ENDPOINT,
    http_referer: Optional[str] = None,
    app_title: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Request a completion from OpenRouter and return only the code text."""

    payload = _build_payload(task, model, system_prompt)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": http_referer or os.getenv(ENV_HTTP_REFERER, DEFAULT_HTTP_REFERER),
        "X-Title": app_title or os.getenv(ENV_APP_TITLE, DEFAULT_APP_TITLE),
    }

    response = requests.post(
        endpoint,
        headers=headers,
        data=json.dumps(payload),
        timeout=timeout,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter request failed ({response.status_code}): {response.text}"
        )

    content = response.json()["choices"][0]["message"]["content"]
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content)
    return str(content)


def _resolve_ciphertext(encrypted_key_b64: Optional[str]) -> str:
    ciphertext = encrypted_key_b64 or os.getenv(ENV_ENCRYPTED_KEY)
    if not ciphertext:
        raise ValueError(
            "Missing encrypted key. Pass `encrypted_key_b64` or set "
            f"the {ENV_ENCRYPTED_KEY} environment variable."
        )
    return ciphertext


def generate_code_file(
    password: str,
    task: str,
    filename: str,
    *,
    encrypted_key_b64: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    output_dir: Optional[Union[str, Path]] = None,
    endpoint: str = OPENROUTER_ENDPOINT,
    http_referer: Optional[str] = None,
    app_title: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> Path:
    """Write the OpenRouter response for ``task`` to ``filename`` and return the path."""

    ciphertext = _resolve_ciphertext(encrypted_key_b64)
    api_key = decrypt_api_key(ciphertext, password)

    completion = request_completion(
        api_key,
        task,
        model=model,
        system_prompt=system_prompt,
        endpoint=endpoint,
        http_referer=http_referer,
        app_title=app_title,
        timeout=timeout,
    )

    target_dir = Path(output_dir) if output_dir else Path.cwd()
    target_path = target_dir / filename
    target_path.write_text(completion.strip() + "\n", encoding="utf-8")
    return target_path
