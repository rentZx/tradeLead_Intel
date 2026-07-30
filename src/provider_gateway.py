"""Secure routing for commercial provider APIs.

Providers can be called directly with a local API key, or through an
allow-listed overseas gateway. The gateway URL never receives provider keys
from this application; it injects them from its own environment.
"""

from __future__ import annotations

import os
from typing import Any

import requests


def gateway_services() -> set[str]:
    value = os.getenv("TRADELEAD_GATEWAY_SERVICES", "")
    return {
        item.strip().lower()
        for item in value.split(",")
        if item.strip()
    }


def gateway_enabled(service: str) -> bool:
    return bool(
        os.getenv("TRADELEAD_API_GATEWAY_URL", "").strip()
        and os.getenv("TRADELEAD_API_GATEWAY_TOKEN", "").strip()
        and service.lower() in gateway_services()
    )


def provider_configured(service: str, local_key_env: str) -> bool:
    return bool(os.getenv(local_key_env, "").strip()) or gateway_enabled(service)


def provider_request(
    service: str,
    method: str,
    direct_url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_payload: dict[str, Any] | None = None,
    timeout: int = 35,
) -> requests.Response:
    """Call a provider directly or through the fixed-service gateway."""
    if gateway_enabled(service):
        gateway_url = os.getenv("TRADELEAD_API_GATEWAY_URL", "").strip().rstrip("/")
        gateway_token = os.getenv("TRADELEAD_API_GATEWAY_TOKEN", "").strip()
        safe_params = {
            name: value
            for name, value in (params or {}).items()
            if name.lower() not in {"api_key", "api_token", "key", "token"}
        }
        gateway_params = {"service": service.lower(), **safe_params}
        return requests.request(
            method.upper(),
            gateway_url,
            headers={
                "Accept": "application/json",
                "X-TradeLead-Gateway-Token": gateway_token,
            },
            params=gateway_params,
            json=json_payload,
            timeout=timeout,
        )

    if method.upper() == "GET":
        return requests.get(
            direct_url,
            headers=headers,
            params=params,
            timeout=timeout,
        )
    if method.upper() == "POST":
        return requests.post(
            direct_url,
            headers=headers,
            params=params,
            json=json_payload,
            timeout=timeout,
        )
    raise ValueError(f"Unsupported provider request method: {method}")
