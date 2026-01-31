import json
import os
import time
from typing import Any

import httpx
from loguru import logger

from wayfinder_paths.core.config import get_api_base_url
from wayfinder_paths.core.constants.base import DEFAULT_HTTP_TIMEOUT


class WayfinderClient:
    def __init__(self, api_key: str | None = None):
        """
        Initialize WayfinderClient.

        Args:
            api_key: Optional API key for service account authentication.
                    If provided, uses API key auth. Otherwise falls back to config.json.
        """
        self.api_base_url = f"{get_api_base_url()}/"
        timeout = httpx.Timeout(DEFAULT_HTTP_TIMEOUT)
        self.client = httpx.AsyncClient(timeout=timeout)

        self.headers = {
            "Content-Type": "application/json",
        }

        self._api_key: str | None = api_key
        self._access_token: str | None = None
        self._refresh_token: str | None = None

    def set_bearer_token(self, token: str) -> None:
        """
        Set runtime OAuth/JWT Bearer token for Wayfinder services.
        """
        self.headers["Authorization"] = f"Bearer {token}"
        self._access_token = token

    def set_tokens(self, access: str | None, refresh: str | None) -> None:
        """Set both access and refresh tokens and configure Authorization header."""
        if access:
            self.set_bearer_token(access)
        if refresh:
            self._refresh_token = refresh

    def clear_auth(self) -> None:
        """Clear Authorization headers (useful for logout or auth mode switch)."""
        self.headers.pop("Authorization", None)

    async def _refresh_access_token(self) -> bool:
        """Attempt to refresh access token using stored refresh token."""
        if not self._refresh_token:
            logger.debug("No refresh token available")
            return False
        try:
            logger.info("Attempting to refresh access token")
            start_time = time.time()
            url = f"{get_api_base_url()}/auth/token/refresh/"
            payload = {"refresh": self._refresh_token}
            response = await self.client.post(
                url, json=payload, headers={"Content-Type": "application/json"}
            )
            if response.status_code != 200:
                logger.warning(
                    f"Token refresh failed with status {response.status_code}"
                )
                return False
            data = response.json()
            new_access = data.get("access") or data.get("access_token")
            if not new_access:
                logger.warning("No access token in refresh response")
                return False
            self.set_bearer_token(new_access)
            elapsed = time.time() - start_time
            logger.info(f"Access token refreshed successfully in {elapsed:.2f}s")
            return True
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Token refresh failed after {elapsed:.2f}s: {e}")
            return False

    def _load_config_credentials(self) -> dict[str, str | None]:
        """
        Load credentials from config.json.
        Expected shape:
        {
          "user": { "username": ..., "password": ..., "refresh_token": ..., "api_key": ... },
          "system": { "api_key": ... }
        }
        """
        try:
            with open("config.json") as f:
                cfg = json.load(f)
            user = cfg.get("user", {}) if isinstance(cfg, dict) else {}
            system = cfg.get("system", {}) if isinstance(cfg, dict) else {}
            return {
                "username": user.get("username"),
                "password": user.get("password"),
                "refresh_token": user.get("refresh_token"),
                "api_key": user.get("api_key") or system.get("api_key"),
            }
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            logger.debug(f"Could not load config file at config.json: {e}")
            return {
                "username": None,
                "password": None,
                "refresh_token": None,
                "api_key": None,
            }
        except Exception as e:
            logger.warning(f"Unexpected error loading config file at config.json: {e}")
            return {
                "username": None,
                "password": None,
                "refresh_token": None,
                "api_key": None,
            }

    async def _ensure_bearer_token(self) -> bool:
        """
        Ensure Authorization header is set. Priority: existing header > constructor api_key > config.json api_key > config.json tokens > username/password.
        Raises PermissionError if no credentials found.
        """
        if self.headers.get("Authorization"):
            return True

        # Check for API key: constructor > config.json
        api_key = self._api_key
        if not api_key:
            creds = self._load_config_credentials()
            api_key = creds.get("api_key") or os.getenv("WAYFINDER_API_KEY")

        if api_key:
            api_key = api_key.strip() if isinstance(api_key, str) else api_key
            if not api_key:
                raise ValueError("API key cannot be empty")
            self.headers["Authorization"] = f"Bearer {api_key}"
            return True

        # Fall back to OAuth token-based auth
        creds = self._load_config_credentials()
        refresh = creds.get("refresh_token")

        if refresh:
            self._refresh_token = refresh
            refreshed = await self._refresh_access_token()
            if refreshed:
                return True

        username = creds.get("username")
        password = creds.get("password")

        if username and password:
            try:
                url = f"{get_api_base_url()}/auth/token/"
                payload = {"username": username, "password": password}
                response = await self.client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code == 200:
                    data = response.json()
                    access = data.get("access") or data.get("access_token")
                    refresh = data.get("refresh") or data.get("refresh_token")
                self.set_tokens(access, refresh)
                return bool(access)
            except Exception as e:
                logger.debug(f"Failed to authenticate with username/password: {e}")
                pass

        raise PermissionError(
            "Not authenticated: provide api_key (via constructor or config.json) for service account auth, "
            "or username+password/refresh_token in config.json for personal access"
        )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        retry_on_401: bool = True,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Wrapper around httpx that injects headers and auto-refreshes tokens on 401 once.
        Ensures API key or bearer token is set in headers when available (for service account auth and rate limits).
        """
        logger.debug(f"Making {method} request to {url}")
        start_time = time.time()

        # Ensure API key or bearer token is set in headers if available and not already set
        # This ensures API keys are passed to all endpoints (including public ones) for rate limiting
        if not self.headers.get("Authorization"):
            # Try to get API key from constructor or config
            api_key = self._api_key
            if not api_key:
                creds = self._load_config_credentials()
                api_key = creds.get("api_key") or os.getenv("WAYFINDER_API_KEY")

            if api_key:
                api_key = api_key.strip() if isinstance(api_key, str) else api_key
                if api_key:
                    self.headers["Authorization"] = f"Bearer {api_key}"

        merged_headers = dict(self.headers)
        if headers:
            merged_headers.update(headers)
        resp = await self.client.request(method, url, headers=merged_headers, **kwargs)

        if resp.status_code == 401 and retry_on_401 and self._refresh_token:
            logger.info("Received 401, attempting token refresh and retry")
            refreshed = await self._refresh_access_token()
            if refreshed:
                merged_headers = dict(self.headers)
                if headers:
                    merged_headers.update(headers)
                resp = await self.client.request(
                    method, url, headers=merged_headers, **kwargs
                )
                logger.info("Retry after token refresh successful")
            else:
                logger.error("Token refresh failed, request will fail")

        elapsed = time.time() - start_time
        if resp.status_code >= 400:
            logger.warning(
                f"HTTP {resp.status_code} response for {method} {url} after {elapsed:.2f}s"
            )
        else:
            logger.debug(
                f"HTTP {resp.status_code} response for {method} {url} after {elapsed:.2f}s"
            )

        resp.raise_for_status()
        return resp

    async def _authed_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Ensure Authorization (via env/config creds) and perform the request.
        Retries once on 401 by re-acquiring tokens.
        """
        ok = await self._ensure_bearer_token()
        if not ok:
            raise PermissionError("Not authenticated: set env tokens or credentials")
        try:
            return await self._request(method, url, headers=headers, **kwargs)
        except httpx.HTTPStatusError as e:
            if e.response is not None and e.response.status_code == 401:
                # Retry after attempting re-acquire/refresh
                await self._ensure_bearer_token()
                return await self._request(method, url, headers=headers, **kwargs)
            raise
