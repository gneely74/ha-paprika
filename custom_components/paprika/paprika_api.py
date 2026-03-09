"""Async client for the Paprika Recipe Manager API."""

from __future__ import annotations

import gzip
import json
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

PAPRIKA_V1_URL = "https://www.paprikaapp.com/api/v1"
PAPRIKA_V2_URL = "https://www.paprikaapp.com/api/v2"


class PaprikaApiError(Exception):
    """Base exception for Paprika API errors."""


class PaprikaAuthError(PaprikaApiError):
    """Authentication error."""


class PaprikaApi:
    """Async client for the Paprika Recipe Manager API."""

    def __init__(
        self,
        email: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._email = email
        self._password = password
        self._session = session
        self._token: str | None = None

    async def authenticate(self) -> None:
        """Login and obtain a Bearer token via the v1 API."""
        try:
            async with self._session.post(
                f"{PAPRIKA_V1_URL}/account/login/",
                data={"email": self._email, "password": self._password},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientResponseError as err:
            raise PaprikaApiError(f"HTTP {err.status} during auth") from err

        if "error" in data:
            msg = data["error"]
            if isinstance(msg, dict):
                msg = msg.get("message", str(msg))
            raise PaprikaAuthError(f"Auth failed: {msg}")

        self._token = data["result"]["token"]

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make an authenticated request, re-authenticating on 401."""
        if self._token is None:
            await self.authenticate()

        headers = {"Authorization": f"Bearer {self._token}"}

        async with self._session.request(
            method, url, headers=headers, **kwargs
        ) as resp:
            if resp.status == 401:
                # Token expired — re-authenticate and retry once.
                await self.authenticate()
                headers = {"Authorization": f"Bearer {self._token}"}
                async with self._session.request(
                    method, url, headers=headers, **kwargs
                ) as retry:
                    retry.raise_for_status()
                    return await retry.json()
            resp.raise_for_status()
            return await resp.json()

    # ── Recipes ──────────────────────────────────────────────────────

    async def get_recipes(self) -> list[dict]:
        """Fetch the recipe stub list (uid + hash pairs)."""
        data = await self._request("GET", f"{PAPRIKA_V2_URL}/sync/recipes/")
        return data["result"]

    async def get_recipe(self, uid: str) -> dict:
        """Fetch a single recipe by UID (may be gzip-compressed)."""
        data = await self._request(
            "GET", f"{PAPRIKA_V2_URL}/sync/recipe/{uid}/"
        )
        result = data["result"]

        if isinstance(result, str):
            try:
                decompressed = gzip.decompress(result.encode("latin-1"))
                return json.loads(decompressed)
            except Exception:
                return json.loads(result)
        return result

    async def get_all_recipes_full(self) -> list[dict]:
        """Fetch every recipe with full details (one request per recipe)."""
        stubs = await self.get_recipes()
        recipes: list[dict] = []
        for stub in stubs:
            try:
                recipe = await self.get_recipe(stub["uid"])
                recipes.append(recipe)
            except Exception:
                _LOGGER.warning("Failed to fetch recipe %s", stub["uid"])
        return recipes

    # ── Meal plan ────────────────────────────────────────────────────

    async def get_meals(self) -> list[dict]:
        """Fetch all meal plan entries."""
        data = await self._request("GET", f"{PAPRIKA_V2_URL}/sync/meals/")
        return data["result"]

    # ── Categories ───────────────────────────────────────────────────

    async def get_categories(self) -> list[dict]:
        """Fetch all categories."""
        data = await self._request(
            "GET", f"{PAPRIKA_V2_URL}/sync/categories/"
        )
        return data["result"]
